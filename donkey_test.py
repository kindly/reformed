from columns import *
from tables import *
from database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine

class test_basic_input(object):

    def sjkletUp(self):
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
        self.meta.create_all(self.engine)

        self.Session = sa.orm.sessionmaker(bind =self.engine)


    def teihjkst_donkey_input(self):

        session = self.Session()

        fred = self.Donkey.tables["donkey"].sa_class()
        fred.name = "fred"
        fred.age = 13

        session.add(fred)
        session.commit()

        assert "fred" in [a.name for a in\
                          session.query(Database("donkey").sa_class()).all()]

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
    
    meta.create_all(engine)

    Session = sa.orm.sessionmaker(bind =engine)

    session = Session()

    fred = Donkey.tables["people"].sa_class()
    fred.name = "fred"
#    fred.age = 13

    session.add(fred)
    session.commit()

    assert "fred" in [a.name for a in\
                      session.query(Database("donkey").sa_class()).all()]


