#!/usr/bin/env python
import sqlalchemy as sa


class BaseSchema(object):
    
    def __init__(self, type,*args, **kw):
        """ Defines the information needed to make an actual database field """
        self.type = type
        self.use_field_name=kw.pop("use_field_name", False)
    
    def _set_name(self, Field, name):
        if self.use_field_name:
            self.name = Field.name
        else:
            self.name = name

class Columns(BaseSchema):
    
    def _set_parent(self, Field, name):
        
        self._set_name(Field, name)
            
        if self.name in Field.items.iterkeys():
            raise AttributeError("column already in field definition")
        else: 
            Field.columns[self.name] = self
            self.field = Field
        
class Relations(BaseSchema):

    def __init__(self, type, *args, **kw):

        super(Relations,self).__init__(self, type,*args, **kw)
        self.other = args[0]
        
    def _set_parent(self, Field, name):
        
        self._set_name(Field, name)
            
        if self.name in Field.items.iterkeys():
            raise AttributeError("column already in field definition")
        else:
            Field.relations[self.name] = self
            self.field = Field
        
class Fields(object):
    
    def __init__(self, name, *args, **kw):
        """ the base class of all Fields.  A field is a composite of many real
        database columns"""
        self.name = name
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

    def _set_parent(self, Table):
        
        for n,v in self.items.iteritems():
            if n in Table.items.iterkeys():
                raise AtributeError("already an item named %s" % n)
                
        Table.fields[self.name] = self
        self.table = Table
    
class Text(Fields):
    
    def __init__(self, name, *args, **kw):
        
        self.text = Columns(sa.Unicode, use_field_name = True)

        super(Text,self).__init__(name, *args, **kw)
    
class ManyToOne(Fields):
    
    def __init__(self, name, other, *args, **kw):

        self.manytoone = Relations("manytoone", other, use_field_name = True)
    
        super(ManyToOne,self).__init__(name, *args, **kw)

class OneToMany(Fields):
    
    def __init__(self, name, other, *args, **kw):

        self.onetomany = Relations("onetomany", other, use_field_name = True)
    
        super(OneToMany,self).__init__(name, *args, **kw)

class OneToOne(Fields):
    
    def __init__(self, name, other, *args, **kw):

        self.onetoone = Relations("onetoone",other,use_field_name = True)
    
        super(OneToOne,self).__init__(name, *args, **kw)
