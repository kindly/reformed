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
from tests.donkey_test import test_donkey

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)

class test_donkey_validate_sqlite(test_donkey):

    persist = True

    @classmethod
    def setUpClass(cls):
        if not hasattr(cls, "engine"):
            cls.engine = create_engine('sqlite:///tests/test_donkey.sqlite',echo = True)

        meta_to_drop = sa.MetaData()
        meta_to_drop.reflect(bind=cls.engine)
        for table in reversed(meta_to_drop.sorted_tables):
            table.drop(bind=cls.engine)

        super(test_donkey_validate_sqlite, cls).setUpClass()

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
        
        self.Donkey._add_table_no_persist(tables.Table("woo%s" % rand , Text("woo")))
        self.Donkey.update_sa(update_tables = False)

        assert_raises(custom_exceptions.DatabaseInvalid, 
                      reformed.validate_database.validate_database, self.Donkey)
        try:
            reformed.validate_database.validate_database(self.Donkey)
        except custom_exceptions.DatabaseInvalid, e:
            assert "woo%s" % rand in e.list

        self.Donkey.persist()

    def test_validate_after_wronly_add_field(self):

        rand = random.randrange(1,100000)

        self.Donkey.tables["people"]._add_field_no_persist( Text("wrong%s" % rand))
        self.Donkey.update_sa(reload = True)
        self.Donkey.metadata.create_all(self.Donkey.engine)

        assert_raises(custom_exceptions.DatabaseInvalid,
                      reformed.validate_database.validate_database, self.Donkey)
        try:
            reformed.validate_database.validate_database(self.Donkey)
        except custom_exceptions.DatabaseInvalid, e:
            assert u"people.wrong%s" % rand in e.list


        self.Donkey.tables["people"]._add_field_by_alter_table(Text("wrong%s" % rand))

    def test_validate_after_added_column(self):

        rand = random.randrange(1,100000)

        self.Donkey.tables["people"]._add_field_by_alter_table(Text("wrong%s" % rand))

        self.Donkey.update_sa(reload = True)

        tab_def, tab_dat, col_def, col_dat, col_dif = reformed.validate_database.validate_database(self.Donkey) 

        assert u"people.wrong%s" % rand in col_dat

    def test_validate_after_difference(self):

        rand = random.randrange(1,100000)

        self.Donkey.tables["people"]._add_field_by_alter_table(Text("wrong%s" % rand))

        self.Donkey.tables["people"]._add_field_no_persist( Money("wrong%s" % rand))

        self.Donkey.update_sa(reload = True)

        tab_def, tab_dat, col_def, col_dat, col_dif = reformed.validate_database.validate_database(self.Donkey) 
        
        assert u"people.wrong%s" % rand in col_dif
        


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
