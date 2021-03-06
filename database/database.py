##   This file is part of Reformed.
##
##   Reformed is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License version 2 as
##   published by the Free Software Foundation.
##
##   Reformed is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with Reformed.  If not, see <http://www.gnu.org/licenses/>.
##
##   -----------------------------------------------------------------
##	
##   Reformed
##   Copyright (c) 2008-2009 Toby Dacre & David Raznick
##	
##	database.py
##	======
##	
##	This file contains the Database class that provides access to
##  all fuctionality to create the schema, and give acces to query
##  and modify a reformed database.

import logging
from collections import defaultdict
import os
import datetime

import sqlalchemy as sa
import networkx as nx
from ZODB.PersistentMapping import PersistentMapping
import transaction

import custom_exceptions
import search
import resultset
import tables
from util import split_table_fields, SchemaLock
from fields import ForeignKey, Integer
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from util import OrderedDict
import fields as field_types
import sessionwrapper
import validate_database
from events import Event
import actions

log = logging.getLogger('rebase.application.database')

class Database(object):

    def __init__(self, *tables, **kw):

        log.info("initialising database")
        self.status = "updating"

        self.kw = kw
        self.metadata = None

        self.connection_string = kw.get("connection_string", None)
        if self.connection_string:
            self.engine = create_engine(self.connection_string)
            self.metadata = MetaData()
            self.metadata.bind = self.engine
            self._Session = sessionmaker(bind=self.engine, autoflush = False)
            self.Session = sessionwrapper.SessionClass(self._Session, self)

        self.logging_tables = kw.get("logging_tables", None)
        self.quiet = kw.get("quiet", None)

        self.application = kw.get("application", None)
        if self.application:
            self.set_application(self.application)

        self.max_table_id = 0
        self.max_event_id = 0

        self.persisted = False
        self.graph = None
        self.relations = []

        self.tables = OrderedDict()

        self.search_actions = {}
        self.search_names = {}
        self.search_ids = {}

        for table in tables:
            self.add_table(table)

    def set_application(self, application):

        self.application = application
        if not self.connection_string:
            self.metadata = application.metadata
            self.engine = application.engine
            self._Session = application.Session
            self.Session = sessionwrapper.SessionClass(self._Session, self)

        if self.logging_tables is not None:
            self.logging_tables = self.application.logging_tables
        if self.quiet is not None:
            self.quiet = self.application.quiet

        self.application_folder = self.application.application_folder
        self.zodb = self.application.zodb
        self.zodb_tables_init()
        self.application.Session = self.Session

        with SchemaLock(self) as file_lock:
            self.load_from_persist()
        self.status = "active"


    def zodb_tables_init(self):
        zodb = self.application.aquire_zodb()

        connection = zodb.open()
        root = connection.root()
        if "tables" not in root:
            root["tables"] = PersistentMapping()
            root["table_count"] = 0
            root["event_count"] = 0
            transaction.commit()
        connection.close()

        zodb.close()
        self.application.get_zodb(True)

    def __getitem__(self, item):
        if isinstance(item, int):
            table = self.get_table_by_id(item)
            if not table:
                raise IndexError("table id %s does not exist" % item)
            return table
        else:
            return self.tables[item]

    def get_table_by_id(self, id):

        for table in self.tables.itervalues():
            if table.table_id == id:
                return table

    def add_table(self, table, ignore = False, drop = False):

        log.info("adding table %s" % table.name)

        if table.name in self.tables.iterkeys():
            if ignore:
                return
            elif drop:
                self.drop_table(table.name)
            else:
                raise custom_exceptions.DuplicateTableError("already a table named %s"
                                                            % table.name)


        self._add_table_no_persist(table)

    def rename_table(self, table, new_name, session = None):

        if isinstance(table, tables.Table):
            table_to_rename = table
        else:
            table_to_rename = self.tables[table]

        with SchemaLock(self) as file_lock:
            for relations in table_to_rename.tables_with_relations.values():
                for rel in relations:
                    if rel.other == table_to_rename.name:
                        field = rel.parent
                        field.args = [new_name] + list(field.args[1:])

            table_to_rename.name = new_name
            file_lock.export(uuid = True)
            table_to_rename.sa_table.rename(new_name)
            file_lock.export()
            self.load_from_persist(True)

        if table_to_rename.logged:
            self.rename_table("_log_%s" % table_to_rename.name, "_log_%s" % new_name, session)

    def drop_table(self, table):

        with SchemaLock(self) as file_lock:
            if isinstance(table, tables.Table):
                table_to_drop = table

            else:
                table_to_drop = self.tables[table]

            if table_to_drop.dependant_tables:
                raise custom_exceptions.DependencyError((
                    "cannot delete table %s as the following tables"
                    " depend on it %s" % (table.name, table.dependant_tables)))

            for relations in table_to_drop.tables_with_relations.itervalues():
                for relation in relations:
                    field = relation.parent
                    field.table.fields.pop(field.name)
                    field.table.field_list.remove(field)

            self.tables.pop(table_to_drop.name)

            file_lock.export(uuid = True)
            table_to_drop.sa_table.drop()
            file_lock.export()
            self.load_from_persist(True)

        if table_to_drop.logged:
            self.drop_table(self.tables["_log_" + table_to_drop.name])


    def add_relation_table(self, table):
        if "_core" not in self.tables:
            raise custom_exceptions.NoTableAddError("table %s cannot be added as there is"
                                                    "no _core table in the database"
                                                    % table.name)

        assert table.primary_entities
        assert table.secondary_entities

        table.relation = True
        table.kw["relation"] = True

        self.add_table(table)

        relation = ForeignKey("_core_id", "_core", backref = table.name)
        table._add_field_no_persist(relation)

        event = Event("delete",
                      actions.DeleteRows("_core"))

        table.add_event(event)

    def add_info_table(self, table):
        if "_core" not in self.tables:
            raise custom_exceptions.NoTableAddError("table %s cannot be added as there is"
                                                    "no _core table in the database"
                                                    % table.name)

        table.info_table = True
        table.kw["info_table"] = True

        self.add_table(table)

        relation = ForeignKey("_core_id", "_core", backref = table.name)
        table._add_field_no_persist(relation)

        event = Event("delete",
                      actions.DeleteRows("_core"))

        table.add_event(event)


    def add_entity(self, table):
        if "_core" not in self.tables:
            raise custom_exceptions.NoTableAddError("table %s cannot be added as there is"
                                                    "no _core table in the database"
                                                    % table.name)

        table.entity = True
        table.kw["entity"] = True
        self.add_table(table)

        #add relation
        relation = ForeignKey("_core_id", "_core", backref = table.name)
        table._add_field_no_persist(relation)



        ##add title events

        if table.title_field:
            title_field = table.title_field
        else:
            title_field = "name"

        event = Event("new change",
                      actions.CopyTextAfter("primary_entity._core_entity.title", title_field))

        table.add_event(event)


        if table.summary_fields:

            event = Event("new change",
                          actions.CopyTextAfterField("primary_entity._core_entity.summary", table.summary_fields))

            table.add_event(event)

        event = Event("delete",
                      actions.DeleteRows("primary_entity._core_entity"))

        table.add_event(event)


    def _add_table_no_persist(self, table):

        table._set_parent(self)


    def persist(self):

        self.status = "updating"

        for table in self.tables.values():
            if not self.logging_tables:
                ## FIXME should look at better place to set this
                table.kw["logged"] = False
                table.logged = False
            if table.logged and "_log_%s" % table.name not in self.tables.iterkeys() :
                self.add_table(self.logged_table(table))

        for table in self.tables.itervalues():
            table.add_foreign_key_columns()

        self.update_sa(True)

        with SchemaLock(self) as file_lock:
            file_lock.export(uuid = True)
            self.metadata.create_all(self.engine)
            self.persisted = True
            file_lock.export()
            self.load_from_persist(True)

    def get_file_path(self, uuid_name = False):

        uuid = datetime.datetime.now().isoformat().\
                replace(":", "-").replace(".", "-")
        if uuid_name:
            file_name = "generated_schema-%s.py" % uuid
        else:
            file_name = "generated_schema.py"

        file_path = os.path.join(
            self.application.application_folder,
            "_schema",
            file_name
        )
        return file_path

    def code_repr_load(self):

        import _schema.generated_schema as sch
        sch = reload(sch)
        database = sch.database
        database.clear_sa()
        for table in database.tables.values():
            table.database = self
            self.add_table(table)
            table.persisted = True

        self.max_table_id = database.max_table_id
        self.max_event_id = database.max_event_id

        self.persisted = True


    def code_repr_export(self, file_path):

        try:
            os.remove(file_path)
            os.remove(file_path+"c")
        except OSError:
            pass

        out_file = open(file_path, "w")

        output = [
            "from database.database import Database",
            "from database.tables import Table",
            "from database.fields import *",
            "from database.database import table, entity, relation",
            "from database.events import Event",
            "from database.actions import *",
            "",
            "",
            "database = Database(",
            "",
            "",
        ]

        for table in sorted(self.tables.values(),
                            key = lambda x:x.table_id):
            output.append(table.code_repr() + ",")

        kw_display = ""
        if self.kw:
            kw_list = ["%s = %s" % (i[0], repr(i[1])) for i in self.kw.items()]
            kw_display = ", ".join(sorted(kw_list))

        output.append(kw_display)
        output.append(")")

        out_file.write("\n".join(output))
        out_file.close()

        return file_path


    def load_from_persist(self, restart = False):

        self.clear_sa()
        self.tables = OrderedDict()
        try:
            self.code_repr_load()
        except ImportError:
            return
        self.add_relations()
        self.update_sa()
        self.validate_database()


    def add_relations(self):     #not property for optimisation
        self.relations = []
        for table_name, table_value in self.tables.iteritems():
            ## make sure fk columns are remade
            table_value.foriegn_key_columns_current = None
            table_value.add_relations()
            for rel_name, rel_value in table_value.relations.iteritems():
                self.relations.append(rel_value)



    def checkrelations(self):
        for relation in self.relations:
            if relation.other not in self.tables.iterkeys():
                raise custom_exceptions.RelationError,\
                        "table %s does not exits" % relation.other


    def update_sa(self, reload = False):
        if reload == True and self.status <> "terminated":
            self.status = "updating"

        if reload:
            self.clear_sa()

        self.checkrelations()
        self.make_graph()
        try:
            for table in self.tables.itervalues():
                table.make_paths()
                table.make_sa_table()
                table.make_sa_class()
            for table in self.tables.itervalues():
                table.sa_mapper()
            sa.orm.compile_mappers()
            for table in self.tables.itervalues():
                for column in table.columns.iterkeys():
                    getattr(table.sa_class, column).impl.active_history = True
                table.columns_cache = table.columns
            for table in self.tables.itervalues():
                table.make_schema_dict()
            ## put valid_info tables into info_table
            for table in self.tables.itervalues():
                if table.relation or table.entity:
                    for valid_info_table in table.valid_info_tables:
                        info_table = self.tables[valid_info_table]
                        assert info_table.info_table
                        info_table.valid_core_types.append(table.name)
            self.collect_search_actions()


        except (custom_exceptions.NoDatabaseError,\
                custom_exceptions.RelationError):
            pass
        if reload == True and self.status <> "terminated":
            self.status = "active"

    def clear_sa(self):
        sa.orm.clear_mappers()
        if self.metadata:
            self.metadata.clear()
        for table in self.tables.itervalues():
            table.foriegn_key_columns_current = None
            table.mapper = None
            table.sa_class = None
            table.sa_table = None
            table.paths = None
            table.local_tables = None
            table.one_to_many_tables = None
            table.events = dict(new = [],
                                delete = [],
                                change = [])
            table.schema_dict = None
            table.valid_core_types = []
            table.columns_cache = None

        self.graph = None
        self.search_actions = {}
        self.search_names = {}
        self.search_ids = {}


    def tables_with_relations(self, table):
        relations = defaultdict(list)
        for n, v in table.relations.iteritems():
            relations[(v.other, "here")].append(v)
        for v in self.relations:
            if v.other == table.name:
                relations[(v.table.name, "other")].append(v)
        return relations

    def result_set(self, search):

        return resultset.ResultSet(search)

    def search(self, table_name, where = "id>0", *args, **kw):
        ##FIXME id>0 should be changed to none once search is sorted

        """
        :param table_name: specifies the base table you will be query from (required)

        :param where: either a paramatarised or normal where clause, if paramitarised
        either values or params keywords have to be added. (optional first arg, if
        missing will query without where)

        :param tables: an optional list of onetoone or manytoone tables to be extracted
        with results

        :param keep_all: will keep id, _core_entity_id, modified_by and modified_on fields

        :param fields: an optional explicit field list in the form 'field' for base table
        and 'table.field' for other tables.  Overwrites table option and keep all.

        :param limit: the row limit

        :param offset: the offset

        :param internal: if true will not convert date, boolean and decimal fields

        :param values: a list of values to replace the ? in the paramatarised queries

        :param params: a dict with the keys as the replacement to inside the curly
        brackets i.e key name will replace {name} in query.

        :param order_by: a string in the same form as a sql order by
        ie 'name desc, donkey.name, donkey.age desc'  (name in base table)
        """

        session = kw.pop("session", None)
        if session:
            external_session = True
        else:
            session = self.Session()
            external_session = False

        tables = kw.get("tables", [table_name])
        fields = kw.get("fields", None)

        join_tables = []

        if fields:
            join_tables = split_table_fields(fields, table_name).keys()
            if table_name in join_tables:
                join_tables.remove(table_name)
            tables = None
        if tables:
            join_tables.extend(tables)
            if table_name in tables:
                join_tables.remove(table_name)

        if "order_by" not in kw:
            kw["order_by"] = "id"

        if join_tables:
            kw["extra_outer"] = join_tables
            kw["distinct_many"] = False

        try:
            query = search.Search(self, table_name, session, where, *args, **kw)
            result = resultset.ResultSet(query, **kw)
            result.collect()
            return result

        except Exception, e:
            session.rollback()
            raise
        finally:
            if not external_session:
                session.close()

    def search_single(self, table_name, *args, **kw):

        result = self.search(table_name, *args, limit = 2, **kw)
        data = result.results

        if not data or len(data) == 2:
            raise custom_exceptions.SingleResultError("one result not found\n\n table:\n %s \nargs:\n %s\ndata:\n%s" % (table_name, args, data))

        return result

    def search_single_data(self, table_name, *args, **kw):

        try:
            session = self.Session()
            result = self.search(table_name, *args,
                                 limit = 2, session = session, **kw)
            data = result.results

            if not data or len(data) == 2:
                raise custom_exceptions.SingleResultError("one result not found")

            return result.data[0]
        finally:
            session.close()

    def logged_table(self, logged_table):

        logging_table = tables.Table("_log_"+ logged_table.name,
                                     logged = False,
                                     modified_date = False,
                                     version = False,
                                     modified_by = False,
                                    )

        for column in logged_table.columns.itervalues():

            ##FIXME if type is an object (not a class) need different rules
            if hasattr(column.type, "length"):
                length = column.type.length
                field =getattr(field_types, column.type.__class__.__name__)\
                              (column.name, length = length)
            elif hasattr(column.type, "precision"):
                field =getattr(field_types, column.type.__class__.__name__)(column.name)
            else:
                field =getattr(field_types, column.type.__name__)(column.name)

            logging_table.add_field(field)

        logging_table.add_field(Integer("_logged_table_id"))

        return logging_table

    def get_class(self, table):

        if table not in self.tables.iterkeys():
            raise custom_exceptions.NoTableError("table %s does not exist" % table)

        return self.tables[table].sa_class

    def get_instance(self, table):

        if table not in self.tables.iterkeys():
            raise custom_exceptions.NoTableError("table %s does not exist" % table)

        return self.tables[table].sa_class()

    def validate_database(self):

        return validate_database.validate_database(self)

    def collect_search_actions(self):

        for table in self.tables.itervalues():
            for action in table.events["new"]:
                if isinstance(action, actions.UpdateSearch):
                    self.search_actions[action.event_id] = (table.name, action)
                    ## FIXME there can be duplicate names so they will overwrite
                    action.set_names(table.name)
                    self.search_names[action.name] = str(action.event_id)
                    self.search_ids[str(action.event_id)] = action.name


    def make_graph(self):

        if self.graph is not None and len(self.graph.nodes()) == len(self.tables):
            return

        gr = nx.MultiDiGraph()

        for table in self.tables.keys():
            gr.add_node(table)

        for rel in self.relations:
            gr.add_edge(rel.table.name, rel.other, None, {"relation" : rel})

        self.graph = gr

    def set_option(self, item, key, value):

        if item.count("."):
            table_name, field_name = item.split(".")
            table = self[table_name]
            field = self[table_name].fields[field_name]
            field.set_kw(key, value)
        else:
            table = self[item]
            table.set_kw(key, value)

def table(name, database, *args, **kw):
    """helper to add table to database args and keywords same as Table definition"""
    if name in database.tables:
        print '<%s> exists will not create' % name
        return
    database.add_table(tables.Table(name, *args,  **kw))

def entity(name, database, *args, **kw):
    """helper to add entity to database args and keywords same as Table definition"""
    if name in database.tables:
        print '<%s> exists will not create' % name
        return
    database.add_entity(tables.Table(name, *args,  **kw))

def relation(name, database, *args, **kw):
    """helper to add entity to database args and keywords same as Table definition"""
    if name in database.tables:
        print '<%s> exists will not create' % name
        return
    database.add_relation_table(tables.Table(name, *args,  **kw))

def info_table(name, database, *args, **kw):
    """helper to add entity to database args and keywords same as Table definition"""
    if name in database.tables:
        print '<%s> exists will not create' % name
        return
    database.add_info_table(tables.Table(name, *args,  **kw))
