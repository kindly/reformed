from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import os
import logging

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)

class test_donkey(object):

    @classmethod
    def setUpClass(cls):
        if not hasattr(cls, "engine"):
            cls.engine = create_engine('sqlite:///:memory:', echo=True)
        
#        cls.engine = create_engine('mysql://localhost/test_donkey', echo = True)
        cls.meta = sa.MetaData()
        cls.Session = sa.orm.sessionmaker(bind =cls.engine, autoflush = False)
        cls.Donkey = Database("Donkey", 
                            Table("people",
                                  Text("name", mandatory = True, length = 30),
                                  Address("supporter_address"),
                                  OneToMany("email","email", 
                                            order_by = "email",
                                            eager = True, 
                                            cascade = "all, delete-orphan"),
                                  OneToMany("donkey_sponsership",
                                            "donkey_sponsership"),
                                  OneToMany("relation",
                                            "relation"),
                                  entity = True),
                            Table("email",
                                  Email("email")
                                 ),
                            Table("donkey", 
                                  Text("name", validation = '__^[a-zA-Z0-9]*$'),
                                  Integer("age", validation = 'Int'),
                                  OneToOne("donkey_pics","donkey_pics",
                                           many_side_mandatory = False,
                                           ),
                                  OneToMany("donkey_sponsership",
                                            "donkey_sponsership"),
                                  entity = True
                                 ),
                            Table("donkey_pics",
                                  Binary("pic"),
                                  Text("pic_name")
                                 ),
                            Table("donkey_sponsership",
                                  Money("amount"),
                                  Date("giving_date"),
                                  entity_relationship = True
                                 ),
                            Table("payments",
                                  Date("giving_date"),
                                  Money("amount"),
                                  Text("source")
                                 ),
                             Table("relation",
                                   Text("relation_type"),
                                   ManyToOne("people", "people")
                                  ),
                        metadata = cls.meta,
                        engine = cls.engine,
                        session = cls.Session
                        )

        cls.Donkey.persist()

        cls.set_up_inserts()

    @classmethod
    def set_up_inserts(cls):

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
        
    @classmethod
    def tearDownClass(cls):

        cls.session.close()


class test_basic_input(test_donkey):

    def test_donkey_input(self):

        assert u"jim" in [a.name for a in\
                          self.session.query(self.Donkey.tables["donkey"].sa_class).all()]

        assert self.david in [ds for ds in\
                         [a._people for a in\
                          self.session.query(self.Donkey.tables["donkey_sponsership"].sa_class).all()]]

        assert self.jim in [ds for ds in\
                         [a._donkey for a in\
                          self.session.query(self.Donkey.tables["donkey_sponsership"].sa_class).all()]]

    def test_address_validation(self):

        assert len(self.david._table.validate(self.david)) > 3
        
        assert_raises(formencode.Invalid,
                      self.david2._table.validate,self.david2)

    def test_logged_attribute(self):

        assert self.david_logged.name == u"david"
        assert self.david_logged.address_line_1 == u"43 union street"
        assert self.david_logged.postcode == u"es388"

    def test_regex_validation(self):

        poo = self.Donkey.tables["donkey"].sa_class()
        poo.name = "don_keyfasf"
        assert_raises(formencode.Invalid,self.session.add, poo)

    def test_table_paths(self):

        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey")] == ["donkey", "manytoone"]
        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey", "donkey_pics",)] == ["donkey_pics", "onetoone"]
        assert self.Donkey.tables["donkey"].paths[("donkey_sponsership", "_people", "email")] == ["email", "onetomany"]

class test_after_reload(test_basic_input):
    
    @classmethod
    def setUpClass(cls):
        super(test_after_reload, cls).setUpClass()
        cls.Donkey.update_sa(reload = True)
        super(test_after_reload, cls).set_up_inserts()
        
    @classmethod
    def set_up_inserts(cls):
        pass
        
