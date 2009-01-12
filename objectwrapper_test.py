from fields import *
from tables import *
from database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import logging
from donkey_test import test_donkey
from objectwrapper import * 

logging.basicConfig(filename = "sql.txt")
logging.getLogger('sqlalchemy.engine').setLevel(logging.info)


class test_object_wrapper_basic(test_donkey):

    def setUp(self):

        super(test_object_wrapper_basic,self).setUp()
        paul = self.Donkey.tables["people"].sa_class()
        self.paulwrapped = ObjectWrapper(paul, self.session)
        self.paulwrapped.name = u"paul"
        self.paulwrapped.save()

        paul = self.Donkey.tables["people"].sa_class()

        self.jim100 = self.Donkey.tables["donkey"].sa_class()
        self.jim100wrapped = ObjectWrapper(self.jim100, self.session, 
                                           workflow = "onetoone")
        self.jim100wrapped.name = u"jim100"
        self.jim100wrapped.pic_name = u"jimmi"
        self.jim100wrapped.save()

        self.session.commit()
        
    def test_getting_setting_basice(self):

        assert self.paulwrapped.name == u"paul"
        assert "paul" in [people.name for people in 
                          self.session.query(self.Donkey.tables["people"].sa_class).all()]

    def test_getting_setting_one_to_one(self):

        assert self.jim100wrapped.name == u"jim100"
        assert self.jim100wrapped.pic_name == u"jimmi"

        
        assert "jim100" in [donkey.name for donkey in
                            self.session.query(self.Donkey.tables["donkey"].sa_class).all()]

        assert "jimmi" in [donkey.pic_name for donkey in
                            self.session.query(self.Donkey.tables["donkey_pics"].sa_class).all()]









        

        
        




