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

    def teerst_basic_query(self):

        query = QueryFromString(None, "boo.boo = 20")

        assert query.ast[0].operator == "="
        assert query.ast[0].table == "boo"
        assert query.ast[0].field == "boo"
        assert query.ast[0].value == "20"

        query = QueryFromString(None, "boo.boo like 20")
        assert query.ast[0].operator == "like"

        query = QueryFromString(None, "boo.boo between 20 and 30")

        assert query.ast[0].operator == "between"
        assert query.ast[0].value == "20"
        assert query.ast[0].value2 == "30"

        query = QueryFromString(None, "boo.boo BetWeen 20 and 30")
        assert query.ast[0].operator == "between"

        query = QueryFromString(None, """boo.boo < 'pop' """)
        assert query.ast[0].operator == "<"
        assert query.ast[0].value == "pop"

        query = QueryFromString(None, """boo.boo in ("boo*3232", foo, loo) """)
        assert query.ast[0].operator == "in"
        assert list(query.ast[0].value) == ['boo*3232', 'foo', 'loo']

        query = QueryFromString(None, """not boo = 10 and boo = 80""")
        assert query.ast[0][1] == "and"

        assert_raises(pyparsing.ParseException, QueryFromString, None, """boo = 77-54-5835""") 

        query = QueryFromString(None, """wee = 2008-05-02""")
        assert query.ast[0].value == datetime.datetime(2008,05,02)

        query = QueryFromString(None, """wee = 02/05/2008""")
        assert query.ast[0].value == datetime.datetime(2008,05,02)

        query = QueryFromString(None, """wee = 4.20""")
        assert query.ast[0].value == Decimal("4.20")

    def test_gather_covering_ors(self):

        query = QueryFromString(None, """wee = 4.20""")
        assert query.covering_ors == set()

        query = QueryFromString(None, """pop.wee = 4.20 or table.wee = 10""")
        assert query.covering_ors == set(["table", "pop"])

        query = QueryFromString(None, """lam = 4 or pop.wee = 4.20 or table.wee = 10""")
        assert query.covering_ors == set(["table", "pop"])

        query = QueryFromString(None, """not (pop.wee = 4.20 or table.wee = 10)""")
        assert query.covering_ors == set()

        query = QueryFromString(None, """not (pop.wee = 4.20 and table.wee = 10)""")
        assert query.covering_ors == set(["table", "pop"])

        query = QueryFromString(None, """not (pop.wee = 4.20 and table.wee = 10 or person.pop = 9)""")
        assert query.covering_ors == set(["table", "pop", "person"])

    def test_gather_joins(self):

        query = QueryFromString(None, """pop.wee = 4.20 or table.wee = 10""")
        assert query.inner_joins == set(["table", "pop"])

        query = QueryFromString(None, """pop.wee < 4.20 or table.wee = 10""")
        assert query.inner_joins == set(["table"])
        assert query.outer_joins == set(["pop"])

        query = QueryFromString(None, """not (pop.wee < 4.20 and table.wee like ppp)""")
        assert query.inner_joins == set(["pop"])
        assert query.outer_joins == set(["table"])

        query = QueryFromString(None, """not pop.wee < 4.20 and table.wee like 'ppp'""")
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


