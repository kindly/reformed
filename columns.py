#!/usr/bin/env python
import sqlalchemy as sa


class BaseSchema(object):
    
    def __init__(self, type,*args, **kw):
        """ Defines the information needed to make an actual database field """
        self.type = type
        self.name = kw.pop("name", None)
        self.original_table = kw.pop("original_table", None)
        self.use_parent_name=kw.pop("use_parent_name", False)
        self.args = args
        self.kw = kw
    
    def _set_name(self, Field, name):
        if self.use_parent_name:
            self.name = Field.decendants_name
        else:
            self.name = name

class Columns(BaseSchema):
    
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
                
        Table.fields[self.name] = self
        self.table = Table
    
class Text(Fields):
    
    def __init__(self, name, *args, **kw):
        
        self.text = Columns(sa.Unicode, use_parent_name = True)

        super(Text,self).__init__(name, *args, **kw)
    
class ManyToOne(Fields):
    
    def __init__(self, name, other, *args, **kw):

        self.manytoone = Relations("manytoone", other, use_parent_name = True)
    
        super(ManyToOne,self).__init__(name, *args, **kw)

class OneToMany(Fields):
    
    def __init__(self, name, other, *args, **kw):

        self.onetomany = Relations("onetomany", other, use_parent_name = True)
    
        super(OneToMany,self).__init__(name, *args, **kw)

class OneToOne(Fields):
    
    def __init__(self, name, other, *args, **kw):

        self.onetoone = Relations("onetoone",other,use_parent_name = True)
    
        super(OneToOne,self).__init__(name, *args, **kw)
