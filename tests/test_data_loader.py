import donkey_test
from reformed.data_loader import SingleRecord 

import yaml

class donkey_test(donkey_test.test_donkey):

    @classmethod
    def set_up_inserts(cls):
        peter ="""
        name : peter
        address_line1 : 16 blooey
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

        cls.new_record = SingleRecord(cls.Donkey, "people", peter)        
        
        #load(cls.Donkey, "people", peter)
        cls.session = cls.Donkey.Session()

    def test_single_record_process(self):
        
        print self.new_record.all_fields
        assert ("donkey_sponsership", 0, "_donkey", 0, "name") in self.new_record.all_fields.keys()
        assert self.new_record.all_fields[("donkey_sponsership", 0, "_donkey", 0, "name")] == "fred"
        assert self.new_record.all_fields[("email" , 1, "email")] == "poo2@poo.com"

        print self.new_record.all_obj
        assert ("donkey_sponsership", 0, "_donkey", 0) in self.new_record.all_obj.keys()
        assert self.new_record.all_obj[("donkey_sponsership", 0, "_donkey", 0)] == dict(name = "fred", age =10) 
        assert self.new_record.all_obj[("email" , 1)] == dict(email = "poo2@poo.com")

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




