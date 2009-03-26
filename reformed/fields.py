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
##	This file contains all the standard reformed field subclasses

from columns import *
import datetime

class Text(Field):
    
    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Unicode, use_parent = True)


class Unicode(Field):
    
    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Unicode, use_parent = True)


class Modified(Field):
    
    def __init__(self, name, *args, **kw):
        self.modified_date = Column(sa.DateTime,
                                     onupdate=datetime.datetime.now,
                                     default =datetime.datetime.now)


class DateTime(Field):
    
    def __init__(self, name, *args, **kw):
        self.text = Column(sa.DateTime, use_parent = True)


class Integer(Field):
    
    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Integer, use_parent = True)

    
class Address(Field):
    
    def __init__(self, name, *args, **kw):
        self.address_line_1 = Column(sa.Unicode)
        self.address_line_2 = Column(sa.Unicode)
        self.address_line_3 = Column(sa.Unicode)
        self.postcode = Column(sa.Unicode)
        self.town = Column(sa.Unicode)
        self.country = Column(sa.Unicode)

        self.validation = {"address_line_1": validators.String(
                                                        not_empty = True),
                           "postcode": validators.String(not_empty =True)
                          }


class Binary(Field):

    def __init__(self, name, *args, **kw):
        self.money = Column(sa.Binary, use_parent = True)
        
        
class Boolean(Field):

    def __init__(self, name, *args, **kw):
        self.money = Column(sa.Boolean, use_parent = True)
        
        
class Money(Field):

    def __init__(self, name, *args, **kw):
        self.money = Column(sa.Numeric, use_parent = True)
        

class Numeric(Field):

    def __init__(self, name, *args, **kw):
        self.money = Column(sa.Numeric, use_parent = True)
        

class Email(Field):
    
    def __init__(self, name, *args, **kw):
        self.email = Column(sa.Unicode, use_parent_options = True)
        self.validation = {"email" : validators.Email()}


class Date(Field):
    
    def __init__(self, name, *args, **kw):
        self.date = Column(sa.Date)


class ManyToOne(Field):
    
    def __init__(self, name, other, *args, **kw):
        self.other = other
        self.manytoone = Relation("manytoone", other, use_parent = True)
    

class OneToMany(Field):
    
    def __init__(self, name, other, *args, **kw):
        self.other = other
        self.onetomany = Relation("onetomany", other, use_parent = True)
    

class OneToManyEager(Field):
    
    def __init__(self, name, other, *args, **kw):
        self.other = other
        self.onetomany = Relation("onetomany", other, eager = True, cascade="all, delete-orphan",  use_parent = True)
    

class OneToOne(Field):
    
    def __init__(self, name, other, *args, **kw):
        self.other = other
        self.onetoone = Relation("onetoone",other,use_parent = True)
    
