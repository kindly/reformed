#!/usr/bin/env python
import sqlalchemy as sa
import custom_exceptions 
import formencode
from formencode import validators

class BaseSchema(object):
    
    def __init__(self, type,*args, **kw):
        """ Defines the information needed to make an actual database field """
        self.type = type
        self.name = kw.pop("name", None)
        self.use_parent_name=kw.pop("use_parent_name", False)
        self.args = args
        self.kw = kw
        self.original_table = kw.pop("original_table", None)
    
    def _set_name(self, Field, name):
        if self.use_parent_name:
            self.name = Field.decendants_name
        else:
            self.name = name
    
    @property
    def table(self):
        if self.original_table:
            return self.original_table
        if not hasattr(self,"parent"):
            raise custom_exceptions.NoFieldError("no field defined for column")
        return self.parent.table                                         

class Columns(BaseSchema):

    
    def __init__(self, type,*args, **kw):
        super(Columns,self).__init__(type ,*args, **kw)
        self.original_column = kw.pop("original_column", None)

    def _set_parent(self, parent, name):
        
        self._set_name(parent ,name)
            
        if self.name in parent.items.iterkeys():
            raise AttributeError("column already in field definition")
        else: 
            parent._add_column(self.name, self)
            self.parent = parent
        
class Relations(BaseSchema):

    def __init__(self, type, *args, **kw):

        super(Relations,self).__init__(type ,*args, **kw)
        self.other = args[0]
        
    def _set_parent(self, parent, name):
        
        self._set_name(parent, name)
            
        if self.name in parent.items.iterkeys():
            raise AttributeError("column already in field definition")
        else:
            parent._add_relation(self.name, self)
            self.parent = parent

    @property
    def other_table(self):
        
        try:
            return self.parent.table.database.tables[self.other]
        except AttributeError:
            return None
        
class Fields(object):
    
    def __init__(self, name, *args, **kw):
        """ the base class of all Fields.  A field is a composite of many real
        database columns"""
        self.name = name
        self.decendants_name=name
        self.columns = {}
        self.relations = {}

        for n,v in self.__dict__.iteritems():
            if hasattr(v,"_set_parent"):
                v._set_parent(self,n)

    @property
    def items(self):
        items = {}
        items.update(self.columns)
        items.update(self.relations)
        return items

    def _add_column(self, name, column):
        self.columns[name] = column

    def _add_relation(self, name, relation):
        self.relations[name] = relation

    def _set_parent(self, Table):
        for n,v in self.items.iteritems():
            if n in Table.items.iterkeys():
                raise AtributeError("already an item named %s" % n)
                
        Table.add_field(self)
        self.table = Table
    
