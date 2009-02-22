from fields import *
from tables import *
from database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import logging
import random

class test_donkey_persist(object):

    @classmethod
    def setUpClass(self):
        self.engine = create_engine('sqlite:///donkey.sqlite')
        self.meta = sa.MetaData()
        self.Session = sa.orm.sessionmaker(bind =self.engine)
        self.Donkey = Database("Donkey", 
                        metadata = self.meta,
                        engine = self.engine,
                        session = self.Session)

#       self.Donkey.load_from_persist()
        p = random.randrange(1,10000)
        self.Donkey.add_table(tables.Table("moo%s" % p, Text("moo")))
        self.Donkey.persist()

#       self.jim = self.Donkey.donkey()
#       self.jim.name = u"zjimbobidoobo"
#       self.session.add(self.jim)
#       self.session.commit()

#        self.Donkey.persist()
#       self.Donkey.add_table(tables.Table("moofds", Text("moo")))
#      p = random.randrange(1,10000)
#       self.Donkey.add_table(tables.Table("moo%s" % p, Text("moo")))
    
        self.session = self.Session()

        self.jim = self.Donkey.tables["donkey"].sa_class()
        self.jim.name = u"jim"
        self.jim.age = 13
        self.jim1 = self.Donkey.tables["donkey"].sa_class()
        self.jim1.name = u"jim1"
        self.jim1.age = 131
        jim2 = self.Donkey.tables["donkey"].sa_class()
        jim2.name = u"jim2"
        jim2.age = 132
        jim3 = self.Donkey.tables["donkey"].sa_class()
        jim3.name = u"jim3"
        jim3.age = 133
        jim4 = self.Donkey.tables["donkey"].sa_class()
        jim4.name = u"jim4"
        jim4.age = 142
        jim5 = self.Donkey.tables["donkey"].sa_class()
        jim5.name = u"jim5"
        jim5.age = 135
        jim6 = self.Donkey.tables["donkey"].sa_class()
        jim6.name = u"jim6"
        jim6.age = 136
        jim7 = self.Donkey.tables["donkey"].sa_class()
        jim7.name = u"jim7"
        jim7.age = 137
        jim8 = self.Donkey.tables["donkey"].sa_class()
        jim8.name = u"jim8"
        jim8.age = 138
        jim9 = self.Donkey.tables["donkey"].sa_class()
        jim9.name = u"jim9"
        jim9.age = 132
        jim0 = self.Donkey.tables["donkey"].sa_class()
        jim0.name = u"jim0"
        jim0.age = 102
        self.david = self.Donkey.tables["people"].sa_class()
        self.david.name = u"david"
        self.david.address_line_1 = u"43 union street"
        self.david.postcode = u"es388"
        davidsjim = self.Donkey.tables["donkey_sponsership"].sa_class()
        davidsjim.people = self.david
        davidsjim.donkey = self.jim
        davidsjim.amount = 50
        
        jimpic = file("jim.xcf", mode = "rb").read()
        
        jimimage = self.Donkey.tables["donkey_pics"].sa_class()
        jimimage.donkey = self.jim
        jimimage.pic = jimpic

        self.session.add(self.david)
        self.session.add(self.jim)
        self.session.add(self.jim1)
        self.session.add(jim2)
        self.session.add(jim3)
        self.session.add(jim4)
        self.session.add(jim5)
        self.session.add(jim6)
        self.session.add(jim7)
        self.session.add(jim8)
        self.session.add(jim9)
        self.session.add(jim0)
        self.session.add(davidsjim)
        self.session.add(jimimage)
        self.session.commit()

        self.david2 = self.Donkey.tables["people"].sa_class()
        self.david2.name = u"david"
        self.david2.address_line_1 = u""
        self.david_logged = self.david._table.logged_instance(self.david)
        self.session.add(self.david_logged)
        self.session.commit()
        
    @classmethod
    def tearDownClass(self):

        self.session.close()


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

    def test_add_table_after_loaded(self):

        p = random.randrange(1,10000)
        self.Donkey.add_table(tables.Table("moo%s" % p, Text("moo")))
        self.Donkey.persist()

        self.jim = self.Donkey.tables["donkey"].sa_class()
        self.jim.name = u"zjimbobidoobo"
        self.session.add(self.jim)
        self.session.commit()


        




if __name__ == '__main__':
    
        engine = create_engine('sqlite:///donkey.db', echo=True)
        meta = sa.MetaData()
        Session = sa.orm.sessionmaker(bind =engine)
        Donkey = Database("Donkey", 
                        metadata = meta,
                        engine = engine,
                        session = Session)

