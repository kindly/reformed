#!/usr/bin/env python
from sqlalchemy.orm import mapper
import sqlalchemy as sa
from columns import Columns
import custom_exceptions

class Table(object):
    
    def __init__(self,name,*args,**kw):
        self.name =name
        self.fields = {}
        self.primary_key = kw.pop("primary_key", None)
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

    def add_field(self,field):
        self.fields[field.name] = field
        self.update_sa()
    
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
        else:
            columns["id"] = Columns(sa.Integer, name = "id")
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
        self.update_sa()

    @property    
    def related_tables(self):
        self.check_database()
        return self.database.related_tables(self)

    @property    
    def foriegn_key_columns(self):
        self.check_database()
        d = self.database
        columns={}
        for table, rel in self.related_tables.iteritems():
            if rel == "manytoone":
                for n, v in d.tables[table].primary_key_columns.iteritems():
                    if n == 'id':
                        columns[table+'_id'] =\
                                Columns(v.type,
                                        name = table+'_id',
                                        original_table= table)
                    else:
                        columns[n] = Columns(v.type,
                                             name=n,
                                             original_table= table)
        return columns

    def make_sa_table(self):
        self.check_database()
        if not self.database.metadata:
            raise NoMetadataError("table not assigned a metadata")
        sa_table = sa.Table(self.name, self.database.metadata)
        for n,v in self.primary_key_columns.iteritems():
            sa_table.append_column(sa.Column(n, v.type, primary_key = True))
        for n,v in self.defined_non_primary_key_columns.iteritems():
            sa_table.append_column(sa.Column(n, v.type))
        foriegn_key_columns = []
        related_primary_key_columns =[]
        for n,v in self.foriegn_key_columns.iteritems():
            sa_table.append_column(sa.Column(n, v.type))
            foriegn_key_columns.append(n)
            other_name = "id" if n.endswith("_id") else n
            related_primary_key_columns.append("%s.%s" % (v.original_table,
                                                          other_name)) 
        if foriegn_key_columns:
            sa_table.append_constraint(
                                sa.ForeignKeyConstraint(foriegn_key_columns,
                                   related_primary_key_columns))
        self.sa_table = sa_table
   
    def make_sa_class(self):
        class sa_class(object):
            pass
        self.sa_class = sa_class

    def sa_mapper(self):
        self.properties ={}
        
        






