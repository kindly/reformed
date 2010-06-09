from reformed.search import  QueryFromStringParam, Search
from reformed.resultset import ResultSet
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

        search = Search(self.Donkey, "people", self.session)
        query = QueryFromStringParam(search, "donkey.name = ? and name in ({moo}, ?, {poo})",
                                   pos_args = ["pop", "pooop"],
                                   named_args = {"moo": "cow", "poo": "man"})


        assert len(query.expressions) == 2
        assert query.expressions[0].pos == 0 
        assert query.expressions[1].pos == 20


        assert query.expressions[0].param_values == ["pop"]
        assert query.expressions[1].param_values == ['cow', 'pooop', 'man']

        search = Search(self.Donkey, "people", self.session)
        query = QueryFromStringParam(search, 
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



        query.sa_query = search.search_base
        join_tree = query.make_join_tree()
        query.recurse_join_tree(join_tree)

        expression = query.expressions[0].make_sa_expression(search, "people")
        expression = query.expressions[3].make_sa_expression(search, "people")

        assert query.expressions[0].parsed_values == [u'yes', u'pop']
        assert query.expressions[3].parsed_values == [False]

        search = Search(self.Donkey, "people", self.session)
        query = QueryFromStringParam(search, 
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

        query.sa_query = search.search_base
        join_tree = query.make_join_tree()
        query.recurse_join_tree(join_tree)

        expression = query.expressions[0].make_sa_expression(search, "people")
        expression = query.expressions[3].make_sa_expression(search, "people")

        assert query.expressions[0].parsed_values == [u'yes', u'pop']
        assert query.expressions[3].parsed_values == [False]

        search = Search(self.Donkey, "people", self.session)
        query = QueryFromStringParam(search, 
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

        query.sa_query = search.search_base
        join_tree = query.make_join_tree()
        query.recurse_join_tree(join_tree)

        expression = query.expressions[0].make_sa_expression(search, "people")

        assert query.expressions[0].parsed_values == [datetime.datetime(2019, 1, 1),
                                                      datetime.datetime(2009, 1, 1)] 

        expression = query.expressions[1].make_sa_expression(search, "people")

        assert query.expressions[1].parsed_values == [True] 

    def test_where(self):

        s = Search(self.Donkey, "people", self.session)

        query = QueryFromStringParam(s, """ name = ? or email.email = {} """, pos_args = ["david"], named_args = {"email.email": "poo@poo.com"})

        query.sa_query = s.search_base
        join_tree = query.make_join_tree()
        query.recurse_join_tree(join_tree)

        where = query.convert_where(query.ast[0])

        assert str(where.compile()) == "people.name = ? AND people.id IS NOT NULL OR email_1.email = ? AND email_1.id IS NOT NULL"
        assert where.compile().params == {u'email_2': 'poo@poo.com', u'name_1': 'david'}

        s = Search(self.Donkey, "people", self.session)

        query = QueryFromStringParam(s, """ name = ? or not (email.email < {} and donkey.name = ?)  """, pos_args = ["david", "fred"], named_args = {"email.email" : "poo@poo.com"})
        query.sa_query = s.search_base
        join_tree = query.make_join_tree()
        query.recurse_join_tree(join_tree)

        where = query.convert_where(query.ast[0])
        assert str(where.compile()) == "people.name = ? AND people.id IS NOT NULL OR NOT ((email_1.email < ? OR email_1.id IS NULL) AND donkey_1.name = ? AND donkey_1.id IS NOT NULL)"
        assert where.compile().params == {u'name_2': 'fred', u'email_2': 'poo@poo.com', u'name_1': 'david'}


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

    def test_search_custom(self):

        search = Search(self.Donkey, "people", self.session, "id>0", extra_inner = ["email>email"])

        assert str(search.search()) ==  """SELECT people.town AS people_town, people.name AS people_name, people.country AS people_country, people._version AS people__version, people.gender_id AS people_gender_id, people._modified_by AS people__modified_by, people._core_entity_id AS people__core_entity_id, people.postcode AS people_postcode, people._modified_date AS people__modified_date, people.over_18_id AS people_over_18_id, people.address_line_2 AS people_address_line_2, people.address_line_3 AS people_address_line_3, people.address_line_1 AS people_address_line_1, people.id AS people_id, email_1.active_email AS email_1_active_email, email_1._version AS email_1__version, email_1._modified_by AS email_1__modified_by, email_1._modified_date AS email_1__modified_date, email_1.people_id AS email_1_people_id, email_1.email_number AS email_1_email_number, email_1.email AS email_1_email, email_1.id AS email_1_id 
FROM people JOIN email AS email_2 ON people.id = email_2.people_id LEFT OUTER JOIN email AS email_1 ON people.id = email_1.people_id 
WHERE people.id > ? AND people.id IS NOT NULL ORDER BY email_1.email"""


        search = Search(self.Donkey, "people", self.session, "id>0", extra_outer = ["gender>code", "over_18>code"])
        assert str(search.search()) == """SELECT people.town AS people_town, people.name AS people_name, people.country AS people_country, people._version AS people__version, people.gender_id AS people_gender_id, people._modified_by AS people__modified_by, people._core_entity_id AS people__core_entity_id, people.postcode AS people_postcode, people._modified_date AS people__modified_date, people.over_18_id AS people_over_18_id, people.address_line_2 AS people_address_line_2, people.address_line_3 AS people_address_line_3, people.address_line_1 AS people_address_line_1, people.id AS people_id, email_1.active_email AS email_1_active_email, email_1._version AS email_1__version, email_1._modified_by AS email_1__modified_by, email_1._modified_date AS email_1__modified_date, email_1.people_id AS email_1_people_id, email_1.email_number AS email_1_email_number, email_1.email AS email_1_email, email_1.id AS email_1_id 
FROM people LEFT OUTER JOIN code AS code_1 ON people.gender_id = code_1.id LEFT OUTER JOIN code AS code_2 ON people.over_18_id = code_2.id LEFT OUTER JOIN email AS email_1 ON people.id = email_1.people_id 
WHERE people.id > ? AND people.id IS NOT NULL ORDER BY email_1.email"""


    def test_result_set_get(self):

        search = Search(self.Donkey, "people", self.session, "id=1")
        resultset = ResultSet(search)
        resultset.collect()
        assert resultset.get("name") == "david"

        search = Search(self.Donkey, "people", self.session, "id=1", extra_inner = ["modified_by>user"], extra_outer = ["gender>code", "over_18>code"])
        resultset = ResultSet(search)
        resultset.collect()
        assert resultset.get("modified_by>user.name") == "admin"
        assert resultset.get("name") == "david"
        assert resultset.get("gender>code.name") is None
        assert resultset.get("over_18>code.name") is None











