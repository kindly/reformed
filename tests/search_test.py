import donkey_test
from reformed.search import *
from nose.tools import assert_raises,raises
from reformed.custom_exceptions import *
from reformed.data_loader import FlatFile
import yaml
from sqlalchemy.sql import not_, or_
import pyparsing
import datetime
from decimal import Decimal
import logging

class test_query_from_string(donkey_test.test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, test_query_from_string).set_up_inserts()

        cls.flatfile = FlatFile(cls.Donkey,
                            "people",
                            "tests/new_people.csv",    
                            ["id",
                            "name",
                            "address_line_1",
                            "postcode",
                            "email__0__email",
                            "email__1__email",
                            "donkey_sponsership__0__amount",
                            "donkey_sponsership__0__id",
                            "donkey_sponsership__0___donkey__0__name"]
                            )
        cls.flatfile.load()

    def test_basic_query(self):

        query = QueryFromString(None, "boo.boo = 20", test = True)

        assert query.ast[0].operator == "="
        assert query.ast[0].table == "boo"
        assert query.ast[0].field == "boo"
        assert query.ast[0].value == "20"

        query = QueryFromString(None, "boo.boo like 20", test = True)
        assert query.ast[0].operator == "like"

        query = QueryFromString(None, "boo.boo between 20 and 30", test = True)

        assert query.ast[0].operator == "between"
        assert query.ast[0].value == "20"
        assert query.ast[0].value2 == "30"

        query = QueryFromString(None, "boo.boo BetWeen 20 and 30", test = True)
        assert query.ast[0].operator == "between"

        query = QueryFromString(None, """boo.boo < 'pop' """, test = True)
        assert query.ast[0].operator == "<"
        assert query.ast[0].value == "pop"

        query = QueryFromString(None, """boo.boo in ("boo*3232", foo, loo) """, test = True)
        assert query.ast[0].operator == "in"
        assert list(query.ast[0].value) == ['boo*3232', 'foo', 'loo']

        query = QueryFromString(None, """not boo = 10 and boo = 80""", test = True)
        assert query.ast[0][1] == "and"

        assert_raises(pyparsing.ParseException, QueryFromString, None, """boo = 77-54-5835""", test = True) 

        query = QueryFromString(None, """wee = 2008-05-02""", test = True)
        assert query.ast[0].value == datetime.datetime(2008,05,02)

        query = QueryFromString(None, """wee = 02/05/2008""", test = True)
        assert query.ast[0].value == datetime.datetime(2008,05,02)

        query = QueryFromString(None, """wee = 4.20""", test = True)
        assert query.ast[0].value == Decimal("4.20")

        query = QueryFromString(None, """wee is null""", test = True)
        assert query.ast[0].operator == "is"

        query = QueryFromString(None, """wee is  not null""", test = True)
        assert query.ast[0].operator == "not"

        query = QueryFromString(None, """wee < now""", test = True)
        assert query.ast[0].value.isoformat()[:20] == datetime.datetime.now().isoformat()[:20] 

        query = QueryFromString(None, """wee < now - 5 mins""", test = True)
        assert query.ast[0].value.isoformat()[:20] == (datetime.datetime.now() - datetime.timedelta(minutes = 5)).isoformat()[:20] 

        query = QueryFromString(None, """wee < now + 5 days""", test = True)
        assert query.ast[0].value.isoformat()[:20] == (datetime.datetime.now() + datetime.timedelta(days = 5)).isoformat()[:20] 

        query = QueryFromString(None, """wee < now - 5 hours""", test = True)
        assert query.ast[0].value.isoformat()[:20] == (datetime.datetime.now() - datetime.timedelta(hours = 5)).isoformat()[:20] 

    def test_gather_covering_ors(self):

        query = QueryFromString(None, """wee = 4.20""", test = True)
        assert query.covering_ors == set()

        query = QueryFromString(None, """pop.wee = 4.20 or table.wee = 10""", test = True)
        assert query.covering_ors == set(["table", "pop"])

        query = QueryFromString(None, """lam = 4 or pop.wee = 4.20 or table.wee = 10""", test = True)
        assert query.covering_ors == set(["table", "pop"])

        query = QueryFromString(None, """not (pop.wee = 4.20 or table.wee = 10)""", test = True)
        assert query.covering_ors == set()

        query = QueryFromString(None, """not (pop.wee = 4.20 and table.wee = 10)""", test = True)
        assert query.covering_ors == set(["table", "pop"])

        query = QueryFromString(None, """not (pop.wee = 4.20 and table.wee = 10 or person.pop = 9)""", test = True)
        assert query.covering_ors == set(["table", "pop", "person"])

    def test_gather_joins(self):

        query = QueryFromString(None, """pop.wee = 4.20 or table.wee = 10""", test = True)
        assert query.inner_joins == set(["table", "pop"])

        query = QueryFromString(None, """pop.wee < 4.20 or table.wee = 10""", test = True)
        assert query.inner_joins == set(["table"])
        assert query.outer_joins == set(["pop"])

        query = QueryFromString(None, """not (pop.wee < 4.20 and table.wee like ppp)""", test = True)
        assert query.inner_joins == set(["pop"])
        assert query.outer_joins == set(["table"])

        query = QueryFromString(None, """not pop.wee < 4.20 and table.wee like 'ppp'""", test = True)
        assert query.inner_joins == set(["table", "pop"])

    def test_where(self):

        s = Search(self.Donkey, "people", self.session)

        query = QueryFromString(s, """ name = david or email.email = 'poo@poo.com' """)
        where = query.convert_where(query.ast[0])
        assert str(where.compile()) == "people.name = ? AND people.id IS NOT NULL OR email.email = ? AND email.id IS NOT NULL"
        assert where.compile().params == {u'email_1': 'poo@poo.com', u'name_1': 'david'}


        query = QueryFromString(s, """ name = david or not (email.email < 'poo@poo.com' and donkey.name = "fred")  """)
        where = query.convert_where(query.ast[0])
        assert str(where.compile()) == "people.name = ? AND people.id IS NOT NULL OR NOT ((email.email < ? OR email.id IS NULL) AND donkey.name = ? AND donkey.id IS NOT NULL)"
        assert where.compile().params == {u'name_2': 'fred', u'email_1': 'poo@poo.com', u'name_1': 'david'}

    def test_single_query(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        session = self.Donkey.Session()

        people_class = self.Donkey.get_class("people")
        email_class = self.Donkey.get_class("email")

        base_query = session.query(t.people.id)

        assert set(QueryFromString(search, 'name < "popp02"').add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).filter(people_class.name < u"popp02").all())) == set()
              

        assert set(QueryFromString(search, 'name < "popp02" and email.email like "popi%"').add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).join(["email"]).filter(and_(people_class.name < u"popp02", email_class.email.like(u"popi%"))).all())) == set()

        assert set(QueryFromString(search, "name < popp02 and not email.email like 'popi%'").add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(and_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%"))))).all())) == set()

        assert set(QueryFromString(search, "name < popp02 or not email.email like 'popi%'").add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(or_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%"))))).all())) == set()

        assert set(QueryFromString(search, "not (name < popp02 or not email.email like 'popi%') "
                                  ).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(not_(or_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%")))))).all())) == set()

    def test_zzzz_search_with_single_query(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t
        session = self.session
        search.add_query('name < popp02 and not email.email like "popi%"')

        people_class = self.Donkey.get_class(u"people")
        email_class = self.Donkey.get_class(u"email")

        assert set(search.search().all()).symmetric_difference( 
               set(session.query(people_class).outerjoin(["email"]).\
                   filter(and_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%"))))).all())) == set()

        assert len(search.search()[0:15]) == 15


    def test_search_with_union(self):

        search = Search(self.Donkey, u"people", self.session)
        t = self.Donkey.t
        session = self.session

        search.add_query('name < popp005 and email.email like "popi%"')

        search.add_query('donkey.name in (poo, fine)')


        assert len(search.search().all()) == 6

        search.add_query('donkey_sponsership.amount > 248')
                         
        assert len(search.search().all()) == 8


    def test_search_with_joined_exclude(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        search.add_query('name < popp007 and name <> david' )

        search.add_query('email.email like "popi%"', exclude = True)

        assert len(search.search().all()) == 4

        search.add_query('donkey_sponsership.amount < 3', exclude = True)

        assert len(search.search().all()) == 3

        search.add_query('donkey_sponsership.amount between 11 and 13')

        assert len(search.search().all()) == 6

        search.add_query('donkey_sponsership.amount between 15 and 19')

        assert len(search.search().all()) == 11

        search.add_query('donkey_sponsership.amount between 15 and 16', exclude = True)
        search.add_query('donkey_sponsership.amount between 17 and 18', exclude = True)

        assert len(search.search().all()) == 7

        search.add_query('donkey_sponsership.amount between 15 and 19')

        assert len(search.search().all()) == 11



    def test_z_search_with_except_exclude(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        search.add_query('name < popp007 and name <>  david' )

        search.add_query('email.email like "popi%"', exclude = True)

        assert len(search.search(exclude_mode = "except").all()) == 4

        search.add_query('donkey_sponsership.amount < 3', exclude = True)

        assert len(search.search(exclude_mode = "except").all()) == 3

        search.add_query('donkey_sponsership.amount between 11 and 13')

        assert len(search.search(exclude_mode = "except").all()) == 6

        search.add_query('donkey_sponsership.amount between 15 and 19')

        assert len(search.search(exclude_mode = "except").all()) == 11

        search.add_query('donkey_sponsership.amount between 15 and 16', exclude = True)
        search.add_query('donkey_sponsership.amount between 17 and 18', exclude = True)

        assert len(search.search(exclude_mode = "except").all()) == 7

        search.add_query('donkey_sponsership.amount between 15 and 19')

        assert len(search.search(exclude_mode = "except").all()) == 11


    def test_zz_search_with_limit(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        search.add_query('email.email like "popi%"')
        search.add_query('people.name = "david"', exclude = "true")

        assert len(search.search()[0:2]) == 2

        

