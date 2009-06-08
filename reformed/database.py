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
import resultset
import tables
from fields import ManyToOne
import fields as field_types
import boot_tables
import sessionwrapper
import validate_database
import logging
import networkx as nx

logger = logging.getLogger('reformed.main')
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")
reformedhandler = logging.FileHandler("log.log")
reformedhandler.setFormatter(formatter)

logger.addHandler(reformedhandler)

class Database(object):
    
    def __init__(self,name,*args,**kw):
        self.name =name
        self.tables = {}
        self.metadata = kw.pop("metadata",None)
        self.engine = kw.pop("engine",None)
        self._Session = kw.pop("session",None)
        self.metadata.bind = self.engine
        self.Session = sessionwrapper.SessionClass(self._Session, self)
        self.persisted = False
        boots = boot_tables.boot_tables()
        self.boot_tables =boots.boot_tables
        self.graph = None
        self.load_from_persist()
        for table in args:
            self.add_table(table)
        self.persist()


    def add_table(self, table):

        if table.name in self.tables.iterkeys():
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

        #if self.persisted == True:
        #    self.persist()
    
    def _add_table_no_persist(self, table):

        table._set_parent(self)

    def persist(self):

        if not self.persisted:
            for table in self.boot_tables:
                if table.name in self.tables.iterkeys():
                    break
                self.add_table(table)
        self.update_sa()
        self.metadata.create_all(self.engine)
        for table in self.tables.itervalues():
            if not table.persisted:
                table.persist()
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

            self.add_table(tables.Table( row.table_name.encode("ascii"), *fields, **kw))

        for table in self.tables.itervalues():
            table.persisted = True

        # for first time do not say database is persisted
        if all_tables:
            self.persisted = True
            
        self.update_sa()
        session.close()

    def add_relations(self):     #not property for optimisation
        self.relations = []
        for table_name,table_value in self.tables.iteritems():
            for rel_name,rel_value in table_value.relations.iteritems():
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
                table.make_sa_table()
                table.make_sa_class()
                table.make_paths()
            for table in self.tables.itervalues():
                table.sa_mapper()
            sa.orm.compile_mappers()
            for table in self.tables.itervalues():
                for column in table.columns.iterkeys():
                    getattr(table.sa_class, column).impl.active_history = True
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
        self.graph = None
            

    def tables_with_relations(self,Table):
        relations = {}
        for n, v in Table.relations.iteritems():
            relations[(v.other,"this")] = v
        for v in self.relations:
            if v.other == Table.name:
                relations[(v.table.name,"other")] = v
        return relations

    def query(self, session, queryset):

        return resultset.ResultSet(self, session, queryset)

    def logged_table(self, logged_table):

        logging_table = tables.Table("_log_"+ logged_table.name,
                                     logged = False,
                                     modified_date = False)

        for column in logged_table.columns.itervalues():
            
            ##FIXME if type is an object (not a class) need different rules
            if hasattr(column.type,"length"):
                length = column.type.length
                field =getattr(field_types, column.type.__class__.__name__)\
                              (column.name, length = length)
            else:
                field =getattr(field_types, column.type.__name__)(column.name)
            
            logging_table.add_field(field)

        logging_table.add_field(ManyToOne(logged_table.name+"_logged" 
                                         ,logged_table.name ))

        return logging_table

    def update_tables(self):

        for table in self.tables.values():
                              
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
            gr.add_edge(rel.table.name, rel.other, rel)

        self.graph = gr




    



    
