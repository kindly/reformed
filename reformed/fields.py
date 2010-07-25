#   This file is part of Reformed.
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

import sys
sys.path.append(".")

from columns import Column, Field, Relation, Constraint
import decimal
import columns
import formencode
import global_session as html_session
import validators
import sqlalchemy as sa
import datetime
import events

def get_user_id():

    try:
        user_id = html_session.global_session.session["user_id"]
    except AttributeError, e:
        user_id = 1

    return user_id



class Text(Field):

    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Unicode(100, assert_unicode = False), use_parent = True)

class Password(Field):

    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Unicode(70, assert_unicode = False),  use_parent = True)

class LookupTextValidated(Field):

    extra_kw = ["filter_field", "filter_value"]

    def __init__(self, name, target, *args, **kw):
        self.data_type = "Text"
        self.text = Column(sa.Unicode(100),  use_parent = True)
        self.other = target

        filter_field = kw.get("filter_field", None)
        filter_value = kw.get("filter_value", None)

        self.validation = {name: validators.CheckInField(target,
                                                         filter_field = filter_field,
                                                         filter_value = filter_value )}

class Unicode(Field):

    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Unicode(100), use_parent = True)

class Created(Field):

    def __init__(self, name, *args, **kw):
        self.cat = "internal"
        self.data_type = "DateTime"
        self.created_date = Column(sa.DateTime,
                                   default = datetime.datetime.now)


class CreatedBy(Field):
    def __init__(self, *args, **kw):
        self.cat = "internal"
        self.name = "_created_by"
        #self.created_by = Column(sa.Integer,
        #                         default = get_user_id)
        self._created_by = Relation("manytoone", "user",
                                    foreign_key_name = "created_by",
                                    no_auto_path = True,
                                    many_side_not_null = False,
                                    many_side_default = get_user_id,
                                    backref = False)

class Modified(Field):

    def __init__(self, name, *args, **kw):
        self._modified_date = Column(sa.DateTime,
                                     onupdate = datetime.datetime.now,
                                     default = datetime.datetime.now)

class ModifiedBySession(Field):

    def __init__(self, name, *args, **kw):
        self.name = "__modified_by"
        self.modified_by = Relation("manytoone", "user",
                                    foreign_key_name = "_modified_by",
                                    no_auto_path = True,
                                    many_side_onupdate = get_user_id,
                                    many_side_default = get_user_id,
                                    many_side_not_null = False,
                                    backref = False)

class ModifiedByNoRelation(Field):

    def __init__(self, name, *args, **kw):

        self._modified_by = Column(sa.Integer,
                                  onupdate = get_user_id,
                                  default = get_user_id)

class DateTime(Field):

    def __init__(self, name, *args, **kw):
        self.text = Column(sa.DateTime, use_parent = True)


class Integer(Field):

    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Integer, use_parent = True)

class Image(Field):

    def __init__(self, name, *args, **kw):
        self.text = Column(sa.Integer, use_parent = True)

class Thumb(Field):

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
                           "postcode": validators.String(not_empty = True)
                          }

class RequireIfMissing(Field):

    extra_kw = ["field", "missing"]

    def __init__(self, name, *args, **kw):

        field = kw.get("field")
        missing = kw.get("missing")

        self.chained_validator = validators.RequireIfMissing(field, missing = missing)


class CheckOverLappingDates(Field):

    extra_kw = ["parent_table"]

    def __init__(self, name, *args, **kw):

        parent_table = kw.get("parent_table")
        self.chained_validator = validators.CheckNoOverlappingDates(parent_table)


class CheckNoTwoNulls(Field):

    extra_kw = ["parent_table", "field"]

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

class Email(Field):

    def __init__(self, name, *args, **kw):
        self.email = Column(sa.Unicode(300), use_parent = True)
        self.validation = {name : validators.Email()}


class Date(Field):

    def __init__(self, name, *args, **kw):
        self.date = Column(sa.Date, use_parent = True)


class ManyToOne(Field):

    def __init__(self, name, other, *args, **kw):
        self.other = other
        self.manytoone = Relation("manytoone", other, use_parent = True)

class ForeignKey(Field):

    extra_kw = ["onetoone"]

    def __init__(self, name, other, *args, **kw):

        if name.endswith("_id"):
            relation_name = name[:-3]
            self.relation_name = relation_name
        else:
            relation_name = name

        join = "onetoone" if kw.get("onetoone") else "manytoone"

        backref = kw.get("backref", "_?_%s" % relation_name)

        self.integer = Column(sa.Integer, use_parent = True)

        self.manytoone = Relation(join, other,
                                  backref = backref, use_parent = True,
                                  foreign_key_name = name)



class LookupId(Field):

    extra_kw = ["filter_field", "filter_field",
                "filter_value","backref"]

    def __init__(self, name, other = None, *args, **kw):

        self.data_type = "Integer"

        if not other:
            other = name

        self.filter_field = kw.get("filter_field")
        self.filter_value = kw.get("filter_value", name)

        backref = kw.get("backref", "_?_%s" % name)

        self.integer = Column(sa.Integer, use_parent = True)

        self.manytoone = Relation("manytoone", other, 
                                  foreign_key_name = name, 
                                  backref = backref, use_parent = True)

        self.validation = {name: validators.CheckInField("%s.id" % other,
                                                   filter_field = self.filter_field,
                                                   filter_value = self.filter_value )}

class LookupList(Field):

    extra_kw = ["lookup_list"]

    def __init__(self, name, lookup, *args, **kw):

        self.data_type = "Text"
        if "lookup_list" in kw:
            self.lookup_list = kw["lookup_list"].split(",")

        self.text = Column(sa.Unicode(100), use_parent = True)

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
        self.onetoone = Relation("onetooneother", other, use_parent = True)


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

