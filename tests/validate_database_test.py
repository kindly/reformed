from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import random
import logging
import reformed.validate_database

class test_donkey_validate_sqlite(object):

    persist = True

    @classmethod
    def setUpClass(cls):
        if not hasattr(cls, "engine"):
            cls.engine = create_engine('sqlite:///tests/test_donkey.sqlite',echo = True)
        cls.meta = sa.MetaData()
        cls.Session = sa.orm.sessionmaker(bind =cls.engine , autoflush = False)
        cls.Donkey = Database("Donkey", 
                        metadata = cls.meta,
                        engine = cls.engine,
                        session = cls.Session)

    def test_validate_database(self):

        assert reformed.validate_database.validate_database(self.Donkey) is None

    def test_validate_after_add_table(self):
        
        self.Donkey.add_table(tables.Table("woo%s" % random.randrange(1,10000) , Text("woo")))
        self.Donkey.update_sa()

        assert_raises(custom_exceptions.DatabaseInvalid, 
                      reformed.validate_database.validate_database, self.Donkey)


        self.Donkey.persist()





class test_donkey_validate_mysql(test_donkey_validate_sqlite):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('mysql://localhost/test_donkey', echo = True)
        super(test_donkey_validate_mysql, cls).setUpClass()

class test_donkey_validate_post(test_donkey_validate_sqlite):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('postgres://david:@:5432/test_donkey', echo = True)
        super(test_donkey_validate_post, cls).setUpClass()
