import sqlalchemy as sa
import custom_exceptions
import resultset
import tables
from fields import ManyToOne
import boot_tables

class Database(object):
    
    def __init__(self,name,*args,**kw):
        self.name =name
        self.tables = {}
        self.metadata = kw.pop("metadata",None)
        self.engine = kw.pop("engine",None)
        self.Session = kw.pop("session",None)
        for table in args:
            self.add_table(table)


    def add_table(self, table):

 #       if table.name in self.tables.keys():
  #          raise custom_exceptions.DuplicateTableError("already a table named %s" 
   #                                                     % table.name)

        table._set_parent(self)

#   def __getattr__(self, name):
#       
#       if name not in self.tables.keys():
#           raise AttributeError("Table %s does not exist" % name)
#       return self.tables["name"].sa_class

    def persist(self):

        for table in boot_tables.boot_tables:
            self.add_table(table)
        self.update_sa()
        self.metadata.create_all(self.engine)

        for table in self.tables.values():
            if not table.persisted:
                table.persist()
        

    @property
    def relations(self):
        relations = []
        for table_name,table_value in self.tables.iteritems():
            for rel_name,rel_value in table_value.relations.iteritems():
                relations.append(rel_value)
        return relations                

    def checkrelations(self):
        for relation in self.relations:
            if relation.other not in self.tables.iterkeys():
                raise custom_exceptions.RelationError,\
                        "table %s does not exits" % relation.other
 
    def update_sa(self):
        self.update_tables()
        try:
            for table in self.tables.itervalues():
#               if table.sa_table:
#                   self.metadata.remove(table.sa_table)
                table.make_sa_table()
                table.make_sa_class()
            for table in self.tables.itervalues():
                table.sa_mapper()
        except (custom_exceptions.NoDatabaseError,\
                custom_exceptions.RelationError):
            pass

    def tables_with_relations(self,Table):
        self.checkrelations()
        relations = {}
        for n, v in Table.relations.iteritems():
            relations[v.other] = v
        for v in self.relations:
            if v.other == Table.name:
                relations[v.table.name] = v
        return relations

    def related_tables(self, Table):
        self.checkrelations()
        related_tables = {}
        for n, v in Table.relations.iteritems():
            related_tables[v.other] = v.type
        for v in self.relations:
            if v.other == Table.name:
                if v.type == 'manytoone':
                    relation = 'onetomany'
                elif v.type == 'onetomany':
                    relation = 'manytoone'
                elif v.type == 'onetoone':
                    relation = 'onetooneother'
                else:
                    relation = v.type
                related_tables[v.parent.table.name] = relation
        return related_tables

    def query(self, session, queryset):

        return resultset.ResultSet(self, session, queryset)

    def logged_table(self, logged_table):

        logging_table = tables.Table(logged_table.name + "_log", logged = False)

        for columns in logged_table.columns.itervalues():
            logging_table.add_additional_column(columns)

        logging_table.add_field(ManyToOne(logged_table.name+"_logged" 
                                         ,logged_table.name ))

        return logging_table

    def update_tables(self):

       for table in self.tables.values():
           if table.logged:
               self.add_table(self.logged_table(table))
