from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from tests.donkey_test import test_donkey
from nose.tools import assert_raises,raises
import sqlalchemy as sa
import reformed.custom_exceptions
from reformed.data_loader import SingleRecord
from sqlalchemy import create_engine
from reformed.util import get_table_from_instance, create_data_dict, make_local_tables, get_all_local_data, load_local_data
import datetime
from decimal import Decimal
import formencode as fe
import yaml
import os
import logging

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.debug)
sqllogger.addHandler(sqlhandler)

class test_events(test_donkey):

#    @classmethod
#    def setUpClass(cls):
#        super(test_events, cls).setUpClass()
#        cls.Donkey.tables["contact_summary"].add_field(CopyText("categories", "entity_categories", 
#                                                base_level = "people", 
#                                                fields = "category.category_description,sub_category.sub_category_description,sub_sub_category.sub_sub_category_description",
#                                                counter = "category_number"
#                                                ))
#
#        load_local_data(cls.Donkey, {"__table": u"sub_sub_category",
#                                      "category.category_name": u"a",
#                                      "category.category_description": u"this is a",
#                                      "category.category_type": u"wee",
#                                      "sub_category.sub_category_name": u"ab",
#                                      "sub_category.sub_category_description": u"this is ab",
#                                      "sub_sub_category.sub_sub_category_name": u"abc",
#                                      "sub_sub_category.sub_sub_category_description": u"this is abc"}
#                       )
#
#        load_local_data(cls.Donkey, {"__table": u"sub_sub_category",
#                                      "category.category_name": u"aa",
#                                      "category.category_description": u"this is aa",
#                                      "category.category_type": u"wee",
#                                      "sub_category.sub_category_name": u"aab",
#                                      "sub_category.sub_category_description": u"this is aab",
#                                      "sub_sub_category.sub_sub_category_name": u"aabc",
#                                      "sub_sub_category.sub_sub_category_description": u"this is aabc"}
#                       )

    def test_add_action(self):

        transaction = self.Donkey.get_instance("transactions")

        first = self.session.query(self.Donkey["people"]).first()

        transaction.amount = 10
        transaction._people = first
        self.session.save(transaction)
        self.session.save(first)
        self.session.commit()

        assert first._rel_summary.total_amount == 10
       # assert first.contact_summary.transaction_count == 1

        first = self.session.query(self.Donkey["people"]).first()

        transaction2 = self.Donkey.get_instance("transactions")
        transaction2.amount = 10
        transaction2._people = first
        self.session.save(transaction2)
        self.session.save(first)
        self.session.commit()

        assert first._rel_summary.total_amount == 20 
        assert first._rel_summary.transaction_count == 2

        transaction3 = self.Donkey.get_instance("transactions")
        transaction3.amount = 20
        transaction3._people = first
        self.session.save(transaction3)
        self.session.save(first)
        self.session.commit()

        assert first._rel_summary.total_amount == 40 
        assert first._rel_summary.transaction_count == 3

        self.session.delete(transaction2)
        self.session.commit()
        print first._rel_summary.total_amount
        assert first._rel_summary.total_amount == 30
        assert first._rel_summary.transaction_count == 2

        transaction.amount  = 15
        self.session.save(transaction)
        self.session.commit()
        assert first._rel_summary.total_amount == 35
        assert first._rel_summary.transaction_count == 2

        first._rel_summary.total_amount = 0

        self.session.save(first._rel_summary)
        self.session.commit()

        assert first._rel_summary.total_amount == 0


        new_person = self.Donkey.get_instance("people")
        new_person.postcode = u"esjlkj"
        new_person.name = u"esjlkj"
        new_person.address_line_1 = u"fdsdf"
        self.session.save(new_person)
        self.session.commit()


        transaction_new = self.Donkey.get_instance("transactions")
        transaction_new.amount = 20
        transaction_new._people = new_person

        self.session.save(transaction_new)
        self.session.save(new_person)
        self.session.commit()

        assert new_person._rel_summary.total_amount == 20

        #first.contact_summary.total_amount = 0
        #new_person.contact_summary.total_amount = 0

        #self.session.save(first.contact_summary)
        #self.session.save(new_person.contact_summary)

        #self.session.commit()

        #self.Donkey.tables["transactions"].events[0].update_all(self.session)

        #self.session.commit()

        #assert first.contact_summary.total_amount == 35
        #assert new_person.contact_summary.total_amount == 20



