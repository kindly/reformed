from reformed.fields import *
import formencode
from formencode import validators
from nose.tools import assert_raises

class test_fields():
    
    def setUp(self):
        
        self.a = Text("col")
        self.b = Text("pop" , 
                      mandatory = True, 
                      default = "pop" ,
                      onupdate = "pop") 
        
        self.c = ManyToOne("many","table2")

        self.d = Text("pop" , 
                      mandatory = True, 
                      default = "pop" ,
                      onupdate = "pop")

        self.e = Text("pop" , 
                      mandatory = True, 
                      onupdate = "pop")

        self.f = Text("pop" , 
                      mandatory = False, 
                      onupdate = "pop")
            
    def test_text_field_fieldname(self):
        
        assert self.a.columns["col"].name == "col"
        
    def test_many_to_one(self):
    
        assert self.c.relations["many"].name == "many"

    def test_use_parent(self):

        assert ("nullable", False) in self.b.columns["pop"].sa_options.items()
        assert ("default", "pop") in self.b.columns["pop"].sa_options.items()
        assert ("onupdate", "pop") in self.b.columns["pop"].sa_options.items()

    def test_eq(self):

        assert self.a <> self.b

        assert self.b == self.d

    def test_diff(self):

        print self.b.diff(self.e)

        assert self.b.diff(self.e) == ({'default': 'pop'}, {}, {})
        assert self.e.diff(self.b) == ({}, {'default': 'pop'}, {})

        assert self.f.diff(self.e) == ({}, {}, {'mandatory': [True, False]})
        assert self.e.diff(self.f) == ({}, {}, {'mandatory': [False, True]})

        assert self.f.diff(self.b) == ({}, {'default': 'pop'}, {'mandatory': [True, False]})

        
class test_validation(object):
    
    def setUp(self):

        self.email = Email("email")
        self.address = Address("address") 
        
        kwemail = self.email.validation
        self.email_val_schema = formencode.Schema(**kwemail)

        kwaddress = self.address.validation
        self.address_val_schema = formencode.Schema(allow_extra_fields =True,
                                                    **kwaddress
                                                    )
        

    def test_email_validation(self):

        assert self.email_val_schema.to_python(
                                          {"email" :"kindly@gmail.com"}) ==\
                                          {"email" :"kindly@gmail.com"}
        assert_raises(formencode.Invalid, self.email_val_schema.to_python,
                                          {"email" :"kindlygmail.com"}) 

    def test_multi_evaluation(self):

        assert self.address_val_schema.to_python(
                                          {"address_line_1": "56 moreland",
                                           "address_line_2": "essex",
                                           "postcode" : "IG5 0dp"})==\
                                          {"address_line_1": "56 moreland",
                                           "address_line_2": "essex",
                                           "postcode" : "IG5 0dp"}

        assert_raises(formencode.Invalid, self.address_val_schema.to_python,
                                          {"address_line_1": "",
                                           "address_line_2": "essex",
                                           "postcode" : "IG5 0dp"})

         



 
