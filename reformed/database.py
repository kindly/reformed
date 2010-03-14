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
import time
from collections import defaultdict
from util import get_paths, get_all_local_data
from fields import ManyToOne, OneToOne, OneToMany, Integer, CopyTextAfter, CopyTextAfterField, DeleteRow
import fields as field_types
import boot_tables
import sessionwrapper
import validate_database
import logging
import networkx as nx
import job_scheduler
import threading
import os

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
log_file = os.path.join(root, "log.log")

logger = logging.getLogger('reformed.main')
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")
reformedhandler = logging.FileHandler(log_file)
reformedhandler.setFormatter(formatter)

logger.addHandler(reformedhandler)

class Database(object):

    def __init__(self, name, *args, **kw):

        self.status = "updating"
        self.name =name
        self.tables = {}
        self.metadata = kw.pop("metadata", None)
        self.engine = kw.pop("engine", None)
        self._Session = kw.pop("session", None)
        self.entity = kw.pop("entity", False)
        self.logging_tables = kw.pop("logging_tables", True)
        self.metadata.bind = self.engine
        self.Session = sessionwrapper.SessionClass(self._Session, self)
        self.persisted = False
        boots = boot_tables.boot_tables()
        self.boot_tables = boots.boot_tables
        self.graph = None
        self.fields_to_persist = []
        self.load_from_persist()
        if self.entity:
            self.add_entity_table()
        for table in args:
            if table.entity is True:
                self.add_entity(table)
            else:
                self.add_table(table)
        #self.persist()
        self.status = "active"
        #self.job_scheduler = job_scheduler.JobScheduler(self)
        self.manager_thread = ManagerThread(self, threading.currentThread())
        self.manager_thread.start()

        self.job_scheduler = job_scheduler.JobScheduler(self)

        self.scheduler_thread = job_scheduler.JobSchedulerThread(self, threading.currentThread())

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

        if table.name in self.tables.iterkeys():
            if ignore:
                return
            elif drop:
                self.drop_table(table.name)
            else:
                raise custom_exceptions.DuplicateTableError("already a table named %s"
                                                            % table.name)

        for field in table.fields.itervalues():
            if not hasattr(field, "other") or field.other not in self.tables.iterkeys():
                continue
            ##TODO Horrible mess, need to do much better checking of relations and
            ##need to sort out field column divide for relations
            relation_types= [relation.type for relation in field.relations.itervalues()]
            if ("onetoone" in relation_types or "onetomany" in relation_types) and \
               self.tables[field.other].persisted is True:
                raise custom_exceptions.NoTableAddError("table %s cannot be added"
                                                        % table.name)

        self._add_table_no_persist(table)

    def rename_table(self, table, new_name, session = None):

        if isinstance(table, tables.Table):
            table_to_rename = table
        else:
            table_to_rename = self.tables[table]

        if session:
            defer_update = True
        else:
            session = self.Session()
            defer_update = False

        try:
            #update fields in other tables so that they do not have to change their name
            for relations in table_to_rename.tables_with_relations.itervalues():
                for relation in relations:
                    if relation.foreign_key_table <> table_to_rename.name:
                        field = relation.parent
                        foreign_key_name = relation.foriegn_key_id_name
                        row = field.get_field_row_from_table(session)
                        row.foreign_key_name = u"%s" % foreign_key_name
                        session.save(row)

            for relations in table_to_rename.tables_with_relations.values():
                for rel in relations:
                    if rel.other == table_to_rename.name:
                        field = rel.parent
                        row = field.get_field_row_from_table(session)
                        row.other = u"%s" % new_name
                        session.save(row)

            row = table_to_rename.get_table_row_from_table(session)
            row.table_name = u"%s" % new_name
            session.save(row)
            session._flush()

            if table_to_rename.logged:
                self.rename_table("_log_%s" % table_to_rename.name, "_log_%s" % new_name, session)

            table_to_rename.sa_table.rename(new_name)
        except Exception, e:
            session.rollback()
            raise
        else:
            if not defer_update:
                session._commit()
                self.load_from_persist(True)
        finally:
            if not defer_update:
                session.close()

    def drop_table(self, table):

        session = self.Session()

        try:
            if isinstance(table, tables.Table):
                table_to_drop = table
            else:
                table_to_drop = self.tables[table]

            if table_to_drop.dependant_tables:
                raise custom_exceptions.DependencyError((
                    "cannot delete table %s as the following tables"
                    " depend on it %s" % (table.name, table.dependant_tables)))

            row = table_to_drop.get_table_row_from_table(session)
            session.delete(row)

            for relations in table_to_drop.tables_with_relations.itervalues():
                for relation in relations:
                    row = relation.parent.get_field_row_from_table(session)
                    session.delete(row)

            session._flush()

            table_to_drop.sa_table.drop()

        except Exception, e:
            session.rollback()
            raise
        else:
            session.commit()
            self.load_from_persist(True)
            self.add_relations()
        finally:
            session.close()

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


    def add_entity_table(self):

        if "_core_entity" not in self.tables:
            entity_table = tables.Table("_core_entity",
                                  field_types.Integer("table"),
                                  field_types.Text("title"),
                                  field_types.Text("summary"),
                                  table_type = "internal",
                                  summary = u'The entity table'
                                  )

            self.add_table(entity_table)


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

        if not self.persisted:
            for table in self.boot_tables:
                if table.name in self.tables.iterkeys():
                    break
                self.add_table(table)
        self.update_sa(reload = True)

        session = self.Session()

        try:
            for table in self.tables.itervalues():
                if not table.persisted:
                    table.persist(session)
            for field in self.fields_to_persist:
                field.table._persist_extra_field(field, session)

            session._flush()

            for table in self.tables.itervalues():
                table.persist_foreign_key_columns(session)

            session._flush()

            self.metadata.create_all(self.engine)
        except Exception, e:
            session.rollback()
            raise
        else:
            session._commit()
        finally:
            session.close


        self.load_from_persist(True)


        self.fields_to_persist = []
        self.persisted = True

        self.status = "updating"


    def load_from_persist(self, restart = False):

        session = self.Session()

        self.tables = {}
        self.clear_sa()
        #old boot table state causes issues
        boots = boot_tables.boot_tables()
        self.boot_tables = boots.boot_tables

        for table in self.boot_tables:
            self.add_table(table)

        self.update_sa()
        self.metadata.create_all(self.engine)

        all_tables = session.query(self.tables["__table"].sa_class).all()

        self.tables = {}
        self.clear_sa()

        ## only persist boot tables if first time
        if not all_tables:
            self.persist()
            self.persisted = False #make sure database is not seen as persisted
            return

        for row in all_tables:
            fields = []
            for field in row.field:
                field_name = field.field_name.encode("ascii")
                if field.other:
                    field_other = field.other.encode("ascii")
                else:
                    field_other = field.other

                if field.foreign_key_name:
                    foreign_key_name = field.foreign_key_name.encode("ascii")
                else:
                    foreign_key_name = field.foreign_key_name

                field_kw = {}
                for field_param in field.field_params:
                    if field_param.value == u"True":
                        value = True
                    elif field_param.value == u"False":
                        value = False
                    else:
                        value = field_param.value
                    field_kw[field_param.item.encode("ascii")] = value

                fields.append(getattr(field_types, field.type)(field_name,
                                                              field_other,
                                                              foreign_key_name = foreign_key_name,
                                                              order = field.order,
                                                              field_id = field.id,
                                                              **field_kw))
            kw = {}
            for table_param in row.table_params:
                if table_param.value == u"True":
                    value = True
                elif table_param.value == u"False":
                    value = False
                else:
                    value = table_param.value
                kw[table_param.item.encode("ascii")] = value

            kw["table_id"] = row.id

            self.add_table(tables.Table(row.table_name.encode("ascii"), *fields, **kw))

        for table in self.tables.itervalues():
            table.persisted = True

            orders = [field.order for field in table.fields.values() if field.order]

            if orders:
                table.current_order = max(orders)

        # for first time do not say database is persisted
        if all_tables:
            self.persisted = True

        self.update_sa()
        self.validate_database()
        session.close()

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


    def update_sa(self, reload = False, update_tables = True):
        if reload == True and self.status <> "terminated":
            self.status = "updating"

        if reload:
            self.clear_sa()

        if update_tables:
            self.update_tables()
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

        # convert string values to int
        try:
            limit = int(kw.get("limit", None))
        except:
            limit = None
        count = kw.get("count", False)
        # convert string values to int
        try:
            offset = int(kw.get("offset", 0))
        except:
            offset = 0
        keep_all = kw.get("keep_all", True)
        internal = kw.get("internal", False)
        tables = kw.get("tables", [table_name])
        fields = kw.get("fields", None)

        if "order_by" not in kw:
            kw["order_by"] = "id"


        one_to_many_tables = []

        for table in tables:
            if table == table_name:
                continue
            if table not in self[table_name].local_tables:
                one_to_many_tables.append(self.aliases[table])

        if one_to_many_tables:
            kw["distinct_many"] = True
        query = search.Search(self, table_name, session, where, *args, **kw).search()
        session.close()

        for cls in one_to_many_tables:
            query = query.add_entity(cls)

        if fields:
            tables = None


        try:
            if limit:
                results = query[offset: offset + limit]
            else:
                results = query.all()

            if external_session:
                return results

            data = []
            for result in results:
                if one_to_many_tables:
                    obj = result[0]
                    extra_obj = result[1:]
                else:
                    obj = result
                    extra_obj = None

                data.append(get_all_local_data(obj,
                                       tables = tables,
                                       fields = fields,
                                       internal = internal,
                                       keep_all = keep_all,
                                       allow_system = True,
                                       extra_obj = extra_obj))

            wrapped_results = {"data": data}

            if count:
                wrapped_results["__count"] = query.count()
            return wrapped_results
        except Exception, e:
            session.rollback()
            raise
        finally:
            session.close()

    def search_single(self, table_name, *args, **kw):

        result = self.search(table_name, *args, limit = 2, **kw)

        if isinstance(result, dict):
            result = result["data"]

        if not result or len(result) == 2:
            raise custom_exceptions.SingleResultError("one result not found")
        return result[0]


    def logged_table(self, logged_table):

        logging_table = tables.Table("_log_"+ logged_table.name,
                                     logged = False,
                                     modified_date = False)

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

        #logging_table.add_field(ManyToOne(logged_table.name+"_logged"
        #                                 , logged_table.name ))

        return logging_table

    def update_tables(self):

        for table in self.tables.values():
            if not self.logging_tables:
                table.logged = False
            if table.logged and "_log_%s" % table.name not in self.tables.iterkeys() :
                self.add_table(self.logged_table(table))
        for table in self.tables.values():
            table.add_foriegn_key_field()

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


class ManagerThread(threading.Thread):

    def __init__(self, database, initiator_thread):

        super(ManagerThread, self).__init__()
        self.initiator_thread = initiator_thread
        self.database = database

    def run(self):

        while True:
            if not self.initiator_thread.isAlive():
                self.database.status = "terminated"
            if self.database.status == "terminated":
                self.database.job_scheduler.stop()
                if self.database.scheduler_thread.isAlive():
                    self.database.scheduler_thread.stop()
                    self.database.scheduler_thread.join()
                break
            time.sleep(1)

def table(name, database, *args, **kw):
    """helper to add table to database args and keywords same as Table definition"""
    database.add_table(tables.Table(name, *args, **kw))

def entity(name, database, *args, **kw):
    """helper to add entity to database args and keywords same as Table definition"""
    database.add_entity(tables.Table(name, *args, **kw))

def relation(name, database, *args, **kw):
    """helper to add entity to database args and keywords same as Table definition"""
    database.add_relation_table(tables.Table(name, *args, **kw))

