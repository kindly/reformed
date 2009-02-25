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
##	fields.py
##	======
##	
##	This file contains all the standard reformed field sublesse

from columns import *
import datetime

class Text(Fields):
    
    def __init__(self, name, *args, **kw):
        self.text = Columns(sa.Unicode, use_parent_name = True)

        super(Text,self).__init__(name, *args, **kw)

class Modified(Fields):
    
    def __init__(self, name, *args, **kw):
        self.modified_date = Columns(sa.DateTime,
                                     onupdate=datetime.datetime.now,
                                     default =datetime.datetime.now)

        super(Modified,self).__init__(name, *args, **kw)

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

        self.validation = {"address_line_1": validators.String(
                                                        not_empty = True),
                           "postcode": validators.String(not_empty =True)
                          }

        super(Address, self).__init__(name, *args, **kw)

class Binary(Fields):

    def __init__(self, name, *args, **kw):
        self.money = Columns(sa.Binary, use_parent_name = True)
        
        super(Binary, self).__init__(name, *args, **kw)
        
class Boolean(Fields):

    def __init__(self, name, *args, **kw):
        self.money = Columns(sa.Boolean, use_parent_name = True)
        
        super(Boolean, self).__init__(name, *args, **kw)
        
class Money(Fields):

    def __init__(self, name, *args, **kw):
        self.money = Columns(sa.Numeric, use_parent_name = True)
        
        super(Money, self).__init__(name, *args, **kw)

class Email(Fields):
    
    def __init__(self, name, *args, **kw):
        self.email = Columns(sa.Unicode)
        self.validation = {"email" : validators.Email()}

        super(Email, self).__init__(name, *args, **kw)

class Date(Fields):
    
    def __init__(self, name, *args, **kw):
        self.date = Columns(sa.Date)

        super(Date, self).__init__(name, *args, **kw)

class ManyToOne(Fields):
    
    def __init__(self, name, other, *args, **kw):
        self.other = other
        self.manytoone = Relations("manytoone", other, use_parent_name = True)
    
        super(ManyToOne,self).__init__(name, *args, **kw)

class OneToMany(Fields):
    
    def __init__(self, name, other, *args, **kw):
        self.other = other
        self.onetomany = Relations("onetomany", other, use_parent_name = True)
    
        super(OneToMany,self).__init__(name, *args, **kw)

class OneToOne(Fields):
    
    def __init__(self, name, other, *args, **kw):
        self.other = other
        self.onetoone = Relations("onetoone",other,use_parent_name = True)
    
        super(OneToOne,self).__init__(name, *args, **kw)
