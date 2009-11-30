from reformed.search import  QueryFromStringParam, Search
from donkey_test import test_donkey
from reformed.data_loader import FlatFile
from sqlalchemy.sql import not_, or_, and_
import datetime


class TestParserParams(test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, TestParserParams).set_up_inserts()

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

    def test_parser_params(self):

        ast = QueryFromStringParam(None, "name = {poo}", test = True).ast

        assert ast[0].params == ["poo"]

        ast = QueryFromStringParam(None, "name = {}", test = True).ast

        assert ast[0].params == ["name"]

        ast = QueryFromStringParam(None, "donkey.name = {}", test = True).ast

        assert ast[0].params == ["donkey.name"]

        ast = QueryFromStringParam(None, "donkey.name = ?", test = True).ast

        assert ast[0].params == ["?"]

        ast = QueryFromStringParam(None, "name between {poo} and {moo}", test = True).ast

        assert ast[0].params == ["poo", "moo"]
        
        ast = QueryFromStringParam(None, "name between ? and {moo}", test = True).ast

        assert ast[0].params == ["?", "moo"]

        ast = QueryFromStringParam(None, "name in  ({moo}, ?, {poo})", test = True).ast

        assert ast[0].params == ["moo", "?", "poo"]

        ast = QueryFromStringParam(None, "donkey.name = ? and name in ({moo}, ?, {poo})", test = True).ast

        assert ast[0][0].params == ["?"]

        assert ast[0][2].pos == 20 

        query = QueryFromStringParam(None, "donkey.name = ? and name in ({moo}, ?, {poo})",
                                   pos_args = ["pop", "pooop"],
                                   named_args = {"moo": "cow", "poo": "man"})


        assert len(query.expressions) == 2
        assert query.expressions[0].pos == 0 
        assert query.expressions[1].pos == 20


        assert query.expressions[0].param_values == ["pop"]
        assert query.expressions[1].param_values == ['cow', 'pooop', 'man']

        query = QueryFromStringParam(None, 
                                   "(donkey.name between {} and ?)"
                                   "or (email.email <= {} "
                                   "and name in ({moo}, ?, {poo}))"
                                   "and donkey_sponsership.id is ?",
                                   pos_args = ["pop", "pooop", "not null"],
                                   named_args =  {"donkey.name": "yes",
                                                  "email.email": "got",
                                                  "moo": "cow",
                                                  "poo": "man"} 
                                    )


        assert query.expressions[0].param_values == ["yes", "pop"]
        assert query.expressions[1].param_values == ["got"]
        assert query.expressions[2].param_values == ["cow", "pooop", "man"]
        assert query.expressions[3].param_values == ["not null"]

        expression = query.expressions[0].make_sa_expression(self.Donkey, "people")
        expression = query.expressions[3].make_sa_expression(self.Donkey, "people")

        assert query.expressions[0].parsed_values == [u'yes', u'pop']
        assert query.expressions[3].parsed_values == [False]


        query = QueryFromStringParam(None, 
                                   "(donkey.name between {} and ?)"
                                   "or (email.email <= {} "
                                   "and name in ({moo}, ?, {poo}))"
                                   "and donkey_sponsership.id is ?",
                                   pos_args = ["pop", "pooop", "not null"],
                                   named_args =  {"donkey.name": "yes",
                                                  "email.email": "got",
                                                  "moo": "cow",
                                                  "poo": "man"} 
                                    )


        assert query.expressions[0].param_values == ["yes", "pop"]
        assert query.expressions[1].param_values == ["got"]
        assert query.expressions[2].param_values == ["cow", "pooop", "man"]
        assert query.expressions[3].param_values == ["not null"]

        expression = query.expressions[0].make_sa_expression(self.Donkey, "people")
        expression = query.expressions[3].make_sa_expression(self.Donkey, "people")

        assert query.expressions[0].parsed_values == [u'yes', u'pop']
        assert query.expressions[3].parsed_values == [False]

        query = QueryFromStringParam(None, 
                                   "(donkey._modified_date between {} and ?)"
                                   "or (email.active_email = {}"
                                   "and name in ({moo}, ?, {poo}))"
                                   "and donkey_sponsership.id is ?",
                                   pos_args = ["2009-01-01", "pooop", "not null"],
                                   named_args =  {"donkey._modified_date": "2019-01-01",
                                                  "email.active_email": "True",
                                                  "moo": "cow",
                                                  "poo": "man"} 
                                    )
        expression = query.expressions[0].make_sa_expression(self.Donkey, "people")

        assert query.expressions[0].parsed_values == [datetime.datetime(2019, 1, 1),
                                                      datetime.datetime(2009, 1, 1)] 

        expression = query.expressions[1].make_sa_expression(self.Donkey, "people")

        assert query.expressions[1].parsed_values == [True] 

    def test_where(self):

        s = Search(self.Donkey, "people", self.session)

        query = QueryFromStringParam(s, """ name = ? or email.email = {} """, pos_args = ["david"], named_args = {"email.email": "poo@poo.com"})

        where = query.convert_where(query.ast[0])

        assert str(where.compile()) == "people.name = ? AND people.id IS NOT NULL OR email.email = ? AND email.id IS NOT NULL"
        assert where.compile().params == {u'email_1': 'poo@poo.com', u'name_1': 'david'}


        query = QueryFromStringParam(s, """ name = ? or not (email.email < {} and donkey.name = ?)  """, pos_args = ["david", "fred"], named_args = {"email.email" : "poo@poo.com"})
        where = query.convert_where(query.ast[0])
        assert str(where.compile()) == "people.name = ? AND people.id IS NOT NULL OR NOT ((email.email < ? OR email.id IS NULL) AND donkey.name = ? AND donkey.id IS NOT NULL)"
        assert where.compile().params == {u'name_2': 'fred', u'email_1': 'poo@poo.com', u'name_1': 'david'}


        assert query.covering_ors == set(["email","donkey"])
        assert query.inner_joins == set(["email"])
        assert query.outer_joins == set(["donkey"])

    def test_single_query(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        session = self.Donkey.Session()

        people_class = self.Donkey.get_class("people")
        email_class = self.Donkey.get_class("email")

        base_query = session.query(t.people.id)

        assert set(QueryFromStringParam(search, 'name < ?', pos_args = ["popp02"]).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).filter(people_class.name < u"popp02").all())) == set()
              

        assert set(QueryFromStringParam(search, 'name < ? and email.email like ?', pos_args = ["popp02", "popi%"]).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).join(["email"]).filter(and_(people_class.name < u"popp02", email_class.email.like(u"popi%"))).all())) == set()

        assert set(QueryFromStringParam(search, "name < ? and not email.email like ?", pos_args = ["popp02", "popi%"]).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(and_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%"))))).all())) == set()

        assert set(QueryFromStringParam(search, "name < ? or not email.email like ?", pos_args = ["popp02", "popi%"]).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(or_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%"))))).all())) == set()

        assert set(QueryFromStringParam(search, "not (name < ? or not email.email like ?) ", pos_args = ["popp02", "popi%"]
                                  ).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(not_(or_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%")))))).all())) == set()

    def test_zzzz_search_with_single_query(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t
        session = self.session
        search.add_query('name < ? and not email.email like ?', values = ["popp02", "popi%"])

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


        search.add_query('donkey_sponsership.amount between ? and ?', values = [11,13])


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

        




