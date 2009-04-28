import donkey_test
from reformed.data_loader import *
from nose.tools import assert_raises,raises
from reformed.custom_exceptions import *
import yaml

class donkey_test(donkey_test.test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, donkey_test).set_up_inserts()
        
        david ="""
        id : 1
        address_line_1 : 16 blooey
        postcode : sewjfd
        email :
            -
                email : poo@poo.com
            -
                email : poo2@poo.com
        donkey_sponsership:
            id : 1
            amount : 10
            _donkey : 
                name : fred
                age : 10
        """

        david = yaml.load(david)

        peter ="""
        name : peter
        address_line_1 : 16 blooey
        postcode : sewjfd
        email :
            -
                email : poo@poo.com
            -
                email : poo2@poo.com
        donkey_sponsership:
            amount : 10
            _donkey : 
                name : fred
                age : 10
        """

        peter = yaml.load(peter)

        cls.existing_record = SingleRecord(cls.Donkey, "people", david)
        cls.new_record = SingleRecord(cls.Donkey, "people", peter)        
        cls.existing_record.get_root_obj()
        cls.new_record.get_root_obj()

        cls.existing_record.get_obj(("email" , 0))
        cls.existing_record.get_obj(("donkey_sponsership" , 0))
        cls.existing_record.get_obj(("donkey_sponsership" , 0, "_donkey", 0))

        cls.new_record.get_obj(("email" , 0))
        cls.new_record.get_obj(("donkey_sponsership" , 0))
        cls.new_record.get_obj(("donkey_sponsership" , 0, "_donkey", 0))
        
        #cls.new_record.load()
        cls.session = cls.Donkey.Session()

    def test_single_record_process(self):
        
        assert ("donkey_sponsership", 0, "_donkey", 0) in self.new_record.all_rows.keys()
        assert self.new_record.all_rows[("donkey_sponsership", 0, "_donkey", 0)] == dict(name = "fred", age =10) 
        assert self.new_record.all_rows[("email" , 1)] == dict(email = "poo2@poo.com")

    def test_get_key_data(self):

        assert get_key_data(("donkey_sponsership", 0, "_donkey", 0), self.Donkey , "people") == ["donkey", "manytoone"]

        assert_raises(InvalidKey, get_key_data, 
                     ("donkey_sponsership", 0, "donkey", 0), self.Donkey , "people")

    def test_get_parent_key(self):

        assert_raises(InvalidKey, 
                      get_parent_key,
                      ("donkey_sponsership", 1, "donkey", 5),
                      self.new_record.all_rows)

        assert get_parent_key(("donkey_sponsership", 0, "donkey", 0),
                                             self.new_record.all_rows) == ("donkey_sponsership", 0)

        assert get_parent_key(("donkey", 0),
                                             self.new_record.all_rows) == "root" 

    def test_check_correct_fields(self):

        assert_raises(InvalidField, check_correct_fields, {"name":  "peter", "name2": "bob"}, self.Donkey, "people")

        assert check_correct_fields( {"name":  "peter", "postcode" : "bob"}, self.Donkey, "people") is None

        assert check_correct_fields( {"name":  "peter", "__options" : "bob"}, self.Donkey, "people") is None

        assert check_correct_fields( {"name":  "peter", "id" : "bob"}, self.Donkey, "people") is None

    def test_get_root_obj(self):

        assert self.new_record.all_obj["root"].id is None

        assert self.existing_record.all_obj["root"].name == u"david"

    def test_get_obj_with_id(self):

        obj = self.existing_record.get_obj_with_id( ("donkey_sponsership", 0) , dict(id = 1, amount = 20))

        assert obj.amount == 50   #originally 50

        assert_raises(InvalidData, self.existing_record.get_obj_with_id, ("donkey_sponsership", 0) , dict(id = 2, amount = 20))

        assert_raises(InvalidData, self.existing_record.get_obj_with_id, ("email", 0) , dict(id = 1))

    def test_get_obj_existing_one_to_many(self):

        assert self.existing_record.all_obj[("donkey_sponsership" , 0)].amount == 50

    def test_get_obj_new_one_to_many(self):

        assert self.existing_record.all_obj[("email" , 0)].email is None

    def test_get_obj_new_many_to_one(self):
        
        assert self.new_record.all_obj[("donkey_sponsership" , 0, "_donkey", 0)].age is None

    def test_get_obj_existing_many_to_one(self):
        
        assert self.existing_record.all_obj[("donkey_sponsership" , 0, "_donkey", 0)].age == 13

    def test_get_obj_new_from_key(self):
        
        pass





    def tstlater_load_record(self):

        people = self.session.query(self.Donkey.get_class("people")).all()
        email = self.session.query(self.Donkey.get_class("email")).all()
        donkey = self.session.query(self.Donkey.get_class("donkey")).all()
        donkey_spon = self.session.query(self.Donkey.get_class("donkey_sponsership")).all()
        

        assert (u"peter", u"sewjfd") in [( a.name, a.postcode) for a in 
                                         people]
        assert (u"fred", 10 ) in [( a.name, a.age) for a in 
                                         donkey]
        assert u"poo@poo.com" in [ a.email for a in 
                                         email]
        assert  10  in [ a.amount for a in 
                                         donkey_spon]

