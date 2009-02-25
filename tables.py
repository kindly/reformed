#!/usr/bin/env python
from sqlalchemy.orm import mapper
import sqlalchemy as sa
from sqlalchemy.orm import column_property
from columns import Columns
import custom_exceptions
import formencode
from fields import Modified
from sqlalchemy.orm.interfaces import AttributeExtension

class Table(object):
    
    def __init__(self, name, *args , **kw):
        self.name =name
        self.kw = kw
        self.field_list = args
        self.fields = {}
        self.additional_columns = {}
        self.primary_key = kw.get("primary_key", None)
        self.persisted = kw.get("persisted", False)
        self.entity = kw.get("entity", False)
        self.logged = kw.get("logged", True)
        self.entity_relationship = kw.get("entity_relationship", False)
        if self.primary_key:
            self.primary_key_list = self.primary_key.split(",")
        else:
            self.primary_key_list = []

        for key in self.primary_key_list:
            column_names = []
            for fields in args:
                for column in fields.columns.itervalues():
                    column_names.append(column.name)
            if key not in column_names:
                raise AttributeError("%s is not a column" % key)

        for fields in args:
            fields._set_parent(self)

        if "modified_date" not in self.fields.keys():
            self.add_field(Modified("modified_date"))
        self.sa_table = None
        self.sa_class = None
        self.mapper = None

    def persist(self):
                
        session = self.database.Session()
        __table = self.database.tables["__table"].sa_class()
        __table.table_name = u"%s" % self.name

        for n, v in self.kw.iteritems():
            __table_param = self.database.tables["__table_params"].sa_class()
            __table_param.item = u"%s" % n
            __table_param.value = u"%s" % str(v) 
            __table.table_params.append(__table_param)

        for n, v in self.fields.iteritems():
            __field = self.database.tables["__field"].sa_class()
            __field.name = u"%s" % n
            __field.type = u"%s" % v.__class__.__name__
            if hasattr(v, "other"):
                __field.other = u"%s" % v.other
            __table.field.append(__field)

        session.add(__table)
        session.commit()
        self.persisted = True
        session.close()

    def add_additional_column(self, column):
        self.additional_columns[column.name] = column

    def add_field(self,field):
        field._set_parent(self)
#        self.update_sa()
    
    def update_sa(self):
        try:
            self.check_database()
            self.database.update_sa()
        except custom_exceptions.NoDatabaseError:
            pass

    @property    
    def items(self):
        items = {}
        for n,v in self.fields.iteritems():
            for n,v in v.items.iteritems():
                items[n]=v
        return items

    @property    
    def defined_columns(self):
        columns = {}
        for n,v in self.fields.iteritems():
            for n,v in v.columns.iteritems():
                columns[n]=v
        return columns

    @property    
    def columns(self):
        columns = {}
        for n,v in self.fields.iteritems():
            for n,v in v.columns.iteritems():
                columns[n]=v
        for n,v in self.additional_columns.iteritems():
            columns[n]=v
        try:
            for n,v in self.foriegn_key_columns.iteritems():
                columns[n] = v
        except custom_exceptions.NoDatabaseError:
            pass
        return columns

    @property    
    def relations(self):
        relations = {}
        for n,v in self.fields.iteritems():
            for n,v in v.relations.iteritems():
                relations[n]=v
        return relations

    @property
    def primary_key_columns(self):
        columns = {}
        if self.primary_key:
            for n, v in self.defined_columns.iteritems():
                if n in self.primary_key_list:
                    columns[n] = v
#        else:
#            columns["id"] = Columns(sa.Integer, name = "id")
        return columns

    @property
    def defined_non_primary_key_columns(self):
        columns = {}
        for n, v in self.defined_columns.iteritems():
            if n not in self.primary_key_list:
                columns[n] = v
        return columns

    def check_database(self):
        if not hasattr(self,"database"):
            raise custom_exceptions.NoDatabaseError,\
                  "Table %s has not been assigned a database" % self.name

    def _set_parent(self,Database):
        Database.tables[self.name]=self
        self.database = Database
