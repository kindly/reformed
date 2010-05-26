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

import sqlalchemy as sa
import custom_exceptions
import search
import resultset
import tables
from collections import defaultdict
from util import get_paths, get_all_local_data, split_table_fields
from fields import ManyToOne, OneToOne, OneToMany, Integer, CopyTextAfter, CopyTextAfterField, DeleteRow
import fields as field_types
import sessionwrapper
import validate_database
import logging
import networkx as nx
import threading
import os
from ZODB.PersistentMapping import PersistentMapping
import transaction

log = logging.getLogger('rebase.application.database')

class Database(object):

    def __init__(self, application):

        log.info("initialising database")
        self.status = "updating"

        self.application = application
        self.metadata = application.metadata
        self.engine = application.engine
        self._Session = application.Session
        self.logging_tables = application.logging_tables
        self.quiet = application.quiet


        self.zodb = self.application.zodb
        self.application_dir = self.application.application_folder

        self.metadata.bind = self.engine
        self.Session = sessionwrapper.SessionClass(self._Session, self)
        # update the application Session
        self.application.Session = self.Session

        self.persisted = False
        self.graph = None
        self.fields_to_persist = []
        self.relations = []

        self.tables = {}

        connection = self.zodb.open()
        root = connection.root()
        if "tables" not in root:
            root["tables"] = PersistentMapping()
            root["table_count"] = 0
            transaction.commit()
        connection.close()


        self.load_from_persist()

        self.status = "active"



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

        connection = self.zodb.open()
        root = connection.root()
        persisted_tables = root["tables"]

        try:

            for relations in table_to_rename.tables_with_relations.values():
                for rel in relations:
                    if rel.other == table_to_rename.name:
                        field = rel.parent
                        persisted_field = persisted_tables[field.table.name]["fields"][field.name]
                        persisted_field["args"][0] = new_name

            persisted_table = persisted_tables.pop(table_to_rename.name)
            persisted_tables[new_name] = persisted_table
            table_to_rename.sa_table.rename(new_name)

        except Exception, e:
            transaction.abort()
            raise
        else:
            transaction.commit()
            self.load_from_persist(True)
        finally:
            connection.close()

        if table_to_rename.logged:
            self.rename_table("_log_%s" % table_to_rename.name, "_log_%s" % new_name, session)

    def drop_table(self, table):

        connection = self.zodb.open()
        root = connection.root()
        persisted_tables = root["tables"]

        try:
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
                    persisted_tables[field.table.name]["fields"].pop(field.name)
                    persisted_tables[field.table.name]["field_order"].remove(field.name)

            persisted_tables.pop(table_to_drop.name)

            table_to_drop.sa_table.drop()

        except Exception, e:
            transaction.abort()
            raise
        else:
            transaction.commit()
            self.load_from_persist(True)
        finally:
            connection.close()

        if table_to_drop.logged:
            self.drop_table(self.tables["_log_" + table_to_drop.name])


    @property
    def t(self):
        class Tables(object):
            pass
        tables = Tables()
        for name, table in self.aliases.iteritems():
            setattr(tables, name, table)
        return tables

    def add_relation_table(self, table):
        if "_core_entity" not in self.tables:
            raise custom_exceptions.NoTableAddError("table %s cannot be added as there is"
                                                    "no entity table in the database"
                                                    % table.name)

        table.relationship = True
        table.kw["relationship"] = True

        self.add_table(table)

        primary = OneToMany("%s_primary" % table.name, table.name, backref = "_primary")
        secondary = OneToMany("%s_secondary" % table.name, table.name, backref = "_secondary")

        self.tables["_core_entity"]._add_field_no_persist(primary)
        self.tables["_core_entity"]._add_field_no_persist(secondary)

        if self.tables["_core_entity"].persisted:
            self.fields_to_persist.append(primary)
            self.fields_to_persist.append(secondary)


    def add_entity(self, table):
        if "_core_entity" not in self.tables:
            raise custom_exceptions.NoTableAddError("table %s cannot be added as there is"
                                                    "no entity table in the database"
                                                    % table.name)
        table.entity = True
        table.kw["entity"] = True
        self.add_table(table)

        #add relation
        relation = OneToOne(table.name, table.name, backref = "_entity")
        self.tables["_core_entity"]._add_field_no_persist(relation)

        if self.tables["_core_entity"].persisted:
            self.fields_to_persist.append(relation)

        #add title events

        if table.title_field:
            target_field = table.title_field
        else:
            target_field = "name"

        title_event = CopyTextAfter("%s_title" % table.name, table.name, field_name = "title", fields = target_field)


        self.tables["_core_entity"]._add_field_no_persist(title_event)

        if self.tables["_core_entity"].persisted:
            self.fields_to_persist.append(title_event)

        #add summary events

        if table.summary_fields:
            summary_fields = table.summary_fields

            summary_event = CopyTextAfterField("%s_summary" % table.name, table.name, field_name = "summary", fields = summary_fields)
            self.tables["_core_entity"]._add_field_no_persist(summary_event)

            if self.tables["_core_entity"].persisted:
                self.fields_to_persist.append(summary_event)

        ## add delete event

        delete_event = DeleteRow("delete_%s" % table.name, table.name)
        self.tables["_core_entity"]._add_field_no_persist(delete_event)

        if self.tables["_core_entity"].persisted:
            self.fields_to_persist.append(delete_event)

    def _add_table_no_persist(self, table):

        table._set_parent(self)

    def persist(self):

        self.status = "updating"

        connection = self.zodb.open()
        try:

            ## add logging tables
            for table in self.tables.values():
                if not self.logging_tables:
                    ## FIXME should look at better place to set this
                    table.kw["logged"] = False
                    table.logged = False
                if table.logged and "_log_%s" % table.name not in self.tables.iterkeys() :
                    self.add_table(self.logged_table(table))

            for table in self.tables.itervalues():
                if not table.persisted:
                    table.persist(connection)

            for field in self.fields_to_persist:
                field.table._persist_extra_field(field, connection)

            for table in self.tables.itervalues():
                table.persist_foreign_key_columns(connection)

            for table in self.tables.itervalues():
                if not table.persisted:
                    table.set_field_order(connection)

            self.update_sa(True)
            self.metadata.create_all(self.engine)
        except Exception, e:
            transaction.abort()
            raise
        else:
            transaction.commit()
        finally:
            connection.close()

        self.load_from_persist(True)

        self.fields_to_persist = []
        self.persisted = True

        self.status = "updating"


    def load_from_persist(self, restart = False):

        connection = self.zodb.open()

        if connection:
            self.tables = {}
            self.clear_sa()
            root = connection.root()
            for table_name, table in root["tables"].iteritems():
                fields = []
                for field_name, field in table["fields"].iteritems():
                    field_cls = getattr(field_types, field["type"])
                    fields.append(field_cls(field_name,
                                            *field["args"],
                                            **field["params"]))

                self.add_table(tables.Table(table_name,
                                            *fields,
                                            field_order = list(table["field_order"]),
                                            persisted = True,
                                            **table["params"])
                                            )

        self.update_sa(True)
        self.validate_database()
        connection.close()

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

    def check_related_order_by(self):
        for relation in self.relations:
            if relation.order_by_list:
                for col in relation.order_by_list:
                    if col[0] != 'id' \
                       and col[0] not in self.tables[relation.other].columns.iterkeys():
                        raise custom_exceptions.RelationError,\
                              "ordered column %s does not exits in %s" \
                                % (col[0], relation.other)


    def update_sa(self, reload = False):
        if reload == True and self.status <> "terminated":
            self.status = "updating"

        if reload:
            self.clear_sa()

        self.checkrelations()
        self.check_related_order_by()
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
            self.make_table_aliases()
            for table in self.tables.itervalues():
                for field in table.fields.itervalues():
                    if hasattr(field, "event"):
                        field.event.add_event(self)
                table.make_schema_dict()
        except (custom_exceptions.NoDatabaseError,\
                custom_exceptions.RelationError):
            pass
        if reload == True and self.status <> "terminated":
            self.status = "active"

    def clear_sa(self):
        sa.orm.clear_mappers()
        self.metadata.clear()
        for table in self.tables.itervalues():
            table.foriegn_key_columns_current = None
            table.mapper = None
            table.sa_class = None
            table.sa_table = None
            table.paths = None
            table.local_tables = None
            table.one_to_many_tables = None
            table.events = []
            table.initial_events = []
            table.schema_dict = None
        self.graph = None


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

    def search(self, table_name, where = None, *args, **kw):

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

        result = self.search(table_name, *args, limit = 2, **kw)
        data = result.results

        if not data or len(data) == 2:
            raise custom_exceptions.SingleResultError("one result not found")

        return result.data[0]


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

    def make_graph(self):

        if self.graph is not None and len(self.graph.nodes()) == len(self.tables):
            return

        gr = nx.MultiDiGraph()

        for table in self.tables.keys():
            gr.add_node(table)

        for rel in self.relations:
            gr.add_edge(rel.table.name, rel.other, None, {"relation" : rel})

        self.graph = gr

    def make_table_aliases(self, root_table = None):

        if "_core_entity" in self.tables and not root_table:
            root_table = "_core_entity"
        aliases = {}

        if root_table:
            unique_aliases = set()
            paths = get_paths(self.graph, root_table)
            unique_aliases.update([root_table])
            for key, edge in paths.iteritems():
                unique_aliases.update([edge.name])
            for key, value in self.tables.iteritems():
                unique_aliases.update([key])

            for item in unique_aliases:
                if len(item.split(".")) == 1:
                    aliases[item] = self.get_class(item)
                else:
                    aliases[item] = sa.orm.aliased(self.get_class(item.split(".")[-1]))
        else:
            for key, value in self.tables.iteritems():
                aliases[key] = value.sa_class

        self.aliases = aliases



def table(name, database, *args, **kw):
    """helper to add table to database args and keywords same as Table definition"""
    if name in database.tables:
        print '<%s> exists will not create' % name
        return
    database.add_table(tables.Table(name, *args, quiet = database.quiet, **kw))

def entity(name, database, *args, **kw):
    """helper to add entity to database args and keywords same as Table definition"""
    if name in database.tables:
        print '<%s> exists will not create' % name
        return
    database.add_entity(tables.Table(name, *args, quiet = database.quiet, **kw))

def relation(name, database, *args, **kw):
    """helper to add entity to database args and keywords same as Table definition"""
    if name in database.tables:
        print '<%s> exists will not create' % name
        return
    database.add_relation_table(tables.Table(name, *args, quiet = database.quiet, **kw))

