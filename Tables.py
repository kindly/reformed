#!/usr/bin/env python
import sqlalchemy as sa

class Table(object):
    
    def __init__(self,name,*args,**kw):
        
        self.name =name
        
        self.fields = {}
        
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
