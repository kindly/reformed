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
from util import get_paths, get_all_local_data
from fields import ManyToOne, OneToOne, OneToMany, Integer, CopyTextAfter, CopyTextAfterField
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
        self.persist()
        #self.job_scheduler = job_scheduler.JobScheduler(self)
        self.scheduler_thread = job_scheduler.JobSchedulerThread(self, threading.currentThread())
        self.job_scheduler = self.scheduler_thread.job_scheduler


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

    def drop_table(self, table):

        session = self.Session()

        if isinstance(table, tables.Table):
            table_to_drop = table
        else:
            table_to_drop = self.tables[table]

        if table_to_drop.logged:
            logger_instance = session.query(self.get_class("__table")).filter_by(table_name = u"_log_%s" % table_to_drop.name).one()
            session.delete(logger_instance)
            self.tables["_log_" + table_to_drop.name].sa_table.drop() 
            self.tables.pop("_log_" + table_to_drop.name)

        instance = session.query(self.get_class("__table")).filter_by(table_name = u"%s" % table_to_drop.name).one()
        session.delete(instance)
        table_to_drop.sa_table.drop()
        self.tables.pop(table_to_drop.name)

        session.commit()
        self.add_relations()
        self.update_sa(reload = True)
        session.close()

    @property
    def t(self):
        class Tables(object):
            pass
        tables = Tables()
        for name, table in self.aliases.iteritems():
            setattr(tables, name, table) 
        return tables

    def add_entity_table(self):

        if "_core_entity" not in self.tables:
            entity_table = tables.Table("_core_entity",
                                  field_types.Integer("table"),
                                  field_types.Text("title"),
                                  field_types.Text("summary"),
                                  OneToMany("relation",
                                            "relation"),
                                  )

            relation =  tables.Table("relation",
                               field_types.Text("relation_type"),
                               ManyToOne("_core_entity", "_core_entity", one_way = True)
                              )

            self.add_table(entity_table)
            self.add_table(relation)


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

    
    def _add_table_no_persist(self, table):

        table._set_parent(self)

    def persist(self):

        if not self.persisted:
            for table in self.boot_tables:
                if table.name in self.tables.iterkeys():
                    break
                self.add_table(table)
        self.update_sa(reload = True)
        self.metadata.create_all(self.engine)
        for table in self.tables.itervalues():
            if not table.persisted:
                table.persist()
        for field in self.fields_to_persist:
            field.table._persist_extra_field(field)
        if self.fields_to_persist:
            self.update_sa(reload = True)
        self.fields_to_persist = []
        self.persisted = True


    def load_from_persist(self):

        session = self.Session()
        
        for table in self.boot_tables:
            self.add_table(table)
        self.update_sa()
        self.metadata.create_all(self.engine)
            
        all_tables = session.query(self.tables["__table"].sa_class).all()
        


        ## only persist boot tables if first time
        if not all_tables:
            self.persist()
            self.persisted = False #make sure database is not seen as persisted

        for row in all_tables:
            if row.table_name.endswith(u"__table")  or\
               row.table_name.endswith(u"__table_params")  or\
               row.table_name.endswith(u"__field")  or\
               row.table_name.endswith(u"__field_params"):
                continue
            fields = []
            for field in row.field:
                field_name = field.field_name.encode("ascii")
                if field.other:
                    field_other = field.other.encode("ascii") 
                else:
                    field_other = field.other
                field_kw = {}
                for field_param in field.field_params:
                    if field_param.value == u"True":
                        value = True
                    elif field_param.value == u"False":
                        value = False
                    else:
                        value = field_param.value 
                    field_kw[field_param.item.encode("ascii")] = value

                fields.append(getattr(field_types, field.type)( field_name,
                                                             field_other,
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

        # for first time do not say database is persisted
        if all_tables:
            self.persisted = True
            
        self.update_sa()
        session.close()

    def add_relations(self):     #not property for optimisation
        self.relations = []
        for table_name, table_value in self.tables.iteritems():
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
        if update_tables:
            self.update_tables()
        self.checkrelations()
        self.check_related_order_by()
        if reload:
            self.clear_sa()
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

    def clear_sa(self):
        sa.orm.clear_mappers()
        self.metadata.clear()
        for table in self.tables.itervalues():
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
        relations = {}
        for n, v in table.relations.iteritems():
            relations[(v.other, "here")] = v
        for v in self.relations:
            if v.other == table.name:
                relations[(v.table.name, "other")] = v
        return relations

    def result_set(self, search):

        return resultset.ResultSet(search)
    
    def search(self, table_name, *args, **kw): 

        session = self.Session()

        limit = kw.get("limit", None)
        offset = kw.get("offset", 0)
        internal = kw.get("internal", False)
        query = search.Search(self, table_name, session, *args)
        tables = kw.get("tables", [table_name])

        fields = kw.get("fields", None)

        #if not tables:
        #    if table_name == "_core_entity":
        #        tables = ["_core_entity"]
        #    if self.tables[table_name].entity:
        #        tables = ["_core_entity"]
        #        for table in self.tables[table_name].local_tables:
        #            if table.count("summary"):
        #                tables.append(table)

        if fields:
            tables = None

        if limit:
            result = resultset.ResultSet(query, result_num = limit, offset = offset).first_set()
        else:
            result = resultset.ResultSet(query).all()

        try:
            return [get_all_local_data(obj, 
                                       tables = tables, 
                                       fields = fields,
                                       internal = internal, 
                                       keep_all = True, 
                                       allow_system = True) for obj in result]    
        except Exception, e:
            session.rollback()
            raise
        finally:
            session.close()
        
    def search_single(self, table_name, *args, **kw): 

        result = self.search(table_name, *args, limit = 2, **kw)
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

        logging_table.add_field(Integer("%s_id" % logged_table.name))

        #logging_table.add_field(ManyToOne(logged_table.name+"_logged" 
        #                                 , logged_table.name ))

        return logging_table

    def update_tables(self):

        for table in self.tables.values():
            if not self.logging_tables:
                table.logged = False
            if table.logged and "_log_%s" % table.name not in self.tables.iterkeys() :
                self.add_table(self.logged_table(table))

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

        gr = nx.DiGraph()

        for table in self.tables.keys():
            gr.add_node(table)

        for rel in self.relations:
            gr.add_edge(rel.table.name, rel.other, relation = rel)

        self.graph = gr

    def make_table_aliases(self, root_table = None):

        if "_core_entity" in self.tables and not root_table:
            root_table = "_core_entity"
        aliases = {} 

        if root_table:
            unique_aliases = set()
            paths = get_paths(self.graph, root_table)
            unique_aliases.update([(root_table,)])
            for key, value in paths.iteritems():
                table, join, one_ways = value
                unique_aliases.update([tuple(one_ways + [table])])
            for key, value in self.tables.iteritems():
                unique_aliases.update([(key,)])
            
            for item in unique_aliases:
                if len(item) == 1:
                    aliases[item[0]] = self.get_class(item[0])
                else:
                    aliases["_".join(item)] = sa.orm.aliased(self.get_class(item[-1]))
        else:
            for key, value in self.tables.iteritems():
                aliases[key] = value.sa_class

        self.aliases = aliases






                
                

                






    




