from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import os
import logging

sqlhandler = logging.FileHandler("sql.txt")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)

class test_donkey(object):

    @classmethod
    def setUpClass(self):
        self.engine = create_engine('sqlite:///:memory:', echo=True)
#       os.system("rm tests/test_donkey.sqlite")
#       self.engine = create_engine('sqlite:///tests/test_donkey.sqlite',echo = True)
        self.meta = sa.MetaData()
        self.Session = sa.orm.sessionmaker(bind =self.engine, autoflush = False)
        self.Donkey = Database("Donkey", 
                            Table("people",
                                  Text("name"),
                                  Address("supporter_address"),
                                  OneToMany("email","email"),
                                  OneToMany("donkey_sponsership",
                                            "donkey_sponsership"),
                                  entity = True),
                            Table("email",
                                  Email("email")
                                 ),
                            Table("donkey", 
                                  Text("name"),
                                  Integer("age"),
                                  OneToOne("donkey_pics","donkey_pics"),
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
                        metadata = self.meta,
                        engine = self.engine,
                        session = self.Session
                        )

        self.Donkey.persist()

        self.session = self.Donkey.Session()

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
        davidsjim._people = self.david
        davidsjim._donkey = self.jim
        davidsjim.amount = 50
        
        jimpic = file("tests/jim.xcf", mode = "rb").read()
        
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
        
if __name__ == '__main__':

    engine = create_engine('sqlite:///:memory:', echo=True)
    meta = sa.MetaData()
    Donkey = Database("Donkey", 
                        Table("people",
                              Text("name"),
                              Address("supporter_address"),
                              OneToMany("email","email"),
                              OneToMany("donkey_sponsership","donkey_sponsership"),
                              entity = True),
                        Table("email",
                              Email("email")
                             ),
                        Table("donkey", 
                              Text("name"),
                              Integer("age"),
                              OneToOne("donkey_pics","donkey_pics"),
                              OneToMany("donkey_sponsership","donkey_sponsership"),
                              entity = True
                             ),
                        Table("donkey_pics",
                              Binary("pic")
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
                    metadata = meta
                    )
    
    Donkey.update_sa()
    meta.create_all(engine)

    Session = sa.orm.sessionmaker(bind =engine)

    session = Session()

    fred = Donkey.tables["people"].sa_class()
    fred.name = "fred"
#    fred.age = 13
#

    session.add(fred)
    session.commit()

    new = session.query(Donkey.tables["people"].sa_class).one()

    



