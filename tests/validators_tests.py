from database.fields import *
from database.tables import *
from database.database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
import database.validators as val
from tests.donkey_test import test_donkey
from database.data_loader import SingleRecord
from sqlalchemy import create_engine
from database.util import get_table_from_instance, create_data_dict, make_local_tables, get_all_local_data, load_local_data
import datetime
from decimal import Decimal
import formencode as fe
import yaml
import os
import logging

class test_validation(test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, test_validation).set_up_inserts()

        load_local_data(cls.Donkey, {"__table": u"sub_sub_category",
                                      "category.category_name": u"a",
                                      "category.category_description": u"this is a",
                                      "category.category_type": u"wee",
                                      "sub_category.sub_category_name": u"ab",
                                      "sub_category.sub_category_description": u"this is ab",
                                      "sub_sub_category.sub_sub_category_name": u"abc",
                                      "sub_sub_category.sub_sub_category_description": u"this is abc"}
                       )

    def test_schema_dict(self):

        print self.Donkey.tables["email"].schema_info
        assert self.Donkey.tables["email"].schema_info == {'active_email': [{'not_empty': False, 'type': 'Bool'}], '_version': [{'not_empty': False, 'type': 'Int'}], '_modified_by': [{'not_empty': False, 'type': 'Int'}], '_modified_date': [{'not_empty': False, 'type': 'DateValidator'}], 'people_id': [{'not_empty': False, 'type': 'Int'}], 'email_number': [], 'email': [{'max': 300, 'not_empty_string': False, 'type': 'UnicodeString', 'not_empty': False}, {'type': 'Email'}]}


    def test_address_validation(self):

        assert len(get_table_from_instance(self.david, self.Donkey).validate(self.david, None)) > 3

        assert_raises(formencode.Invalid,
                      get_table_from_instance(self.david2, self.Donkey).validate,self.david2, None)

    def test_regex_validation(self):

        poo = self.Donkey.tables["donkey"].sa_class()
        poo.name = "don_keyfasf"
        assert_raises(formencode.Invalid,self.session.add, poo)

    def test_many_side_mandatory_validation(self):


        assert_raises(
            fe.Invalid,
            load_local_data,
            self.Donkey,
            {"__table": u"category",
            "category.category_name": u"z",
            "category.category_description": u"this is a",
            "category.category_type": u"wee",
            }
        )

        try:
            load_local_data(self.Donkey,
                            {"__table": u"category",
                            "category.category_name": u"z",
                            "category.category_description": u"this is a",
                            "category.category_type": u"wee",
                            })
        except fe.Invalid, e:
            assert e.msg.strip() == "sub_category: Please enter a value"

    def test_zzzz_overlapping_date_validation(self):

        entity = self.session.query(self.Donkey["_core_entity"]).first()
        category = self.session.query(self.Donkey.aliases["sub_sub_category"]).first()

        cat1 = self.Donkey.get_instance("entity_categories")
        cat1.start_date = datetime.datetime(2009,04,02)
        cat1.end_date = datetime.datetime(2009,04,03)
        cat1.category = category

        cat2 = self.Donkey.get_instance("entity_categories")
        cat2.start_date = datetime.datetime(2009,04,02)
        cat2.end_date = datetime.datetime(2009,04,03)
        cat2.category = category

        entity.categories.append(cat1)
        entity.categories.append(cat2)

        self.session.save(entity)

        assert_raises(
            fe.Invalid,
            self.session.save,
            cat1)

        cat2.start_date = datetime.datetime(2009,05,02)
        cat2.end_date = datetime.datetime(2009,05,03)

        assert self.session.save(cat1) is None
        self.session.expunge_all()


    def test_zzzzz_two_nulls_validation(self):

        entity = self.session.query(self.Donkey.aliases["_core_entity"]).first()
        membership1 = self.Donkey.get_instance("membership")
        membership1.start_date = datetime.datetime(2009,05,02)
        membership1._core_entity = entity
        self.session.add(membership1)
        self.session.add(entity)
        self.session.commit()

        membership2 = self.Donkey.get_instance("membership")
        membership2.start_date = datetime.datetime(2009,05,02)
        membership2._core_entity = entity
        assert_raises(formencode.Invalid, self.session.add, membership2)

        membership2.end_date = datetime.datetime(2009,05,02)

        assert self.session.add(membership2) == None


    def test_lookup_validation(self):

        load_local_data(self.Donkey,
                        {"__table": u"donkey",
                        "donkey.name": u"good",
                        "donkey.donkey_type": u"smooth",
                        })


        assert_raises(formencode.Invalid,
                      load_local_data,
                      self.Donkey,
                      {"__table": u"donkey",
                      "donkey.name": u"z",
                      "donkey.donkey_type": u"pooey",
                      })

    def test_uniclode(self):

        string_val = val.UnicodeString(not_empty = True)

        assert_raises(fe.Invalid, string_val.to_python, None)

        string_val.to_python(u"")







