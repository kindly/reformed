from columns import *
from tables import *
from database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import logging

logging.basicConfig(filename = "sql.txt")
logging.getLogger('sqlalchemy.engine').setLevel(logging.info)

class test_result_set_basic(object):

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

        self.session = self.Session()

        self.jim = self.Donkey.tables["donkey"].sa_class()
        self.jim.name = u"jim"
        self.jim.age = 13
        jim1 = self.Donkey.tables["donkey"].sa_class()
        jim1.name = u"jim1"
        jim1.age = 131
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
        davidsjim = self.Donkey.tables["donkey_sponsership"].sa_class()
        davidsjim.people = self.david
        davidsjim.donkey = self.jim
        davidsjim.amount = 50
        
        jimpic = file("jim.xcf", mode = "rb").read()
        


        jimimage = self.Donkey.tables["donkey_pics"].sa_class()
        jimimage.pic = jimpic

        self.session.add(self.david)
        self.session.add(self.jim)
        self.session.add(jim1)
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

    def tearDown(self):

        self.session.close()

    def test_get_first_last_row(self):

        results = self.Donkey.query(self.session, "donkey")
        first = results.first()
        assert first.name == "jim"

        results = self.Donkey.query(self.session, "donkey")
        last = results.last()
        assert last.name == "jim0"

    def test_get_first_last_set(self):

        results = self.Donkey.query(self.session, "donkey")
        first_set = results.first_set()
        assert [donkey.name for donkey in first_set] == [u'jim',
                                                         u'jim1',
                                                         u'jim2',
                                                         u'jim3',
                                                         u'jim4']
        
        results = self.Donkey.query(self.session, "donkey")
        last_set = results.last_set()
        assert [donkey.name for donkey in last_set] == [u'jim0']

    def test_get_next_prev_item(self):

        results = self.Donkey.query(self.session, "donkey")
        first = results.first()
        next = results.next()
        assert next.name== u"jim1"
        next2 = results.next()
        assert next2.name== u"jim2"
        prev = results.prev()
        assert prev.name== u"jim1"
        prev2 = results.prev()
        assert prev2.name== u"jim"
        prev3 = results.prev()
        assert prev3.name== u"jim"

        last = results.last()
        assert last.name== u"jim0"
        lastprev = results.prev()
        assert lastprev.name == u"jim9"
        last2 = results.next()
        assert last2.name == u"jim0"
        last3 = results.next()
        assert last3.name == u"jim0"



    def test_get_next_prev_set(self):

        results = self.Donkey.query(self.session, "donkey")
        firstset = results.first_set()
        nextset = results.next_set()

        assert [donkey.name for donkey in nextset] == [u'jim5',
                                                        u'jim6',
                                                        u'jim7',
                                                        u'jim8',
                                                        u'jim9']
        nextset2 = results.next_set()
        assert [donkey.name for donkey in nextset2] == [u'jim0']

        nextset3 = results.next_set()
        print [donkey.name for donkey in nextset3]
        assert [donkey.name for donkey in nextset3] == [u'jim0']
        

