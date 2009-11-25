from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from reformed.data_loader import FlatFile, load_json_from_file, SingleRecord
from reformed.export import json_dump_all_from_table
from nose.tools import assert_raises
from tests.donkey_persist_test import test_donkey_persist
import yaml
import datetime
import sqlalchemy as sa
from sqlalchemy import create_engine
import random
import time
from reformed.util import get_table_from_instance, load_local_data
from reformed.validate_database import validate_database
import logging
from migrate.versioning import schemadiff


sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)


class test_modify_table_sqlite(object):

    @classmethod
    def setUpClass(cls):

        if not hasattr(cls, "engine"):
            cls.engine = create_engine('sqlite:///tests/test_donkey.sqlite')

        meta_to_drop = sa.MetaData()
        meta_to_drop.reflect(bind=cls.engine)
        for table in reversed(meta_to_drop.sorted_tables):
            table.drop(bind=cls.engine)

        cls.meta = sa.MetaData()
        cls.Session = sa.orm.sessionmaker(bind =cls.engine , autoflush = False)
        cls.Donkey = Database("Donkey", 
                        metadata = cls.meta,
                        engine = cls.engine,
                        session = cls.Session)

    
    randish = str(time.time()).replace(".","")
    
    def test_1_add_table(self):

        self.Donkey.add_table(tables.Table("moo01%s" % self.randish, Text("moo")))
        self.Donkey.add_table(tables.Table("moo02%s" % self.randish, Text("moo")))
        self.Donkey.add_table(tables.Table("moo03%s" % self.randish, Text("moo")))
        self.Donkey.add_table(tables.Table("moo04%s" % self.randish, Text("moo")))
        self.Donkey.persist()

        self.Donkey.load_from_persist(True)

        result = validate_database(self.Donkey)

        assert result[0] == []
        assert result[1] == []
        assert result[2] == []

        #self.jim = self.Donkey.tables["moo01%s" % self.randish].sa_class()
        #self.jim.moo = u"zjimbobidoobo"
        #self.session.add(self.jim)
        #self.session.commit()

    def test_add_relation(self):

        table1 =  self.Donkey["moo01%s" % self.randish]
        table2 =  self.Donkey["moo02%s" % self.randish]

        table1.add_relation(OneToMany("moo02%s" % self.randish,
                                      "moo02%s" % self.randish))

        assert hasattr(table1.sa_class(), "moo02%s" % self.randish)

        assert not hasattr(table1.sa_class(), "mo02%s" % self.randish)


        table1.add_relation(ManyToOne("moo03%s" % self.randish,
                                      "moo03%s" % self.randish))

        assert hasattr(table1.sa_class(), "moo03%s" % self.randish)


        table1.add_relation(OneToOne("moo04%s" % self.randish,
                                      "moo04%s" % self.randish))

        assert hasattr(table1.sa_class(), "moo04%s" % self.randish)



    def test_rename_table(self):

        table1 = tables.Table("to_rename%s" % self.randish, Text("moo"))
        table2 = tables.Table("to_join%s" % self.randish, Text("moo"))

        start = datetime.datetime.now()

        self.Donkey.add_table(table1)
        self.Donkey.add_table(table2)
        self.Donkey.persist()

        table2.add_relation(ManyToOne("to_rename%s" % self.randish,
                                      "to_rename%s" % self.randish))


        self.Donkey.rename_table("to_rename%s" % self.randish, "renamed%s" % self.randish) 


        result = validate_database(self.Donkey)


        assert result[0] == []
        assert result[1] == []
        assert result[2] == []

        self.Donkey.load_from_persist(True)


        result = validate_database(self.Donkey)

        assert result[0] == []
        assert result[1] == []
        assert result[2] == []









class test_modify_table_mysql(test_modify_table_sqlite):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('mysql://localhost/test_donkey')
        super(test_modify_table_mysql, cls).setUpClass()


class test_modify_table_postgres(test_modify_table_sqlite):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('postgres://david:@:5432/test_donkey')
        super(test_modify_table_postgres, cls).setUpClass()
