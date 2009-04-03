##   This file is part of Reformed.
##
##   Reformed is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License version 2 as 
##   published by the Free Software Foundation.
##
##   Reformed is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with Reformed.  If not, see <http://www.gnu.org/licenses/>.
##
##   -----------------------------------------------------------------
##	
##   Reformed
##   Copyright (c) 2008-2009 Toby Dacre & David Raznick
##	
##	columns.py
##	======
##	
##	This file contains the classes that hold information about database
##  fields such as name,type, indexes and constraints. 

import sqlalchemy as sa
import custom_exceptions 
import formencode
from formencode import validators

class BaseSchema(object):
    """Base class of everthing that turn into a database field or 
    constraint or index. Its only use is to gather the type and name
    of the field, constraint or index.

    :param type: This is either a sqlalchemy type or a string 
            with onetomany, manytoone or onetoone to define join types.

    :param use_parent:  if True will use its parents (Field) column parameters
                  instead.
    """

    def __init__(self, type,*args, **kw):

        self.type = type
        self.name = kw.pop("name", None)
        self.use_parent=kw.pop("use_parent", False)
        self.use_parent_options= kw.pop("use_parent_options", False)
        self.args = args
        self.kw = kw
        self.original_table = kw.pop("original_table", None)
        self.sa_options ={}
    
    def _set_name(self, Field, name):
        if self.use_parent:
            self.name = Field.decendants_name
        else:
            self.name = name

    def _set_sa_options(self, Field):

        if self.use_parent or self.use_parent_options:
            self.sa_options.update(Field._sa_options)
            

    def __repr__(self):
        return "<class = %s , name = %s , type = %s>" % ( self.__class__.__name__, self.name
                                           ,self.type ) 
    
    @property
    def table(self):
        """The table object accociated with this object"""
        if self.original_table:
            return self.original_table
        if not hasattr(self,"parent"):
            raise custom_exceptions.NoFieldError("no field defined for column")
        return self.parent.table                                         

class Column(BaseSchema):
    """Contains information to make a database field.
    :param default: default value for the column
    :param onupdate: value whenever the accosiated row is updated"""

    def __init__(self, type,*args, **kw):

        super(Column,self).__init__(type ,*args, **kw)
        ##original column should be made private. 
        self.original_column = kw.pop("original_column", None)
        default = kw.pop("default", None)
        if default:
            self.sa_options["default"] = default
        onupdate = kw.pop("onupdate", None)
        if onupdate:
            self.sa_options["onupdate"] = onupdate
        mandatory = kw.pop("mandatory", False)
        if mandatory:
            self.sa_options["nullable"] = False
        self.validation = kw.pop("validation", None)

    def _set_parent(self, parent, name):
        
        self._set_name(parent ,name)
        self._set_sa_options(parent)
        
        if self.use_parent:
            if parent._length:
                self.type = self.type(parent._length)
            if parent._validation:
                self.validation = parent._validation
            
        if self.name in parent.items.iterkeys():
            raise AttributeError("column already in field definition")
        else: 
            parent._add_column(self.name, self)
            self.parent = parent
        
class Relation(BaseSchema):
    """Specifies a relationship between the table where this relation
    is defined and another table.

    type AND other are mandatory for relations

    :param other: The name of the table where this reltaion will
      join to.

    """

    def __init__(self, type, other, *args, **kw):

        super(Relation,self).__init__(type ,*args, **kw)
        self.other = other 
        self.order_by = kw.pop("order_by", None)

        eager = kw.pop("eager", None)
        if eager:
            self.sa_options["lazy"] = not eager
        cascade = kw.pop("cascade", None)
        if cascade:
            self.sa_options["cascade"] = cascade
        self.many_side_mandatory = kw.pop("many_side_mandatory", True)

    @property
    def order_by_list(self):
        if self.order_by:
            columns_split = self.order_by.split(",")
            order_by = [a.split() for a in columns_split] 
            for col in order_by:
                if len(col) == 1:
                    col.append("")
            return order_by
        else:
            return []
        
    def _set_parent(self, parent, name):
        """adds this relation to a field object"""
        self._set_name(parent ,name)
        self._set_sa_options(parent)

        if self.use_parent:
            if parent._order_by:
                self.order_by = parent._order_by
            if parent._many_side_mandatory is False:
                self.many_side_mandatory = parent._many_side_mandatory 

        if self.name in parent.items.iterkeys():
            raise AttributeError("column already in field definition")
        else:
            parent._add_relation(self.name, self)
            self.parent = parent

    @property
    def other_table(self):
        """Table object of related table"""
        
        try:
            return self.parent.table.database.tables[self.other]
        except AttributeError:
            return None
        
class Field(object):
    """ This is intended to be sublassed and should be the only way
    a database field or relation can be made.  This object can contain
    one or more column object (representing a database field) or one
    relation object (representing a database relataion with a foreign key).
    Examples are in fields.py

    :param name:  field name will be used as column name if use_parent is 
           used"""

    
    def __new__(cls, name, *args, **kw):

        #TODO namespace issues need to be sorted out
        obj = object.__new__(cls)
        obj.name = name
        obj.decendants_name=name
        obj.columns = {}
        obj.relations = {}
        obj._sa_options = {}
        obj._column_order = []
        obj._kw = kw
        obj._default = kw.get("default", None)
        if obj._default:
            obj._sa_options["default"] = obj._default
        obj._onupdate = kw.get("onupdate", None)
        if obj._onupdate:
            obj._sa_options["onupdate"] = obj._onupdate
        obj._mandatory = kw.get("mandatory", False)
        if obj._mandatory:
            obj._sa_options["nullable"] = False
        obj._eager = kw.get("eager", None)
        if obj._eager:
            obj._sa_options["lazy"] = not obj._eager
        obj._cascade = kw.get("cascade", None)
        if obj._cascade:
            obj._sa_options["cascade"] = obj._cascade
        obj._validation = kw.get("validation",None)
        if obj._validation:
            obj._validation = r"%s" % obj._validation.encode("ascii")
        obj._order_by = kw.get("order_by", None)
        obj._length = kw.get("length", None)
        if obj._length:
            obj._length = int(obj._length)
        obj._many_side_mandatory = kw.get("many_side_mandatory", True)
        return obj

    def __repr__(self):
        return "<%s - %s>" % (self.name, self._column_order)

    def __setattr__(self, name, value):

        if isinstance(value, BaseSchema):
            value._set_parent(self, name)
        else:
            object.__setattr__(self, name, value)

    @property
    def items(self):
        items = {}
        items.update(self.columns)
        items.update(self.relations)
        return items

    def _add_column(self, name, column):
        self.columns[name] = column
        self._column_order.append(name)

    def _add_relation(self, name, relation):
        self.relations[name] = relation

    def _set_parent(self, table):
        for n,v in self.items.iteritems():
            if n in table.items.iterkeys():
                raise AttributeError("already an item named %s" % n)
                
        table.fields[self.name] = self
        table.field_order.append(self.name)
        table.add_relations()
        if hasattr(table, "database"):
            table.database.add_relations()
        self.table = table
   
