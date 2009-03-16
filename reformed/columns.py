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
    
    def __init__(self, type,*args, **kw):
        """Base class of everthing that turn into a database field,
        constraint or index. Its only use is to gather the type and name
        of the field, constraint or index.

        Type :  mandatory this is either a sqlalchemy type or a string 
                with onetomany, manytoone or onetoone to define join types.

        use_parent :  if True will use its parents (Field) column parameters
                      instead.
                     
        """
        self.type = type
        self.name = kw.pop("name", None)
        self.use_parent=kw.pop("use_parent", False)
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

        if self.use_parent:
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
    
    def __init__(self, type,*args, **kw):

        """This gathers parameters to be given to a sqlalchemy Column object. It 
        defines a database field.
        
        default : default value for the column
        onupdate : value whenever the accosiated row is updated
        """

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
            self.sa_options["nullable"] = not mandatory

    def _set_parent(self, parent, name):
        
        self._set_name(parent ,name)
        self._set_sa_options(parent)
        
        if parent._length:
            self.type = self.type(parent._length)
            
        if self.name in parent.items.iterkeys():
            raise AttributeError("column already in field definition")
        else: 
            parent._add_column(self.name, self)
            self.parent = parent
        
class Relation(BaseSchema):

    def __init__(self, type, *args, **kw):

        """specifies a relationship between the table where this relation
        is defined and another table.

        type AND other are mandatory for relations
        
        other: The name of the table where this reltaion will join to.
        
        """

        super(Relation,self).__init__(type ,*args, **kw)
        self.other = args[0]
        self.order_by = kw.pop("order_by", None)

        eager = kw.pop("eager", None)
        if eager:
            self.sa_options["lazy"] = not eager
        cascade = kw.pop("cascade", None)
        if cascade:
            self.sa_options["cascade"] = cascade

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

        if parent._order_by:
            self.order_by = parent._order_by

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
    Examples are in fields.py"""

    
    def __init__(self, name, *args, **kw):
        """ 
        This gathers metadata from the subclassed objects and stores the columns
        and relations information.
        
        name:  field name will be used as column name if use_parent is 
               used
        
        """
        #TODO namespace issues need to be sorted out
        self.name = name
        self.decendants_name=name
        self.columns = {}
        self.relations = {}
        self._sa_options = {}
        _default = kw.pop("default", None)
        if _default:
            self._sa_options["default"] = _default
        _onupdate = kw.pop("onupdate", None)
        if _onupdate:
            self._sa_options["onupdate"] = _onupdate
        _mandatory = kw.pop("mandatory", False)
        if _mandatory:
            self._sa_options["nullable"] = not _mandatory
        _eager = kw.pop("eager", None)
        if _eager:
            self.sa_options["lazy"] = not _eager
        _cascade = kw.pop("cascade", None)
        if _cascade:
            self.sa_options["cascade"] = _cascade
        self._order_by = kw.pop("order_by", None)
        self._length = kw.pop("length", None)

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
                raise AttributeError("already an item named %s" % n)
                
        Table.fields[self.name] = self
        self.table = Table
   
