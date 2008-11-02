#!/usr/bin/env python
import sqlalchemy as sa

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
    
    @property    
    def items(self):
        items = {}
        for n,v in self.fields.iteritems():
            for n,v in v.items.iteritems():
                items[n]=v
        return items

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

    def _set_parent(self,Database):

        Database.tables[self.name]=self
        self.database = Database

    @property    
    def sa_defined_columns(self):
        columns = []
        for n, v in self.columns.iteritems():
            columns.append(sa.Column(v.name,
                                     v.type))
        return columns

    @property
    def sa_defined_primary_keys(self):
        columns = []
        if not self.primary_key:
            columns.append(sa.Column("id", 
                                     sa.Integer,
                                     primary_key = True))
        else:
            for n, v in self.columns.iteritems():
                if n in self.primary_key_list:
                    columns.append(sa.Column(v.name,
                                             v.type,
                                             primary_key = True))
        return columns

    def sa_extra_columns(self):
        columns = []
        if not hasattr(self,"database"):
            raise AttributeError,\
                    "Table %s has not been assigned a datatabase" % self.name
