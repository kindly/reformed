#!/usr/bin/env python
import sqlalchemy as sa
import custom_exceptions 

class BaseSchema(object):
    
    def __init__(self, type,*args, **kw):
        """ Defines the information needed to make an actual database field """
        self.type = type
        self.name = kw.pop("name", None)
        self.original_table = kw.pop("original_table", None)
        self.original_column = kw.pop("original_column", None)
        self.use_parent_name=kw.pop("use_parent_name", False)
        self.args = args
        self.kw = kw
    
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
    
class Text(Fields):
    
    def __init__(self, name, *args, **kw):
        self.text = Columns(sa.Unicode, use_parent_name = True)

        super(Text,self).__init__(name, *args, **kw)

class Integer(Fields):
    
    def __init__(self, name, *args, **kw):
        self.text = Columns(sa.Integer, use_parent_name = True)

        super(Integer, self).__init__(name, *args, **kw)
    
class Address(Fields):
    
    def __init__(self, name, *args, **kw):
        self.address_line_1 = Columns(sa.Unicode)
        self.address_line_2 = Columns(sa.Unicode)
        self.address_line_3 = Columns(sa.Unicode)
        self.postcode = Columns(sa.Unicode)
        self.town = Columns(sa.Unicode)
        self.country = Columns(sa.Unicode)

        super(Address, self).__init__(name, *args, **kw)

class Binary(Fields):

    def __init__(self, name, *args, **kw):
        self.money = Columns(sa.Binary, use_parent_name = True)
        
        super(Binary, self).__init__(name, *args, **kw)
        
class Money(Fields):

    def __init__(self, name, *args, **kw):
        self.money = Columns(sa.Numeric, use_parent_name = True)
        
        super(Money, self).__init__(name, *args, **kw)

class Email(Fields):
    
    def __init__(self, name, *args, **kw):
        self.email = Columns(sa.Unicode)

        super(Email, self).__init__(name, *args, **kw)

class Date(Fields):
    
    def __init__(self, name, *args, **kw):
        self.email = Columns(sa.Date)

        super(Date, self).__init__(name, *args, **kw)

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