#    def test_maxdate_action(self):
#
#        person = self.session.query(self.Donkey.aliases["people"]).first()
#        entity = person._entity
#        membership1 = self.Donkey.get_instance("membership")
#        membership1.start_date = datetime.datetime(2009,05,02)
#        membership1.end_date = datetime.datetime(2013,06,02)
#        membership1._core_entity = entity
#        self.session.add(membership1)
#        self.session.add(entity)
#        self.session.commit()
#
#        print entity.people.contact_summary.membership
#        assert entity.people.contact_summary.membership == datetime.datetime(2013,06,02)
#
#        person2 = self.session.query(self.Donkey.aliases["people"]).first()
#        entity2 = person._entity
#        membership2 = self.Donkey.get_instance("membership")
#        membership2.start_date = datetime.datetime(2009,05,02)
#        membership2.end_date = datetime.datetime(2013,07,02)
#        membership2._core_entity = entity
#        self.session.add(membership2)
#        self.session.add(entity2)
#        self.session.commit()
#
#        assert entity.people.contact_summary.membership == datetime.datetime(2013,07,02) 
#
#        person3 = self.session.query(self.Donkey.aliases["people"]).first()
#        entity3 = person._entity
#        membership3 = self.Donkey.get_instance("membership")
#        membership3.start_date = datetime.datetime(2009,05,02)
#        membership3._core_entity = entity
#        self.session.add(membership3)
#        self.session.add(entity3)
#        self.session.commit()
#
#        assert entity.people.contact_summary.membership == datetime.datetime(2199,12,31) 
#
#        self.session.delete(membership3)
#        self.session.commit()
#
#        assert entity.people.contact_summary.membership == datetime.datetime(2013,07,02)
#
#        self.session.delete(membership2)
#        self.session.commit()
#
#        assert entity.people.contact_summary.membership == datetime.datetime(2013,06,02)
#
#        person4 = self.session.query(self.Donkey.aliases["people"]).first()
#        entity4 = person._entity
#        membership4 = self.Donkey.get_instance("membership")
#        membership4.start_date = datetime.datetime(2010,05,02)
#        membership4.end_date = datetime.datetime(2010,05,02)
#        membership4._core_entity = entity
#        self.session.add(membership4)
#        self.session.add(entity4)
#        self.session.commit()
#
#        assert entity.people.contact_summary.membership == datetime.datetime(2013,06,02) 
#        
#        self.session.delete(membership4)
#        self.session.delete(membership1)
#        self.session.commit()
#
#        assert entity.people.contact_summary.membership is None
#
#    def test_copy_text(self):
#
#        person = self.session.query(self.Donkey.aliases["people"]).first()
#
#        assert person.contact_summary.address == "43 union street es388"
#
#        email = self.Donkey.get_instance("email")
#        email.email = u"poo@poo.com"
#        email._people = person
#
#        self.session.add(person)
#        self.session.add(email)
#        self.session.commit()
#
#
#        assert person.contact_summary.email == u"poo@poo.com poo@poo.com"
#        print email.email_number
#        assert email.email_number == 1
#
#        email2 = self.Donkey.get_instance("email")
#        email2.email = u"zpoo@poo.com"
#        email2.active_email = False
#        email2._people = person
#
#        self.session.add(person)
#        self.session.add(email2)
#        self.session.commit()
#
#        assert email2.email_number == 2
#
#
#        assert person.contact_summary.email == u"poo@poo.com poo@poo.com zpoo@poo.com zpoo@poo.com"
#        
#
#        person.contact_summary.modified = False
#        self.session.save(person.contact_summary)
#        self.session.commit()
#
#        assert person.contact_summary.modified == False
#
#        person.postcode = u"es399"
#
#        self.session.save(person)
#        self.session.commit()
#
#        assert person.contact_summary.modified == True
#
#    def test_add_category(self):
#
#        person = self.session.query(self.Donkey.aliases["people"]).first()
#        subsub_category = self.session.query(self.Donkey.aliases["sub_sub_category"]).first()
#
#        entity_categories = self.Donkey.get_instance("entity_categories")
#        entity_categories.category = subsub_category
#        entity_categories.entity = person._entity
#        entity_categories.start_date = datetime.datetime(2001,10,01)
#        entity_categories.end_date = datetime.datetime(2002,10,01)
#
#        self.session.save(entity_categories)
#        self.session.save(person._entity)
#        self.session.save(subsub_category)
#        self.session.save(person)
#
#        self.session.commit()
#
#        assert entity_categories.category_number == 1
#
#        print person.contact_summary
#        print person.contact_summary.categories
#        assert person.contact_summary.categories == "this is a this is ab this is abc"
#
#
#        subsub_category = self.session.query(self.Donkey.aliases["sub_sub_category"])[1]
#
#        entity_categories = self.Donkey.get_instance("entity_categories")
#        entity_categories.category = subsub_category
#        entity_categories.start_date = datetime.datetime(2012,10,01)
#        entity_categories.end_date = datetime.datetime(2013,10,01)
#        entity_categories.entity = person._entity
#
#        self.session.save(entity_categories)
#        self.session.save(person._entity)
#        self.session.save(subsub_category)
#        self.session.save(person)
#
#        self.session.commit()
#
#        assert entity_categories.category_number == 2
#
#        print person.contact_summary.categories 
#
#        assert person.contact_summary.categories == "this is a this is ab this is abc this is aa this is aab this is aabc"
#        
#
#
#        
#
#    def test_z_recreate_all(self):
#
#        self.Donkey.tables["contact_summary"].update_all_initial_events()
#
#        all_people = self.session.query(self.Donkey.aliases["people"]).all()
#
#        all_summary = self.session.query(self.Donkey.aliases["contact_summary"]).all()
#
#        self.session.expire_all()
#
#        assert len(all_summary) == len(all_people)
#        assert all([person.contact_summary.total_amount == 0 for person in all_people])
#        person = self.session.query(self.Donkey.aliases["people"]).first()
#
#        assert person.contact_summary.categories is None
#
#        self.Donkey.tables["contact_summary"].update_all_events()
#
#        self.session.expire_all()
#
#        person = self.session.query(self.Donkey.aliases["people"]).first()
#
#        assert person.contact_summary.categories == "this is a this is ab this is abc this is aabc this is aab this is aa"
#        assert person.contact_summary.total_amount == 35
#        assert person.contact_summary.address == "43 union street es399"
#        assert person.contact_summary.membership is None
#
#        print person.contact_summary.categories
#        print person.contact_summary.email
#
#        assert person.contact_summary.email == u"poo@poo.com poo@poo.com zpoo@poo.com zpoo@poo.com"
#        assert person.contact_summary.modified == True
#        
#        email = self.Donkey.get_instance("email")
#        email.email = u"zzpoo@poo.com"
#        email._people = person
#
#        self.session.add(person)
#        self.session.add(email)
#        self.session.commit()
#
#        assert person.contact_summary.email == u"poo@poo.com poo@poo.com zpoo@poo.com zpoo@poo.com zzpoo@poo.com zzpoo@poo.com"
#
#        self.Donkey.tables["contact_summary"].update_all_events()
#        self.session.expire_all()
#
#        assert person.contact_summary.email == u"poo@poo.com poo@poo.com zpoo@poo.com zpoo@poo.com zzpoo@poo.com zzpoo@poo.com"
#
#    def test_entity_title_summary(self):
#
#
#        person = self.session.query(self.Donkey.aliases["people"]).first()
#
#        assert person.name == person._entity.title
#
#        assert person._entity.summary == "name: david -- address_line_1: 43 union street -- postcode: es399"
#
#        donkey = self.session.query(self.Donkey.aliases["donkey"]).first()
#
#        print donkey._entity.title
#        print donkey.name
#        assert donkey.name == donkey._entity.title
#
#        print donkey._entity.summary
#        assert donkey._entity.summary == "name: jim -- age: 13"
#
#    def zz_delete_entity_test(self):
#    
#        donkey = self.Donkey.get_instance("donkey")
#        donkey.name = u"fresddy"
#        self.session.save(donkey)
#        self.session.commit()
#
#        entity_id = donkey._entity.id 
#
#        self.session.delete(donkey) 
#
#        self.session.commit()
#
#        assert_raises(custom_exceptions.SingleResultError,
#                      self.Donkey.search_single,
#                      "_core_entity",
#                      "id = ?",
#                      values = [entity_id])
#
#        person = self.session.query(self.Donkey.aliases["people"]).first()
#
#        self.session.delete(person)
#
#        assert_raises(custom_exceptions.DependencyError,self.session.commit)







