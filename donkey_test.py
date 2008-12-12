from columns import *
from tables import *
from database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import logging

logging.basicConfig(filename = "sql.txt")
logging.getLogger('sqlalchemy.engine').setLevel(logging.info)

class test_basic_input(object):

    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', echo=True)
        self.meta = sa.MetaData()
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
                        metadata = self.meta
                        )

        self.Donkey.update_sa()

        self.meta.create_all(self.engine)
        self.Session = sa.orm.sessionmaker(bind =self.engine)


    def test_donkey_input(self):

        session = self.Session()

        jim = self.Donkey.tables["donkey"].sa_class()
        jim.name = u"jim"
        jim.age = 13
        david = self.Donkey.tables["people"].sa_class()
        david.name = u"david"
        david.address_line_1 = u"43 union street"
        davidsjim = self.Donkey.tables["donkey_sponsership"].sa_class()
        davidsjim.people = david
        davidsjim.donkey = jim
        davidsjim.amount = 50
        
        jimpic = file("jim.xcf", mode = "rb").read()
        


        jimimage = self.Donkey.tables["donkey_pics"].sa_class()
        jimimage.pic = jimpic

        session.add(david)
        session.add(jim)
        session.add(davidsjim)
        session.add(jimimage)
        session.commit()

        assert u"jim" in [a.name for a in\
                          session.query(self.Donkey.tables["donkey"].sa_class).all()]

        assert david in [ds for ds in\
                         [a.people for a in\
                          session.query(self.Donkey.tables["donkey_sponsership"].sa_class).all()]]

        assert jim in [ds for ds in\
                         [a.donkey for a in\
                          session.query(self.Donkey.tables["donkey_sponsership"].sa_class).all()]]
                          

        session.close()





        


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

    assert "fred" in [a.name for a in\
                      session.query(Donkey.tables["people"].sa_class).all()]

    session.close()

