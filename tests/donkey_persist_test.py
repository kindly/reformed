from database.fields import *
from database.tables import *
from database.database import *
from database.data_loader import FlatFile, load_json_from_file, SingleRecord
from database.export import json_dump_all_from_table
from nose.tools import assert_raises
import yaml
import sqlalchemy as sa
from sqlalchemy import create_engine
import random
import time
from tests.donkey_test import test_donkey
from database.util import get_table_from_instance, load_local_data
from database.validate_database import validate_database
import logging
from migrate.versioning import schemadiff

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)


class test_donkey_persist(test_donkey):

    persist = True

    @classmethod
    def setUpClass(cls):

        if not hasattr(cls, "engine"):
            os.system("rm tests/test_donkey.sqlite")
            cls.engine = create_engine('sqlite:///tests/test_donkey.sqlite')

        try:
            os.remove("tests/zodb.fs")
            os.remove("tests/zodb.fs.lock")
            os.remove("tests/zodb.fs.index")
            os.remove("tests/zodb.fs.tmp")
        except OSError:
            pass

        meta_to_drop = sa.MetaData()
        meta_to_drop.reflect(bind=cls.engine)
        for table in reversed(meta_to_drop.sorted_tables):
            table.drop(bind=cls.engine)

        super(test_donkey_persist, cls).setUpClass()

#        cls.meta = sa.MetaData()
#        cls.Session = sa.orm.sessionmaker(bind =cls.engine , autoflush = False)
#        cls.Donkey = Database("Donkey",
#                        zodb_store = "tests/zodb.fs",
#                        metadata = cls.meta,
#                        engine = cls.engine,
#                        session = cls.Session)

        cls.p = random.randrange(1,10000)
        cls.Donkey.add_table(tables.Table("moo%s" % cls.p, Text("moo")))
        cls.Donkey.persist()

        cls.session = cls.Donkey.Session()

        cls.jim = cls.Donkey.tables["donkey"].sa_class()
        cls.jim.name = u"jim"
        cls.jim.age = 13
        cls.jim1 = cls.Donkey.tables["donkey"].sa_class()
        cls.jim1.name = u"jim1"
        cls.jim1.age = 131
        jim2 = cls.Donkey.tables["donkey"].sa_class()
        jim2.name = u"jim2"
        jim2.age = 132
        jim3 = cls.Donkey.tables["donkey"].sa_class()
        jim3.name = u"jim3"
        jim3.age = 133
        jim4 = cls.Donkey.tables["donkey"].sa_class()
        jim4.name = u"jim4"
        jim4.age = 142
        jim5 = cls.Donkey.tables["donkey"].sa_class()
        jim5.name = u"jim5"
        jim5.age = 135
        jim6 = cls.Donkey.tables["donkey"].sa_class()
        jim6.name = u"jim6"
        jim6.age = 136
        jim7 = cls.Donkey.tables["donkey"].sa_class()
        jim7.name = u"jim7"
        jim7.age = 137
        jim8 = cls.Donkey.tables["donkey"].sa_class()
        jim8.name = u"jim8"
        jim8.age = 138
        jim9 = cls.Donkey.tables["donkey"].sa_class()
        jim9.name = u"jim9"
        jim9.age = 132
        jim0 = cls.Donkey.tables["donkey"].sa_class()
        jim0.name = u"jim0"
        jim0.age = 102
        cls.david = cls.Donkey.tables["people"].sa_class()
        cls.david.name = u"david"
        cls.david.address_line_1 = u"43 union street"
        cls.david.postcode = u"es388"
        davidsjim = cls.Donkey.tables["donkey_sponsership"].sa_class()
        davidsjim._people = cls.david
        davidsjim._donkey = cls.jim
        davidsjim.amount = 50

        jimpic = file("tests/jim.xcf", mode = "rb").read()

        jimimage = cls.Donkey.tables["donkey_pics"].sa_class()
        jimimage.pic = jimpic

        cls.session.add(cls.david)
        cls.session.add(cls.jim)
        cls.session.add(cls.jim1)
        cls.session.add(jim2)
        cls.session.add(jim3)
        cls.session.add(jim4)
        cls.session.add(jim5)
        cls.session.add(jim6)
        cls.session.add(jim7)
        cls.session.add(jim8)
        cls.session.add(jim9)
        cls.session.add(jim0)
        cls.session.add(davidsjim)
        cls.session.add(jimimage)

        cls.david2 = cls.Donkey.tables["people"].sa_class()
        cls.david2.name = u"david"
        cls.david2.address_line_1 = u""
        cls.david_logged = get_table_from_instance(cls.david, cls.Donkey).logged_instance(cls.david)
        cls.session.add(cls.david_logged)
        cls.session.commit()

        donk = cls.session.query(cls.Donkey.get_class("donkey")).first()
        donk.name = u"jimmii%s" % cls.p
        cls.session.add(donk)
        cls.session.commit()
        cls.jimmi_id = donk.id


        donk2 = cls.session.query(cls.Donkey.get_class("donkey")).filter_by(name=donk.name).first()
        donk2.name = u"jimmii"
        cls.session.add(donk2)
        cls.session.commit()