#        self.update_sa()

    @property    
    def related_tables(self):
        self.check_database()
        return self.database.related_tables(self)

    @property    
    def tables_with_relations(self):
        self.check_database()
        return self.database.tables_with_relations(self)

    @property    
    def foriegn_key_columns(self):
        self.check_database()
        d = self.database
        columns={}
        for table, rel in self.tables_with_relations.iteritems():
            if (rel.type == "onetomany" and self.name == rel.other) or\
              (rel.type == "onetoone" and self.name == rel.other) or\
              (rel.type == "manytoone" and self.name == rel.table.name):
                if d.tables[table].primary_key_columns:
                    for n, v in d.tables[table].primary_key_columns.items():
                        columns[n] = Columns(v.type,
                                             name=n,
                                             original_table= table,
                                             original_column= n)
                else:
                    columns[table+'_id'] = Columns(sa.Integer,
                                                   name = table+'_id',
                                                   original_table= table,
                                                   original_column= "id")
        return columns


    @property
    def foreign_key_constraints(self):

        foreign_key_constraints = {}
        self.check_database()
        d = self.database
        for table, rel in self.tables_with_relations.iteritems():
            other_table_columns=[]
            this_table_columns=[]
            for n, v in self.foriegn_key_columns.iteritems():
                if v.original_table == table:
                    other_table_columns.append("%s.%s"%\
                                               (table,v.original_column))
                    this_table_columns.append(n)
            if other_table_columns:
                foreign_key_constraints[table] = [this_table_columns,
                                                  other_table_columns]
        return foreign_key_constraints

    def make_sa_table(self):
        if self.sa_table:
            return
        self.check_database()
        if not self.database.metadata:
            raise custom_exceptions.NoMetadataError("table not assigned a metadata")
        sa_table = sa.Table(self.name, self.database.metadata)
#        for n,v in self.primary_key_columns.iteritems():
#            sa_table.append_column(sa.Column(n, v.type, primary_key = True))
#        for n,v in self.defined_non_primary_key_columns.iteritems():
#            sa_table.append_column(sa.Column(n, v.type))
        sa_table.append_column(sa.Column("id", sa.Integer, primary_key = True))
        for n,v in self.defined_columns.iteritems():
            sa_options = v.sa_options
            sa_table.append_column(sa.Column(n, v.type, **sa_options))
        if self.primary_key_list:
            primary_keys = tuple(self.primary_key_list)
            sa_table.append_constraint(sa.UniqueConstraint(*primary_keys))
        for n,v in self.foriegn_key_columns.iteritems():
            sa_table.append_column(sa.Column(n, v.type))
        for n,v in self.additional_columns.iteritems():
            sa_table.append_column(sa.Column(n, v.type))
        if self.foreign_key_constraints:
            for n,v in self.foreign_key_constraints.iteritems():
                sa_table.append_constraint(sa.ForeignKeyConstraint(v[0],
                                                                   v[1]))
        self.sa_table = sa_table
   
    def make_sa_class(self):

        if self.sa_class:
            return
        table = self
        class sa_class(object):
            def __init__(self):
                self._table = table 
            @sa.orm.reconstructor
            def _table(self):
                self._table = table
        sa_class.__name__ = self.name
        self.sa_class = sa_class

    def sa_mapper(self):
        if self.mapper is None:
            properties ={}
            for column in self.columns:
                properties[column] = column_property( getattr(self.sa_table.c,column),
                                                     extension = AttributeExtension())
            for relation in self.relations.itervalues():
                other_class = self.database.tables[relation.other].sa_class
                properties[relation.name] = sa.orm.relation(other_class,
                                                        backref = self.name)
            self.mapper = mapper(self.sa_class, self.sa_table, properties = properties)
#           self.mapper.compile()
            #sa.orm.compile_mappers()
#           for column in self.columns.keys():
#               print getattr(self.sa_class, column).impl.active_history
#               getattr(self.sa_class, column).impl.active_history = True
#               print getattr(self.sa_class, column).impl.active_history

    @property
    def validation_schema(self):

        schema_dict = {}
        for n,v in self.fields.iteritems():
            if hasattr(v,"validation"):
                schema_dict.update(v.validation)
        return formencode.Schema(allow_extra_fields =True, **schema_dict)
    
    def validate(self, instance):
        
        validation_dict = {}
        for n,v in self.columns.iteritems():
            validation_dict[n] = getattr(instance, n)

        return self.validation_schema.to_python(validation_dict)
    
    def logged_instance(self, instance):

        logged_instance = self.database.tables["_log_" + self.name].sa_class()
        for n,v in self.columns.iteritems():
            setattr(logged_instance, n, getattr(instance,n))
        return logged_instance


