import sqlalchemy as sa
import custom_exceptions
import resultset
import tables
from fields import ManyToOne
import fields as field_types
import boot_tables

class Database(object):
    
    def __init__(self,name,*args,**kw):
        self.name =name
        self.tables = {}
        self.metadata = kw.pop("metadata",None)
        self.engine = kw.pop("engine",None)
        self.Session = kw.pop("session",None)
        self.persisted = False
        boots = boot_tables.boot_tables()
        self.boot_tables =boots.boot_tables
        self.load_from_persist()
        for table in args:
            self.add_table(table)
        self.persist()

    def add_table(self, table):

        if table.name in self.tables.keys():
            raise custom_exceptions.DuplicateTableError("already a table named %s" 
                                                        % table.name)
        for field in table.fields.values():
            if not hasattr(field, "other") or field.other not in self.tables.keys():
                continue
            if (hasattr(field, "onetoone") or hasattr(field, "onetomany")) and \
               self.tables[field.other].persisted is True:
                raise custom_exceptions.NoTableAddError("table %s cannot be added"
                                                        % table.name)

        table._set_parent(self)


    def persist(self):

        if not self.persisted:
            for table in self.boot_tables:
                if table.name in self.tables.keys():
                    break
                self.add_table(table)
        self.update_sa()
        self.metadata.create_all(self.engine)
        for table in self.tables.values():
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

        for row in all_tables:
            if row.table_name.startswith("__"):
                continue
            fields = []
            for field in row.field:
                fields.append(getattr(field_types, field.type)( field.name,
                                                             field.other))
            kw = {}
            for table_param in row.table_params:
                if table_param.value == u"True":
                    value = True
                elif table_param.value == u"False":
                    value = False
                else:
                    value = table_param.value 
                kw[table_param.item.encode("ascii")] = value

            self.add_table(tables.Table( row.table_name.encode("ascii"), *fields, **kw))

        for table in self.tables.values():
            table.persisted = True
            
        self.update_sa()
        self.persisted = True

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

        logging_table = tables.Table("_log_"+ logged_table.name , logged = False)

        for columns in logged_table.columns.itervalues():
            logging_table.add_additional_column(columns)

        logging_table.add_field(ManyToOne(logged_table.name+"_logged" 
                                         ,logged_table.name ))

        return logging_table

    def update_tables(self):

       for table in self.tables.values():
           
           if table.logged and "_log_%s" % table.name not in self.tables.keys() :
               self.add_table(self.logged_table(table))

    def get_class(self, table):

        if table not in self.tables.iterkeys():
            raise custom_exceptions.NoTableError("table %s does not exist" % table)

        return self.tables[table].sa_class

    def get_instance(self, table):

        if table not in self.tables.iterkeys():
            raise custom_exceptions.NoTableError("table %s does not exist" % table)

        return self.tables[table].sa_class()

    
