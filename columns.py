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

        use_parent_name :  if True will use its parents name (Field name) 
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
        """The table object accociated with this object"""
        if self.original_table:
            return self.original_table
        if not hasattr(self,"parent"):
            raise custom_exceptions.NoFieldError("no field defined for column")
        return self.parent.table                                         

class Columns(BaseSchema):
    
    def __init__(self, type,*args, **kw):

        """This gathers parameters to be given to a sqlalchemy Column object. It 
        defines a database field.
        
        default : default value for the column
        onupdate : value whenever the accosiated row is updated
        """


        super(Columns,self).__init__(type ,*args, **kw)
        ##original column should be made private. 
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

        type AND other are mandatory for relations
        
        other: The name of the table where this reltaion will join to.
        
        """

        super(Relations,self).__init__(type ,*args, **kw)
        self.other = args[0]
        
    def _set_parent(self, parent, name):
        """adds this relation to a field object"""
        
        self._set_name(parent, name)
            
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
        
class Fields(object):
    """ This is intended to be sublassed and should be the only way
    a database field or relation can be made.  This object can contain
    one or more column object (representing a database field) or one
    relation object (representing a database relataion with a foreign key).
    Examples are in Fields.py"""

    
    def __init__(self, name, *args, **kw):
        """ 
        This gathers metadata from the subclassed objects and stores the columns
        and relations information.
        
        name:  field name will be used as column name if use parent name is 
               used
        
        """
        #TODO namespace issues need to be sorted out
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
   
