import donkey_test
from reformed.search import *
from nose.tools import assert_raises,raises
from reformed.custom_exceptions import *
from reformed.data_loader import FlatFile
import yaml
from sqlalchemy.sql import not_, or_
import logging

#sqlhandler = logging.FileHandler("sql.log")
#sqllogger = logging.getLogger('sqlalchemy.engine')
#sqllogger.setLevel(logging.info)
#sqllogger.addHandler(sqlhandler)

class test_search(donkey_test.test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, test_search).set_up_inserts()

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



    def test_conjunctions(self):

        s = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        assert str(Conjunction("not", "or", [t.people.name <> "poo", [t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10]], search = s)) ==\
                "and <and not <(True, 'name', 'ne'), or not <(True, 'email', 'like_op'), (True, 'amount', 'gt')>>>"

        assert str(Conjunction("not", [t.people.name <> "poo", [t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10]], search = s)) ==\
                "and <or not <(True, 'name', 'ne'), or not <(True, 'email', 'like_op'), (True, 'amount', 'gt')>>>"

        assert str(Conjunction("not", [t.people.name <> "poo", "not", [t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10]], search = s)) ==\
                "and <or not <(True, 'name', 'ne'), and <(False, 'email', 'like_op'), (False, 'amount', 'gt')>>>"

        assert str(Conjunction("not", [t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10]], search = s)) ==\
                "and <or not <(True, 'name', 'ne'), and <(True, 'email', 'like_op'), (False, 'amount', 'gt')>>>"

        assert str(Conjunction("or", [t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10]], search = s)) ==\
                "and <or <(False, 'name', 'ne'), or not <(False, 'email', 'like_op'), (True, 'amount', 'gt')>>>"

        assert str(Conjunction("or", [t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10, t.donkey]], search = s)) ==\
                "and <or <(False, 'name', 'ne'), or not <(False, 'email', 'like_op'), (True, 'amount', 'gt'), (True, 'donkey', 'eq')>>>"

        assert str(Conjunction("or", [t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10, "not", t.donkey]], search = s)) ==\
                "and <or <(False, 'name', 'ne'), or not <(False, 'email', 'like_op'), (True, 'amount', 'gt'), (False, 'donkey', 'ne')>>>"
        
        assert Conjunction("or", [t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10]], search = s).tables_covered_by_this ==\
                set([])

        assert Conjunction(t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10], type ="or", search = s).tables_covered_by_this==\
                set(['donkey_sponsership', 'email', 'people'])

        assert Conjunction(t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10], type ="or", search = s).inner_joins==\
                set(['email'])

        assert Conjunction(t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10], type ="or", search = s).outer_joins==\
                set(['donkey_sponsership', 'people'])

        assert Conjunction(t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount < 10], type ="or", search = s).inner_joins==\
                set(['email', 'donkey_sponsership'])

        assert Conjunction(t.people.name == "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount < 10], type ="or", search = s).inner_joins==\
                set(['donkey_sponsership', 'email', 'people'])


        assert Conjunction("or", [t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10, t.donkey]], search = s).inner_joins ==\
                set(["email"])

        assert Conjunction("or", [t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10, t.donkey]], search = s).outer_joins ==\
                set(['donkey_sponsership', 'people', 'donkey'])

        assert Conjunction("or", [t.people.name <> "poo", "not", ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10, "not", t.donkey]], search = s).inner_joins ==\
                set(["email", "donkey"])
    
    def test_where_clause(self):

        s = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        print SingleQuery(s,
                               Conjunction("or", [t.people.name <> "poo", "not",
                                              ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10, "not", t.donkey]], search = s)
                                               ).where.compile()


        assert str(SingleQuery(s,
                               Conjunction("or", [t.people.name <> "poo", "not",
                                              ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10, "not", t.donkey]], search = s)
                                               ).where.compile()) == "people.name != ? OR people.name IS NULL OR email.email LIKE ? OR donkey_sponsership.amount <= ? OR donkey_sponsership.amount IS NULL OR donkey.id IS NOT NULL"

        assert str(SingleQuery(s,
                               Conjunction("not" , "or", [t.people.name <> "poo", "not",
                                              ["not", t.email.email.like("poo2%"), t.donkey_sponsership.amount > 10, "not", t.donkey]], search = s)
                                               ).where.compile()) == "people.name = ? AND (email.email NOT LIKE ? OR email.email IS NULL) AND donkey_sponsership.amount > ? AND donkey.id IS NULL"

    def test_single_query(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        session = self.Donkey.Session()

        base_query = session.query(t.people.id)

        people_class = self.Donkey.get_class("people")
        email_class = self.Donkey.get_class("email")

        assert set(SingleQuery(search, t.people.name < u"popp02").add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).filter(people_class.name < u"popp02").all())) == set()

        assert set(SingleQuery(search, t.people.name < u"popp02", t.email.email.like(u"popi%")).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).join(["email"]).filter(and_(people_class.name < u"popp02", email_class.email.like(u"popi%"))).all())) == set()

        assert set(SingleQuery(search, t.people.name < u"popp02", "not", t.email.email.like(u"popi%")).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(and_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%"))))).all())) == set()

        assert set(SingleQuery(search, 
                               "or",
                                   [t.people.name < u"popp02",
                                   "not", t.email.email.like(u"popi%")]
                              ).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(or_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%"))))).all())) == set()

        assert set(SingleQuery(search, 
                               "not" ,"or",
                                   [t.people.name < u"popp02",
                                   "not", t.email.email.like(u"popi%")]
                              ).add_conditions(base_query).all()).symmetric_difference(
               set(session.query(people_class.id).outerjoin(["email"]).\
                   filter(not_(or_(people_class.name < u"popp02", or_(email_class.email == None, not_(email_class.email.like(u"popi%")))))).all())) == set()

    def test_zzzz_search_with_single_query(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t
        session = self.session
        search.add_query(t.people.name < u"popp02", "not", t.email.email.like(u"popi%"))

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

        search.add_query(t.people.name < u"popp005",  t.email.email.like(u"popi%"))

        search.add_query(t.donkey.name.in_([u"poo", u"fine"]))

        for line in search.table_paths_list:
            print line

        assert len(search.search().all()) == 6

        search.add_query(t.donkey_sponsership.amount > 248)
                         
        assert len(search.search().all()) == 8


    def test_search_with_joined_exclude(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        search.add_query(t.people.name < u"popp007", t.people.name <>  u"david" )

        search.add_query(t.email.email.like(u"popi%"), exclude = True)

        assert len(search.search().all()) == 4

        search.add_query(t.donkey_sponsership.amount < 3, exclude = True)

        assert len(search.search().all()) == 3

        search.add_query(t.donkey_sponsership.amount.between(11,13))

        assert len(search.search().all()) == 6

        search.add_query(t.donkey_sponsership.amount.between(15, 19))

        assert len(search.search().all()) == 11

        search.add_query(t.donkey_sponsership.amount.between(15, 16), exclude = True)
        search.add_query(t.donkey_sponsership.amount.between(17, 18), exclude = True)

        assert len(search.search().all()) == 7

        search.add_query(t.donkey_sponsership.amount.between(15, 19))

        assert len(search.search().all()) == 11



    def test_z_search_with_except_exclude(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        search.add_query(t.people.name < u"popp007", t.people.name <>  u"david" )

        search.add_query(t.email.email.like(u"popi%"), exclude = True)

        assert len(search.search(exclude_mode = "except").all()) == 4

        search.add_query(t.donkey_sponsership.amount < 3, exclude = True)

        assert len(search.search(exclude_mode = "except").all()) == 3

        search.add_query(t.donkey_sponsership.amount.between(11,13))

        assert len(search.search(exclude_mode = "except").all()) == 6

        search.add_query(t.donkey_sponsership.amount.between(15, 19))

        assert len(search.search(exclude_mode = "except").all()) == 11

        search.add_query(t.donkey_sponsership.amount.between(15, 16), exclude = True)
        search.add_query(t.donkey_sponsership.amount.between(17, 18), exclude = True)

        assert len(search.search(exclude_mode = "except").all()) == 7

        search.add_query(t.donkey_sponsership.amount.between(15, 19))

        assert len(search.search(exclude_mode = "except").all()) == 11

    def test_zz_search_with_limit(self):

        search = Search(self.Donkey, "people", self.session)
        t = self.Donkey.t

        search.add_query(t.email.email.like(u"popi%"))
        search.add_query(t.people.name ==  u"david", exclude = "true")


        assert len(search.search()[0:2]) == 2
        
