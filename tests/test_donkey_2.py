from reformed.data_loader import FlatFile 
from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
import reformed.custom_exceptions
from reformed.data_loader import SingleRecord
from sqlalchemy import create_engine
from reformed.util import get_table_from_instance, create_data_dict, make_local_tables, get_all_local_data, load_local_data
import datetime
import yaml
from decimal import Decimal
import formencode as fe
import yaml
import os
import logging

class test_donkey_search(object):

    @classmethod
    def setUpClass(cls):
        if not hasattr(cls, "engine"):
            cls.engine = create_engine('sqlite:///:memory:', echo = True )
            #cls.engine = create_engine('sqlite:///:memory:')
        
#        cls.engine = create_engine('mysql://localhost/test_donkey', echo = True)
        cls.meta = sa.MetaData()
        cls.Sess = sa.orm.sessionmaker(bind =cls.engine, autoflush = False)
        cls.donkey = Database("donkey", 
                            Table("people",
                                  Text("name", mandatory = True, length = 30),
                                  Address("supporter_address"),
                                  DateTime("dob"),
                                  Boolean("active"),
                                  OneToMany("email","email"),
                                 ),
                            Table("email",
                                  Email("email"),
                                  Counter("email_number", base_level = "people"),
                                  Boolean("default_email", default = True)
                                 ),
                        metadata = cls.meta,
                        engine = cls.engine,
                        session = cls.Sess,
                        entity = True
                        )

        cls.donkey.persist()
        cls.session = cls.donkey.Session()

        david ="""
        id : 1
        address_line_1 : 16 blooey
        postcode : sewjfd
        email :
            -
                default_email : true
                email : poo@poo.com
            -
                email : poo2@poo.com
                default_email : false
        """


    @classmethod
    def tearDownClass(cls):

        cls.session.close()
        cls.donkey.status = "terminated"

    
    def test_basic(self):

        david = yaml.load("""
        address_line_1 : 16 blooey
        postcode : sewjfd
        name : david
        email :
            -
                default_email : true
                email : poo@poo.com
            -
                email : poo2@poo.com
                default_email : false
        """)

        SingleRecord(self.donkey, "people",  david).load()

        print self.donkey.search("people",
                                  "email.default_email in (?)",
                                  values = ["false"],
                                  tables = ["people", "email"], 
                                  keep_all = False) 

        assert self.donkey.search("people",
                                  "email.default_email = ?",
                                  values = ["false"],
                                  tables = ["people", "email"],
                                  keep_all = False) == \
{'data': [{'town': None, 'email.email': u'poo2@poo.com', 'email.people_id': 1, 'name': u'david', 'dob': None, '__table': 'people', 'email.email_number': 1, 'postcode': u'sewjfd', 'country': None, 'active': None, 'email.default_email': False, 'address_line_2': None, 'address_line_3': None, 'address_line_1': u'16 blooey'}]}
        






