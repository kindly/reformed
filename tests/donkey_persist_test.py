from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from reformed.data_loader import FlatFile
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import random
import logging

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)

class test_donkey_persist_sqlite(object):

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
        davidsjim.people = cls.david
        davidsjim.donkey = cls.jim
        davidsjim.amount = 50
        
        jimpic = file("tests/jim.xcf", mode = "rb").read()
        
        jimimage = cls.Donkey.tables["donkey_pics"].sa_class()
        jimimage.donkey = cls.jim
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
        cls.session.commit()

        cls.david2 = cls.Donkey.tables["people"].sa_class()
        cls.david2.name = u"david"
        cls.david2.address_line_1 = u""
        cls.david_logged = cls.david._table.logged_instance(cls.david)
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

        
    @classmethod
    def tearDownClass(cls):

        cls.session.close()


#class test_basic_input(test_donkey_persist):

    def test_donkey_input(self):

        assert u"jim" in [a.name for a in\
                          self.session.query(self.Donkey.tables["donkey"].sa_class).all()]

#       assert self.david in [ds for ds in\
#                         [a.people for a in\
#                          self.session.query(self.Donkey.tables["donkey_sponsership"].sa_class).all()]]

#       assert self.jim in [ds for ds in\
#                        [a.donkey for a in\
#                         self.session.query(self.Donkey.tables["donkey_sponsership"].sa_class).all()]]

    def test_address_validation(self):

        assert len(self.david._table.validate(self.david)) > 3
        
        assert_raises(formencode.Invalid,
                      self.david2._table.validate,self.david2)

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

    def test_z_add_entity_after_loaded(self):

        p = random.randrange(1,10000)
        self.Donkey.add_entity(tables.Table("entity%s" % p, Text("moo")))
        self.Donkey.persist()

        self.jim = self.Donkey.tables["entity%s" % p].sa_class()
        self.jim.moo = u"zjimbobidoobo"
        self.session.add(self.jim)
        self.session.commit()
        print [a.entity_id for a in self.session.query(self.Donkey.get_class("entity%s" % p)).all()]
        assert all([a.entity_id for a in self.session.query(self.Donkey.get_class("entity%s" % p)).all()])

    def test_log_tables_loaded(self):

        assert hasattr(self.Donkey.get_class("_log_people"), "name")

    def test_automatic_logging(self):

        all_logs = self.session.query(self.Donkey.get_class("_log_donkey")).all()
        assert (self.jimmi_id, u"jimmii%s" % self.p) in [(a.donkey_id,a.name) for a in all_logs]

    def test_params_load(self):

        assert self.Donkey.tables["donkey"].fields["name"]._validation == "__^[a-zA-Z0-9]*$"
        assert self.Donkey.tables["donkey"].fields["donkey_pics"]._many_side_mandatory == False 
        assert self.Donkey.tables["donkey"].fields["age"]._validation == "Int"
        assert self.Donkey.tables["people"].fields["name"]._length == 30
        assert self.Donkey.tables["people"].fields["name"]._mandatory == True
        assert self.Donkey.tables["people"].fields["email"]._cascade == "all, delete-orphan"
        assert self.Donkey.tables["people"].fields["email"]._order_by == "email"
        assert self.Donkey.tables["people"].fields["email"]._eager == True

    def test_regex_validation(self):

        poo = self.Donkey.tables["donkey"].sa_class()
        poo.name = "don_keyfasf"
        assert_raises(formencode.Invalid, self.session.add, poo)

    def test_data_load_with_header(self):

        flatfile = FlatFile(self.Donkey,
                            "people",
                            "tests/new_people_with_header.csv")    
        flatfile.load()


        result = self.session.query(self.Donkey.get_class("people")).filter_by(name = "popph15").first()

        assert 1500 in [a.amount for a in result.donkey_sponsership]
    
class test_donkey_persist_mysql(test_donkey_persist_sqlite):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('mysql://localhost/test_donkey', echo = True)
        super(test_donkey_persist_mysql, cls).setUpClass()

class test_donkey_persist_post(test_donkey_persist_sqlite):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('postgres://david:@:5432/test_donkey', echo = True)
        super(test_donkey_persist_post, cls).setUpClass()
