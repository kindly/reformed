from tests.donkey_test import test_donkey
from database.export import *
from database.data_loader import *


class test_export_database(test_donkey):


    def test_single_object(self):

        session = self.Donkey.Session()

        person = session.query(self.Donkey.get_class("people")).first()

        print SingleObject(person, self.Donkey).data 
        assert SingleObject(person, self.Donkey).data == {'donkey_sponsership': [{'_donkey': [{'age': '13', 'name': 'jim', '_version': '1'}], 'amount': '50', '_version': '1'}], 'address_line_1': '43 union street', 'postcode': 'es388', 'name': 'david', '_version': '1'}

        assert SingleRecord(self.Donkey, "people", SingleObject(person, self.Donkey).data).load() == None


    def test_z_multi_line(self):

        session = self.Donkey.Session()
        countpeople = session.query(self.Donkey.get_class("people")).count()
        countspone = session.query(self.Donkey.get_class("donkey_sponsership")).count()

        people = session.query(self.Donkey.get_class("people")).all()

        all_rows = multi_row_export(people, self.Donkey)

        print all_rows

        for line in all_rows:
            SingleRecord(self.Donkey, "people", line).load() 

        countpeopleafter = session.query(self.Donkey.get_class("people")).count()
        countsponeafter = session.query(self.Donkey.get_class("donkey_sponsership")).count()

        assert countpeople*2 == countpeopleafter
        assert countspone*2 == countsponeafter


    def test_zz_json_dump(self):

        session = self.Donkey.Session()
        countpeople = session.query(self.Donkey.get_class("people")).count()
        countspone = session.query(self.Donkey.get_class("donkey_sponsership")).count()

        json_dump_all_from_table(session, "people", self.Donkey, "tests/json_dump.json")

        load_json_from_file("tests/json_dump.json", self.Donkey, "people")

        countpeopleafter = session.query(self.Donkey.get_class("people")).count()
        countsponeafter = session.query(self.Donkey.get_class("donkey_sponsership")).count()

        assert countpeople*2 == countpeopleafter
        assert countspone*2 == countsponeafter











        

        