class test_donkey_persist_sqlite(test_donkey_persist):


    @classmethod
    def tearDownClass(cls):

        cls.session.close()
        sa.orm.clear_mappers()
        cls.Donkey.status = "terminated"


    def test_1_donkey_input(self):

        assert u"jim" in [a.name for a in\
                          self.session.query(self.Donkey.tables["donkey"].sa_class).all()]

        assert self.david in [ds for ds in\
                          [a._people for a in\
                           self.session.query(self.Donkey.tables["donkey_sponsership"].sa_class).all()]]

        assert self.jim in [ds for ds in\
                         [a._donkey for a in\
                          self.session.query(self.Donkey.tables["donkey_sponsership"].sa_class).all()]]

    def test_address_validation(self):

        assert len(get_table_from_instance(self.david, self.Donkey).validate(self.david, self.session)) > 3

        assert_raises(formencode.Invalid,
                      get_table_from_instance(self.david2, self.Donkey).validate,self.david2, self.session)

    #def test_many_side_not_null(self):

    #    email = self.Donkey.t.email()
    #    email.email = "poo@poo.com"
    #    assert_raises(formencode.Invalid, self.session.save, email)

    def test_logged_attribute(self):


        assert self.david_logged.name == u"david"
        assert self.david_logged.address_line_1 == u"43 union street"
        assert self.david_logged.postcode == u"es388"

    def test_z_add_table_after_loaded(self):

        p = random.randrange(1,10000)
        self.Donkey.add_table(tables.Table("moo%s" % p, Text("moo")))
        self.Donkey.persist()

        self.jim = self.Donkey.tables["moo%s" % p].sa_class()
        self.jim.moo = u"zjimbobidoobo"
        self.session.add(self.jim)
        self.session.commit()

    def test_zz_drop_table(self):

        self.Donkey.drop_table("moo%s" % self.p)

        assert "moo%s" % self.p not in self.Donkey.tables
        assert "_log_moo%s" % self.p not in self.Donkey.tables


        assert validate_database(self.Donkey)[0] == []
        assert validate_database(self.Donkey)[1] == []
        assert validate_database(self.Donkey)[2] == []

        ## field difference ok due to server default diffs not workin
        ##assert validate_database(self.Donkey)[4] == []

    def test_add_ignore_existing_table(self):

        a = len(self.Donkey.tables)

        self.Donkey.add_table(tables.Table("donkey", Text("moo")), ignore = True)

        b = len(self.Donkey.tables)

        assert a == b

    def test_z_add_drop_existing_table(self):
        print self.Donkey.tables.keys()


        self.Donkey.add_table(tables.Table("moo%s" % self.p, Text("moo%s" % self.p)), drop = True)

        self.Donkey.persist()



        print validate_database(self.Donkey)
        diff = schemadiff.getDiffOfModelAgainstDatabase(self.Donkey.metadata,
                                                    self.Donkey.engine)

        print diff
        assert validate_database(self.Donkey)[0] == []
        assert validate_database(self.Donkey)[1] == []
        assert validate_database(self.Donkey)[2] == []

        ## field difference ok due to server default diffs not workin
        ## assert validate_database(self.Donkey)[4] == []

    def test_z_add_entity_after_loaded(self):

        p = random.randrange(1,10000)
        self.Donkey.add_entity(tables.Table("entity%s" % p, Text("moo"), Text("name")))
        self.Donkey.persist()

        self.jim = self.Donkey.tables["entity%s" % p].sa_class()
        self.jim.moo = u"zjimbobidoobo"
        self.session.add(self.jim)
        self.session.commit()
        assert all([a._core_entity_id for a in self.session.query(self.Donkey.get_class("entity%s" % p)).all()])

    def test_log_tables_loaded(self):

        assert hasattr(self.Donkey.get_class("_log_people"), "name")

    def test_automatic_logging(self):

        all_logs = self.session.query(self.Donkey.get_class("_log_donkey")).all()

        assert (self.jimmi_id, u"jimmii%s" % self.p) in [(a._logged_table_id,a.name) for a in all_logs]

    def test_params_load(self):

        assert self.Donkey.tables["donkey"].fields["name"].field_validation == "__^[a-zA-Z0-9]*$"
        assert self.Donkey.tables["donkey"].fields["donkey_pics"].many_side_not_null == False
        assert self.Donkey.tables["donkey"].fields["age"].field_validation == "Int"
        assert self.Donkey.tables["people"].fields["name"].length == 30
        assert self.Donkey.tables["people"].fields["name"].mandatory == True
        assert self.Donkey.tables["people"].fields["email"].cascade == "all, delete-orphan"
        assert self.Donkey.tables["people"].fields["email"].order_by == "email"
        assert self.Donkey.tables["people"].fields["email"].eager == True

    def test_regex_validation(self):

        poo = self.Donkey.tables["donkey"].sa_class()
        poo.name = "don_keyfasf"
        assert_raises(formencode.Invalid, self.session.add, poo)

    def test_data_load_with_header(self):

        flatfile = FlatFile(self.Donkey,
                            "people",
                            "tests/new_people_with_header.csv")

        flatfile.load()


        result = self.session.query(self.Donkey.get_class("people")).filter_by(name = u"popph15").first()

        assert 1500 in [a.amount for a in result.donkey_sponsership]

    def test_indexs_present(self):

        print [a.name for a in self.Donkey.tables["donkey"].sa_table.indexes]
        assert "idx_name" in [a.name for a in self.Donkey.tables["donkey"].sa_table.indexes]


    def test_all_fields_have_different_numbers(self):


        for table in self.Donkey.tables.values():
            if table.name.startswith("__") or table.name.startswith("_log_"):
                continue
            field_ids = []
            print table

            for field in table.fields.values():
                print field.name,field.field_id
                field_ids.append(field.field_id)


            print field_ids
            assert len(field_ids) == len(set(field_ids))

    ## to test later

    #def test_zzz_cascade(self):

    #    load_local_data(self.Donkey, {"__table": u"sub_sub_category",
    #                                  "category.category_name": u"a",
    #                                  "category.category_description": u"this is a",
    #                                  "category.category_type": u"wee",
    #                                  "sub_category.sub_category_name": u"ab",
    #                                  "sub_category.sub_category_description": u"this is ab",
    #                                  "sub_sub_category.sub_sub_category_name": u"abc",
    #                                  "sub_sub_category.sub_sub_category_description": u"this is abc"}
    #                   )
