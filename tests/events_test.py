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

    def test_add_action(self):

        transaction = self.Donkey.get_instance("transactions")

        first = self.session.query(self.Donkey.t.people).first()

        transaction.amount = 10
        transaction._people = first
        self.session.save(transaction)
        self.session.save(first)
        self.session.commit()

        assert first.contact_summary.total_amount == 10
       # assert first.contact_summary.transaction_count == 1

        first = self.session.query(self.Donkey.t.people).first()

        transaction2 = self.Donkey.get_instance("transactions")
        transaction2.amount = 10
        transaction2._people = first
        self.session.save(transaction2)
        self.session.save(first)
        self.session.commit()

        assert first.contact_summary.total_amount == 20 
        assert first.contact_summary.transaction_count == 2

        transaction3 = self.Donkey.get_instance("transactions")
        transaction3.amount = 20
        transaction3._people = first
        self.session.save(transaction3)
        self.session.save(first)
        self.session.commit()

        assert first.contact_summary.total_amount == 40 
        assert first.contact_summary.transaction_count == 3

        self.session.delete(transaction2)
        self.session.commit()
        assert first.contact_summary.total_amount == 30
        assert first.contact_summary.transaction_count == 2

        transaction.amount  = 15
        self.session.save(transaction)
        self.session.commit()
        assert first.contact_summary.total_amount == 35
        assert first.contact_summary.transaction_count == 2

        first.contact_summary.total_amount = 0

        self.session.save(first.contact_summary)
        self.session.commit()

        assert first.contact_summary.total_amount == 0

        self.Donkey.tables["transactions"].events[0].update_all(self.session)
        self.session.commit()

        assert first.contact_summary.total_amount == 35

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

        assert new_person.contact_summary.total_amount == 20

        first.contact_summary.total_amount = 0
        new_person.contact_summary.total_amount = 0

        self.session.save(first.contact_summary)
        self.session.save(new_person.contact_summary)

        self.session.commit()

        self.Donkey.tables["transactions"].events[0].update_all(self.session)

        self.session.commit()

        assert first.contact_summary.total_amount == 35
        assert new_person.contact_summary.total_amount == 20



    def test_maxdate_action(self):

        person = self.session.query(self.Donkey.t.people).first()
        entity = person._entity
        membership1 = self.Donkey.get_instance("membership")
        membership1.start_date = datetime.datetime(2009,05,02)
        membership1.end_date = datetime.datetime(2013,06,02)
        membership1._core_entity = entity
        self.session.add(membership1)
        self.session.add(entity)
        self.session.commit()

        assert entity.people.contact_summary.membership == datetime.datetime(2013,06,02)

        person2 = self.session.query(self.Donkey.t.people).first()
        entity2 = person._entity
        membership2 = self.Donkey.get_instance("membership")
        membership2.start_date = datetime.datetime(2009,05,02)
        membership2.end_date = datetime.datetime(2013,07,02)
        membership2._core_entity = entity
        self.session.add(membership2)
        self.session.add(entity2)
        self.session.commit()

        assert entity.people.contact_summary.membership == datetime.datetime(2013,07,02) 

        person3 = self.session.query(self.Donkey.t.people).first()
        entity3 = person._entity
        membership3 = self.Donkey.get_instance("membership")
        membership3.start_date = datetime.datetime(2009,05,02)
        membership3._core_entity = entity
        self.session.add(membership3)
        self.session.add(entity3)
        self.session.commit()

        assert entity.people.contact_summary.membership == datetime.datetime(2199,12,31) 

        self.session.delete(membership3)
        self.session.commit()

        assert entity.people.contact_summary.membership == datetime.datetime(2013,07,02)

        self.session.delete(membership2)
        self.session.commit()

        assert entity.people.contact_summary.membership == datetime.datetime(2013,06,02)

        person4 = self.session.query(self.Donkey.t.people).first()
        entity4 = person._entity
        membership4 = self.Donkey.get_instance("membership")
        membership4.start_date = datetime.datetime(2010,05,02)
        membership4.end_date = datetime.datetime(2010,05,02)
        membership4._core_entity = entity
        self.session.add(membership4)
        self.session.add(entity4)
        self.session.commit()

        assert entity.people.contact_summary.membership == datetime.datetime(2013,06,02) 
        
        self.session.delete(membership4)
        self.session.delete(membership1)
        self.session.commit()

        assert entity.people.contact_summary.membership is None

    def test_copy_text(self):

        person = self.session.query(self.Donkey.t.people).first()

        assert person.contact_summary.address == "43 union street es388"

        email = self.Donkey.get_instance("email")
        email.email = u"poo@poo.com"
        email._people = person

        self.session.add(person)
        self.session.add(email)
        self.session.commit()


        assert person.contact_summary.email == u"poo@poo.com poo@poo.com"
        print email.email_number
        assert email.email_number == 1

        email2 = self.Donkey.get_instance("email")
        email2.email = u"zpoo@poo.com"
        email2.active_email = False
        email2._people = person

        self.session.add(person)
        self.session.add(email2)
        self.session.commit()

        assert email2.email_number == 2


        assert person.contact_summary.email == u"poo@poo.com poo@poo.com zpoo@poo.com zpoo@poo.com"
        

        person.contact_summary.modified = False
        self.session.save(person.contact_summary)
        self.session.commit()

        assert person.contact_summary.modified == False

        person.postcode = u"es399"

        self.session.save(person)
        self.session.commit()

        assert person.contact_summary.modified == True
        

    def test_z_recreate_all(self):

        self.Donkey.tables["contact_summary"].update_all_initial_events()

        all_people = self.session.query(self.Donkey.t.people).all()

        all_summary = self.session.query(self.Donkey.t.contact_summary).all()

        self.session.expire_all()

        assert len(all_summary) == len(all_people)
        assert all([person.contact_summary.total_amount == 0 for person in all_people])

        self.Donkey.tables["contact_summary"].update_all_events()

        self.session.expire_all()

        person = self.session.query(self.Donkey.t.people).first()

        assert person.contact_summary.total_amount == 35
        assert person.contact_summary.address == "43 union street es399"
        assert person.contact_summary.membership is None

        print person.contact_summary.email

        assert person.contact_summary.email == u"poo@poo.com poo@poo.com zpoo@poo.com zpoo@poo.com"
        assert person.contact_summary.modified == True
        
        email = self.Donkey.get_instance("email")
        email.email = u"zzpoo@poo.com"
        email._people = person

        self.session.add(person)
        self.session.add(email)
        self.session.commit()

        assert person.contact_summary.email == u"poo@poo.com poo@poo.com zpoo@poo.com zpoo@poo.com zzpoo@poo.com zzpoo@poo.com"

        self.Donkey.tables["contact_summary"].update_all_events()
        self.session.expire_all()

        assert person.contact_summary.email == u"poo@poo.com poo@poo.com zpoo@poo.com zpoo@poo.com zzpoo@poo.com zzpoo@poo.com"
