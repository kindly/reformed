from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from reformed.data_loader import FlatFile, load_json_from_file, SingleRecord
from reformed.export import json_dump_all_from_table
from nose.tools import assert_raises
from tests.donkey_persist_test import test_donkey_persist
import yaml
import reformed.custom_exceptions
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

    @classmethod
    def tearDownClass(cls):

        sa.orm.clear_mappers()
        cls.Donkey.status = "terminated"

    
    randish = str(time.time()).replace(".","")
    
    def test_1_add_table(self):

        self.Donkey.add_table(tables.Table("moo01%s" % self.randish, Text("moo")))
        self.Donkey.add_table(tables.Table("moo02%s" % self.randish, Text("moo")))
        self.Donkey.add_table(tables.Table("moo03%s" % self.randish, Text("moo")))
        self.Donkey.add_table(tables.Table("moo04%s" % self.randish, Text("moo")))
        self.Donkey.persist()

        for table in self.Donkey.tables.values():
            assert None not in [field.order for field in table.fields.values() if field.category.endswith("field")]

        self.Donkey.load_from_persist(True)

        result = validate_database(self.Donkey)

        assert not any([result[num] for num in range(0,4)])


        #self.jim = self.Donkey.tables["moo01%s" % self.randish].sa_class()
        #self.jim.moo = u"zjimbobidoobo"
        #self.session.add(self.jim)
        #self.session.commit()

    def test_2_add_relation(self):

        table1 = self.Donkey["moo01%s" % self.randish]

        table1.add_relation(OneToMany("moo02%s" % self.randish,
                                      "moo02%s" % self.randish))

        for table in self.Donkey.tables.values():
            assert None not in [field.order for field in table.fields.values() if field.category.endswith("field")]


        table1 = self.Donkey["moo01%s" % self.randish]
        table2 = self.Donkey["moo02%s" % self.randish]

        assert hasattr(table1.sa_class(), "moo02%s" % self.randish)

        assert "moo01%s_id" % self.randish in table2.fields
        assert "moo01%s_id" % self.randish in table2.defined_columns
        assert not table2.defined_columns["moo01%s_id" % self.randish].sa_options["nullable"]

        assert not hasattr(table1.sa_class(), "mo02%s" % self.randish)


        table1.add_relation(ManyToOne("moo03%s" % self.randish,
                                      "moo03%s" % self.randish))

        table1 =  self.Donkey["moo01%s" % self.randish]

        assert "moo03%s_id" % self.randish in table1.fields
        assert "moo03%s_id" % self.randish in table1.defined_columns
        assert not table1.defined_columns["moo03%s_id" % self.randish].sa_options["nullable"]

        assert hasattr(table1.sa_class(), "moo03%s" % self.randish)


        table1.add_relation(OneToOne("moo04%s" % self.randish,
                                      "moo04%s" % self.randish))

        table1 =  self.Donkey["moo01%s" % self.randish]

        assert hasattr(table1.sa_class(), "moo04%s" % self.randish)

        for table in self.Donkey.tables.values():
            assert None not in [field.order for field in table.fields.values() if field.category.endswith("field")]


    def test_3_rename_table(self):

        table1 = tables.Table("to_rename%s" % self.randish, Text("moo"))
        table2 = tables.Table("to_join%s" % self.randish, Text("moo"))

        start = datetime.datetime.now()

        self.Donkey.add_table(table1)
        self.Donkey.add_table(table2)
        self.Donkey.persist()
        
        table2 =  self.Donkey["to_join%s" % self.randish]

        table2.add_relation(ManyToOne("to_rename%s" % self.randish,
                                      "to_rename%s" % self.randish))




        self.Donkey.rename_table("to_rename%s" % self.randish, "renamed%s" % self.randish) 


        result = validate_database(self.Donkey)


        assert not any([result[num] for num in range(0,4)])



    def test_4_rename_drop_field(self):

        table1 = tables.Table("rename_field", Text("man"), Text("moo"), Integer("man2"), Text("man3"), Text("man4"))

        self.Donkey.add_table(table1)
        self.Donkey.persist()

        if self.Donkey.engine.name == "sqlite":
            assert_raises(Exception, table1.rename_field, "moo", "mooed") 
            return

        table1.rename_field("moo", "mooed") 

        result = validate_database(self.Donkey)

        assert not any([result[num] for num in range(0,4)])

        table1.drop_field("man") 

        result = validate_database(self.Donkey)

        assert not any([result[num] for num in range(0,4)])

        table1 = self.Donkey["rename_field"]
        
        assert set([field.order for field in table1.fields.values() if field.category.endswith("field")]) == set([1,2,3,4])

        table1.alter_field("man2", type = "Text", mandatory = True, default = "wee", validation = "Email")

        table1 = self.Donkey["rename_field"]

        assert table1.fields["man2"].field_validation == "Email"

        table1.alter_field("man2", type = "Text", mandatory = True, default = "wee", validation = "__.*")
        
        result = validate_database(self.Donkey)

        assert not any([result[num] for num in range(0,4)])

        table1 = self.Donkey["rename_field"]

        assert table1.fields["man2"].field_validation == "__.*"





    def test_5_drop_table(self):

        table1 =  self.Donkey["moo01%s" % self.randish]

        assert_raises(custom_exceptions.DependencyError, self.Donkey.drop_table, table1)

        table2 =  self.Donkey["moo02%s" % self.randish]

        self.Donkey.drop_table(table2)

        result = validate_database(self.Donkey)

        assert not any([result[num] for num in range(0,4)])

        table4 =  self.Donkey["moo04%s" % self.randish]

        self.Donkey.drop_table(table4)

        result = validate_database(self.Donkey)

        assert not any([result[num] for num in range(0,4)])

        table1 =  self.Donkey["moo01%s" % self.randish]

        self.Donkey.drop_table(table1)

        result = validate_database(self.Donkey)

        assert not any([result[num] for num in range(0,4)])

    def test_6_delete_relation(self):

        table1 = self.Donkey["renamed%s" % self.randish]
        table2 = self.Donkey["to_join%s" % self.randish]

        table2.delete_relation("to_rename%s" % self.randish)

    def test_7_add_remove_index(self):

        table1 = self.Donkey["renamed%s" % self.randish]
        table1.add_index(Index("moooed", "moo"))

        result = validate_database(self.Donkey)
        assert not any([result[num] for num in range(0,4)])

        table1 = self.Donkey["renamed%s" % self.randish]

        table1.delete_index("moooed")
        assert not any([result[num] for num in range(0,4)])






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
