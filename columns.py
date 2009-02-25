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
##	This file contains the base classes for all reformed fields. Fields
##  are composites of many real database columns.

import sqlalchemy as sa
import custom_exceptions 
import formencode
from formencode import validators

class BaseSchema(object):
    
    def __init__(self, type,*args, **kw):
        """Base class of everthing that turn into a real database coulumn
        constraint or index. 

        Type :  mandatory this is either a sqlalchemy type or a string 
                with onetomany, manytoone or onetoone to define join types.

        use_parent_name :  if True will use its parents name (field name) 
                           to define its name. 
                     
        """
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

    def __repr__(self):
        return "<class = %s , name = %s , type = %s>" % ( self.__class__.__name__, self.name
                                           ,self.type ) 
    
    @property
    def table(self):
        if self.original_table:
            return self.original_table
        if not hasattr(self,"parent"):
            raise custom_exceptions.NoFieldError("no field defined for column")
        return self.parent.table                                         

class Columns(BaseSchema):

    
    def __init__(self, type,*args, **kw):

        """This will be used to make a real database column
        
        default : default value for the column
        onupdate : value whenever the accosiated row is updated
        """


        super(Columns,self).__init__(type ,*args, **kw)
        self.original_column = kw.pop("original_column", None)
        self.sa_options ={}
        default = kw.pop("default", None)
        if default:
            self.sa_options["default"] = default
        onupdate = kw.pop("onupdate", None)
        if onupdate:
            self.sa_options["onupdate"] = onupdate

    def _set_parent(self, parent, name):
        
        self._set_name(parent ,name)
            
        if self.name in parent.items.iterkeys():
            raise AttributeError("column already in field definition")
        else: 
            parent._add_column(self.name, self)
            self.parent = parent
        
class Relations(BaseSchema):

    def __init__(self, type, *args, **kw):

        """specifies a relationship between the table where this relation
        is defined and another table.

        type AND other are mandatory for relations"""

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

        """Table of related table"""
        
        try:
            return self.parent.table.database.tables[self.other]
        except AttributeError:
            return None
        
class Fields(object):
    
    def __init__(self, name, *args, **kw):
        """ The base class of all Fields.  A field is a composite of many real
        database columns
        
        name:  field name will be used as column name if use parent name is 
               used
        
        """
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
                raise AttributeError("already an item named %s" % n)
                
        Table.fields[self.name] = self
        self.table = Table
   