#
#        a = self.session.query(self.Donkey.t.category).first()
#
#        a.category_name = "oh no"

#        self.session.session.commit()



    def tfdsest_z_after_export_then_import(self):

        session = self.Donkey.Session()

        donkey_spon = self.Donkey.get_class("donkey_sponsership")
        countpeople = session.query(self.Donkey.get_class("people")).count()
        countspone = session.query(self.Donkey.get_class("donkey_sponsership")).filter(donkey_spon.people_id != None).count()

        json_dump_all_from_table(session, "people", self.Donkey, "tests/json_dump_persistant.json")

        load_json_from_file("tests/json_dump_persistant.json", self.Donkey, "people")

        countpeopleafter = session.query(self.Donkey.get_class("people")).count()
        countsponeafter = session.query(self.Donkey.get_class("donkey_sponsership")).filter(donkey_spon.people_id != None).count()

        assert countpeople*2  == countpeopleafter
        assert countspone*2  == countsponeafter


class test_donkey_persist_mysql(test_donkey_persist_sqlite):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('mysql://localhost/test_donkey')
        super(test_donkey_persist_mysql, cls).setUpClass()

class test_donkey_persist_post(test_donkey_persist_sqlite):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('postgres://david:@:5432/test_donkey')
        super(test_donkey_persist_post, cls).setUpClass()
