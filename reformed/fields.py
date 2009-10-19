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

from columns import Column, Field, Relation, Constraint
import decimal
import columns
import formencode
import validators
import sqlalchemy as sa
import datetime
import events


class Text(Field):
    
    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Unicode(100),  use_parent = True)

class TextLookupValidated(Field):
    
    def __init__(self, name, target, *args, **kw):
        self.text = Column(sa.Unicode(100),  use_parent = True)

        filter_field = kw.get("filter_field", None)
        filter_value = kw.get("filter_value", None)

        self.validation = {name: validators.CheckInField(target, 
                                                         filter_field = filter_field,
                                                         filter_value = filter_value )}

class Unicode(Field):
    
    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Unicode(100), use_parent = True)


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
        self.address_line_1 = Column(sa.Unicode(100))
        self.address_line_2 = Column(sa.Unicode(100))
        self.address_line_3 = Column(sa.Unicode(100))
        self.postcode = Column(sa.Unicode(100))
        self.town = Column(sa.Unicode(100))
        self.country = Column(sa.Unicode(100))

        self.validation = {"address_line_1": validators.String(
                                                        not_empty = True),
                           "postcode": validators.String(not_empty =True)
                          }

class RequireIfMissing(Field):

    def __init__(self, name, *args, **kw):

        field = kw.get("field")
        missing = kw.get("missing")

        self.chained_validator = validators.RequireIfMissing(field, missing = missing)


class CheckOverLappingDates(Field):

    def __init__(self, name, *args, **kw):

        parent_table = kw.get("parent_table")
        self.chained_validator = validators.CheckNoOverlappingDates(parent_table)


class CheckNoTwoNulls(Field):

    def __init__(self, name, *args, **kw):

        parent_table = kw.get("parent_table")
        field = kw.get("field")
        self.chained_validator = validators.CheckNoTwoNulls(parent_table, field)

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
        
class Numeric(Field):

    def __init__(self, name, *args, **kw):
        self.money = Column(sa.Numeric, use_parent = True)

class Email(Field):
    
    def __init__(self, name, *args, **kw):
        self.email = Column(sa.Unicode(100), use_parent_options = True)
        self.validation = {"email" : validators.Email()}


class Date(Field):
    
    def __init__(self, name, *args, **kw):
        self.date = Column(sa.Date, use_parent = True)


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
        self.onetoone = Relation("onetoone", other, use_parent = True)


class Index(Field):

    def __init__(self, name, fields, *args, **kw):
        self.other = fields
        self.index = columns.Index("normal", fields, use_parent = True)

class UniqueIndex(Field):

    def __init__(self, name, fields, *args, **kw):
        self.other = fields
        self.index = columns.Index("unique", fields, use_parent = True)
    
class UniqueConstraint(Field):

    def __init__(self, name, fields, *args, **kw):
        self.other = fields
        self.index = columns.Constraint("unique", fields, use_parent = True)

class SumDecimal(Field):

    def __init__(self, name, target, *args, **kw):

        self.other = target
        self.total_amount = Column(sa.Numeric, default = 0, use_parent = True)
        self.base_level = kw.get("base_level", None)
        self.event = events.SumEvent(target, self, self.base_level)

class CountRows(Field):

    def __init__(self, name, target, *args, **kw):

        self.other = target
        self.base_level = kw.get("base_level", None)
        self.count = Column(sa.Integer, default = 0, use_parent = True)
        self.event = events.CountEvent(target, self, self.base_level)

class AddRow(Field):

    def __init__(self, name, target, *args, **kw):

        self.other = target
        self.base_level = kw.get("base_level", None)
        self.initial_event = kw.get("initial_event", False)
        self.event = events.AddRow(target, self, self.base_level, initial_event = self.initial_event)

class MaxDate(Field):

    def __init__(self, name, target, *args, **kw):

        self.other = target
        self.base_level = kw.get("base_level", None)
        self.exists = Column(sa.DateTime, use_parent = True)
        self.event = events.MaxDate(target, self, self.base_level)

class Counter(Field):

    def __init__(self, name, target = None, *args, **kw):

        self.base_level = kw.get("base_level", None)

        self.counter = Column(sa.Integer, default = 0, validate = False, use_parent = True)

        self.event = events.Counter(target, self, self.base_level)



class CopyTextAfter(Field):

    def __init__(self, name, target, *args, **kw):

        self.other = target
        self.base_level = kw.get("base_level", None)
        fields = kw.get("fields", None)
        self.changed_flag = kw.get("changed_flag", None)
        self.update_when_flag = kw.get("update_when_flag" , None)

        self.field_name = kw.get("field_name" , None)

        if not self.field_name:
            self.exists = Column(sa.Unicode(100), use_parent = True)

        if fields:
            self.event = events.CopyTextAfter(target, self, self.base_level,
                                              field_list = fields,
                                              changed_flag = self.changed_flag,
                                              field_name = self.field_name,
                                              update_when_flag = self.update_when_flag)
        else:
            self.event = events.CopyTextAfter(target, self, self.base_level,
                                              changed_flag = self.changed_flag,
                                              field_name = self.field_name,
                                              update_when_flag = self.update_when_flag)

class CopyTextAfterField(Field):

    def __init__(self, name, target, *args, **kw):

        self.other = target
        self.base_level = kw.get("base_level", None)
        fields = kw.get("fields", None)
        self.changed_flag = kw.get("changed_flag", None)
        self.update_when_flag = kw.get("update_when_flag" , None)

        self.field_name = kw.get("field_name" , None)

        if not self.field_name:
            self.exists = Column(sa.Unicode(100), use_parent = True)

        if fields:
            self.event = events.CopyTextAfterField(target, self, self.base_level,
                                              field_list = fields,
                                              changed_flag = self.changed_flag,
                                              field_name = self.field_name,
                                              update_when_flag = self.update_when_flag)
        else:
            self.event = events.CopyTextAfterField(target, self, self.base_level,
                                              changed_flag = self.changed_flag,
                                              field_name = self.field_name,
                                              update_when_flag = self.update_when_flag)

class CopyText(Field):

    def __init__(self, name, target, *args, **kw):

        self.other = target
        self.base_level = kw.get("base_level", None)
        fields = kw.get("fields", None)
        counter = kw.get("counter", "counter")
        self.changed_flag = kw.get("changed_flag", None)
        self.update_when_flag = kw.get("update_when_flag" , None)

        self.field_name = kw.get("field_name" , None)

        self.exists = Column(sa.Unicode(100), use_parent = True)

        if fields:
            self.event = events.CopyText(target, self, self.base_level,
                                              field_list = fields,
                                              changed_flag = self.changed_flag,
                                              counter = counter,
                                              field_name = self.field_name,
                                              update_when_flag = self.update_when_flag)
        else:
            self.event = events.CopyText(target, self, self.base_level,
                                              changed_flag = self.changed_flag,
                                              counter = counter,
                                              field_name = self.field_name,
                                              update_when_flag = self.update_when_flag)
