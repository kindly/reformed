from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import random
import logging
import reformed.validate_database
import migrate.changeset

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)

class test_donkey_validate_sqlite(object):

    persist = True

    @classmethod
    def setUpClass(cls):
        if not hasattr(cls, "engine"):
            cls.engine = create_engine('sqlite:///tests/test_donkey.sqlite',echo = True)
        cls.meta = sa.MetaData(cls.engine)
        cls.Session = sa.orm.sessionmaker(bind =cls.engine , autoflush = False)
        cls.Donkey = Database("Donkey", 
                        metadata = cls.meta,
                        engine = cls.engine,
                        session = cls.Session)

    def test_validate_database(self):

        tab_def, tab_dat, col_def, col_dat, col_dif = reformed.validate_database.validate_database(self.Donkey) 
        assert tab_def == []
        assert col_def == []

    def test_validate_after_add_table(self):

        rand = random.randrange(1,10000)
        
        self.Donkey.add_table(tables.Table("woo%s" % rand , Text("woo")))
        self.Donkey.update_sa()

        assert_raises(custom_exceptions.DatabaseInvalid, 
                      reformed.validate_database.validate_database, self.Donkey)
        try:
            reformed.validate_database.validate_database(self.Donkey)
        except custom_exceptions.DatabaseInvalid, e:
            assert "woo%s" % rand in e.list

        self.Donkey.persist()

    def test_validate_after_wronly_add_field(self):

        rand = random.randrange(1,10000)

        self.Donkey.tables["people"].add_field( Text("wrong%s" % rand))
        self.Donkey.update_sa(reload = True)
        self.Donkey.metadata.create_all(self.Donkey.engine)

        assert_raises(custom_exceptions.DatabaseInvalid,
                      reformed.validate_database.validate_database, self.Donkey)

        self.Donkey.tables["people"]._add_field_by_alter_table(Text("wrong%s" % rand))

        





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
