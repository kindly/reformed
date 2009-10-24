from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
import reformed.custom_exceptions
from reformed.data_loader import SingleRecord
from sqlalchemy import create_engine
from reformed.util import get_table_from_instance, create_data_dict, make_local_tables, get_all_local_data, load_local_data
import datetime
from decimal import Decimal
import formencode as fe
import yaml
import os
import logging

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.debug)
sqllogger.addHandler(sqlhandler)

class test_donkey(object):

    @classmethod
    def setUpClass(cls):
        if not hasattr(cls, "engine"):
            cls.engine = create_engine('sqlite:///:memory:', echo = False)
            #cls.engine = create_engine('sqlite:///:memory:')
        
#        cls.engine = create_engine('mysql://localhost/test_donkey', echo = True)
        cls.meta = sa.MetaData()
        cls.Sess = sa.orm.sessionmaker(bind =cls.engine, autoflush = False)
        cls.Donkey = Database("Donkey", 
                            Table("people",
                                  Text("name", mandatory = True, length = 30),
                                  Address("supporter_address"),
                                  OneToMany("email","email", 
                                            order_by = "email",
                                            eager = True, 
                                            cascade = "all, delete-orphan"),
                                  OneToMany("donkey_sponsership",
                                            "donkey_sponsership"),
                                  OneToOne("contact_summary",
                                           "contact_summary"),
                                  OneToMany("transactions",
                                           "transactions"),
                                  entity = True,
                                  summary_fields = "name,address_line_1,postcode"
                                  ),
                            Table("contact_summary",
                                  SumDecimal("total_amount", "transactions.amount", base_level = "people"),
                                  AddRow("new_row", "people", initial_event = True),
                                  CountRows("transaction_count", "transactions.id", base_level = "people"),
                                  MaxDate("membership", "membership", base_level = "people"),
                                  CopyText("email", "email", 
                                           base_level = "people", 
                                           fields = "email,email", 
                                           update_when_flag = "active_email",
                                           counter = "email_number"),
                                  CopyTextAfter("address", "people",
                                                base_level = "people",
                                                fields = "address_line_1,postcode",
                                                changed_flag = "modified"),
                                  Boolean("modified", default = True),
                                  logged = False, validated = False
                                 ),
                            Table("transactions",
                                   Date("date"),
                                   Money("amount"),
                                   Text("Type")),
                            Table("email",
                                  Email("email"),
                                  Counter("email_number", base_level = "people"),
                                  Boolean("active_email", default = True)
                                 ),
                            Table("donkey", 
                                  Text("name", validation = '__^[a-zA-Z0-9]*$'),
                                  Integer("age", validation = 'Int'),
                                  TextLookupValidated("donkey_type", "donkey_types.donkey_type", filter_field = "donkey_type_type", filter_value = "looks"),
                                  OneToOne("donkey_pics","donkey_pics",
                                           many_side_not_null = False,
                                           ),
                                  OneToMany("donkey_sponsership",
                                            "donkey_sponsership"),
                                  Index("idx_name", "name"),
                                  summary_fields = "name,age",
                                  entity = True
                                 ),
                            Table("donkey_types",
                                  Text("donkey_type"),
                                  Text("donkey_type_type")),
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
                             Table("membership",
                                   DateTime("start_date", mandatory = True),
                                   DateTime("end_date" ),
                                   ManyToOne("_core_entity", "_core_entity"),
                                   CheckNoTwoNulls("val_duplicate_membership", parent_table = "_core_entity", field = "end_date"),  
                                  ),
                             Table("_core_lock",
                                  Text("table_name"),
                                  Integer("row_id"),
                                  DateTime("date"),
                                  UniqueConstraint("unique", "table_name,row_id,date"),
                                  logged = False),
                        metadata = cls.meta,
                        engine = cls.engine,
                        session = cls.Sess,
                        entity = True
                        )

        cls.Donkey.add_table(Table("category",
                             Text("category_name"),
                             Text("category_description"),
                             Text("category_type"),
                             OneToMany("sub_category", "sub_category", many_side_mandatory = True),
                             primary_key = 'category_name')
                            )

        cls.Donkey.add_table(Table("sub_category",
                             Text("sub_category_name"),
                             Text("sub_category_description"),
                             OneToMany("sub_sub_category", "sub_sub_category", many_side_mandatory = True),
                             primary_key = 'category_name,sub_category_name')
                            )

        cls.Donkey.add_table(Table("sub_sub_category",
                             Text("sub_sub_category_name"),
                             Text("sub_sub_category_description"),
                             OneToMany('entity_categories', 'entity_categories',
                                       backref = 'category'),
                             primary_key = 'category_name,sub_category_name,'
                                           'sub_sub_category_name')
                            )

        cls.Donkey.add_table(Table("entity_categories",
                             DateTime("start_date"),
                             DateTime("end_date"),
                             Counter("category_number", base_level = "_core_entity"),
                             ManyToOne("entity", "_core_entity",
                                       backref = "categories"),
                             CheckOverLappingDates("check_dates", parent_table = "_core_entity"))
                            )


        cls.Donkey.persist()
        cls.session = cls.Donkey.Session()

        cls.set_up_inserts()

    @classmethod
    def set_up_inserts(cls):

        cls.jim = cls.Donkey.tables["donkey"].sa_class()
        cls.jim.name = u"jim"
        cls.jim.age = 13
        cls.jim1 = cls.Donkey.tables["donkey"].sa_class()
        cls.jim1.name = u"jim1"
        cls.jim1.age = 131
        jim2 = cls.Donkey.tables["donkey"].sa_class()
        jim2.name = u"jim2"
        jim2.age = 132
        jim3 = cls.Donkey.tables["donkey"].sa_class()
        jim3.name = u"jim3"
        jim3.age = 133
        jim4 = cls.Donkey.tables["donkey"].sa_class()
        jim4.name = u"jim4"
        jim4.age = 142
        jim5 = cls.Donkey.tables["donkey"].sa_class()
        jim5.name = u"jim5"
        jim5.age = 135
        jim6 = cls.Donkey.tables["donkey"].sa_class()
        jim6.name = u"jim6"
        jim6.age = 136
        jim7 = cls.Donkey.tables["donkey"].sa_class()
        jim7.name = u"jim7"
        jim7.age = 137
        jim8 = cls.Donkey.tables["donkey"].sa_class()
        jim8.name = u"jim8"
        jim8.age = 138
        jim9 = cls.Donkey.tables["donkey"].sa_class()
        jim9.name = u"jim9"
        jim9.age = 132
        jim0 = cls.Donkey.tables["donkey"].sa_class()
        jim0.name = u"jim0"
        jim0.age = 102
        cls.david = cls.Donkey.tables["people"].sa_class()
        cls.david.name = u"david"
        cls.david.address_line_1 = u"43 union street"
        cls.david.postcode = u"es388"
        davidsjim = cls.Donkey.tables["donkey_sponsership"].sa_class()
        davidsjim._people = cls.david
        davidsjim._donkey = cls.jim
        davidsjim.amount = 50
        
        jimpic = file("tests/jim.xcf", mode = "rb").read()
        
        jimimage = cls.Donkey.tables["donkey_pics"].sa_class()
        jimimage.donkey = cls.jim
        jimimage.pic = jimpic

        cls.session.add(cls.david)
        cls.session.add(cls.jim)
        cls.session.add(cls.jim1)
        cls.session.add(jim2)
        cls.session.add(jim3)
        cls.session.add(jim4)
        cls.session.add(jim5)
        cls.session.add(jim6)
        cls.session.add(jim7)
        cls.session.add(jim8)
        cls.session.add(jim9)
        cls.session.add(jim0)
        cls.session.add(davidsjim)
        cls.session.add(jimimage)

        cls.david2 = cls.Donkey.tables["people"].sa_class()
        cls.david2.name = u"david"
        cls.david2.address_line_1 = u""
        cls.david_logged = get_table_from_instance(cls.david, cls.Donkey).logged_instance(cls.david)
        cls.session.add(cls.david_logged)
        cls.session.commit()

        donkey_type1 = cls.Donkey.get_instance("donkey_types")
        donkey_type1.donkey_type = u"hairy"
        donkey_type1.donkey_type_type = u"looks"
        donkey_type2 = cls.Donkey.get_instance("donkey_types")
        donkey_type2.donkey_type = u"smooth"
        donkey_type2.donkey_type_type = u"looks"
        donkey_type3 = cls.Donkey.get_instance("donkey_types")
        donkey_type3.donkey_type = u"pooey"
        donkey_type3.donkey_type_type = u"smell"

        cls.session.add(donkey_type1)
        cls.session.add(donkey_type2)
        cls.session.add(donkey_type3)
        cls.session.commit()
        
    @classmethod
    def tearDownClass(cls):

        cls.session.close()
        cls.Donkey.job_scheduler.threadpool.wait()


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
        

    def test_logged_attribute(self):

        assert self.david_logged.name == u"david"
        assert self.david_logged.address_line_1 == u"43 union street"
        assert self.david_logged.postcode == u"es388"


    def test_table_paths(self):

        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey")] == ["donkey", "manytoone", []]
        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey", "donkey_pics",)] == ["donkey_pics", "onetoone", []]
        assert self.Donkey.tables["donkey"].paths[("donkey_sponsership", "_people", "email")] == ["email", "onetomany", []]

    def test_z_make_table_paths(self):

        people = self.Donkey.tables["people"]
        people.paths = None
        people.make_paths()

        #assert self.Donkey.aliases == {} 

    def test_create_data_dict(self):

        results = self.session.query(self.Donkey.tables["donkey"].sa_class)[:2]
        print create_data_dict(results) 
        assert create_data_dict(results) == {1: {'donkey.age': 13, 'donkey.donkey_type': None, 'donkey.name': u'jim'}, 2: {'donkey.age': 131, 'donkey.donkey_type': None, 'donkey.name': u'jim1'}}

        results2 = self.session.query(self.Donkey.tables["donkey"].sa_class).first()
        print create_data_dict(results2) 
        assert create_data_dict(results2) == {1: {'donkey.age': 13, 'donkey.donkey_type': None, 'donkey.name': u'jim'}}

    def test_create_local_data(self):

        result = self.session.query(self.Donkey.tables["donkey_sponsership"].sa_class).first()

        print get_all_local_data(result)


        assert get_all_local_data(result) == {'contact_summary.people_id': 1, 'contact_summary.transaction_count': 0, 'people.name': u'david', '__table': 'donkey_sponsership', 'contact_summary.membership': None, 'donkey_pics.pic_name': None, 'contact_summary.modified': True, 'contact_summary.email': None, 'contact_summary.address': u'43 union street es388', 'donkey_sponsership.donkey_id': 1, 'people.town': None, 'donkey_sponsership.giving_date': None, 'people.postcode': u'es388', 'donkey_sponsership.people_id': 1, 'people.country': None, 'people.address_line_1': u'43 union street', 'people.address_line_2': None, 'people.address_line_3': None, 'contact_summary.total_amount': Decimal('0'), 'donkey_sponsership.amount': Decimal('50'), 'donkey_pics.pic': None, 'donkey.donkey_type': None, 'donkey.age': 13, 'donkey_pics.donkey_id': None, 'donkey.name': u'jim'} 

    def test_local_tables(self):
        

        assert make_local_tables(self.Donkey.tables["people"].paths) == [{'_core_entity': ('_entity',), 'contact_summary': ('contact_summary',)}, {'transactions': ('transactions',), 'donkey_sponsership': ('donkey_sponsership',), 'entity_categories': ('_entity', 'categories'), 'membership': ('_entity', '_membership'), 'relation': ('_entity', 'relation'), 'email': ('email',)}] 


        assert make_local_tables(self.Donkey.tables["donkey"].paths) == [{'_core_entity': ('_entity',), 'donkey_pics': ('donkey_pics',)}, {'entity_categories': ('_entity', 'categories'), 'membership': ('_entity', '_membership'), 'relation': ('_entity', 'relation'), 'donkey_sponsership': ('donkey_sponsership',)}] 
        

        print self.Donkey.tables["relation"].local_tables 
        assert self.Donkey.tables["relation"].local_tables == {'donkey': ('__core_entity', 'donkey'), 'relation_donkey': ('_core_entity', 'donkey'), 'people': ('__core_entity', 'people'), 'relation_contact_summary': ('_core_entity', 'people', 'contact_summary'), 'donkey_pics': ('__core_entity', 'donkey', 'donkey_pics'), 'contact_summary': ('__core_entity', 'people', 'contact_summary'), '_core_entity': ('__core_entity',), 'relation_people': ('_core_entity', 'people'), 'relation__core_entity': ('_core_entity',), 'relation_donkey_pics': ('_core_entity', 'donkey', 'donkey_pics')} 

        print self.Donkey.tables["relation"].one_to_many_tables

        assert self.Donkey.tables["relation"].one_to_many_tables == {'transactions': ('__core_entity', 'people', 'transactions'), 'relation_transactions': ('_core_entity', 'people', 'transactions'), 'relation_entity_categories': ('_core_entity', 'categories'), 'donkey_sponsership': ('__core_entity', 'donkey', 'donkey_sponsership'), 'entity_categories': ('__core_entity', 'categories'), 'membership': ('__core_entity', '_membership'), 'relation_membership': ('_core_entity', '_membership'), 'relation_relation': ('_core_entity', 'relation'), 'relation_donkey_sponsership': ('_core_entity', 'people', 'donkey_sponsership'), 'relation_email': ('_core_entity', 'people', 'email'), 'email': ('__core_entity', 'people', 'email')}
        
    def test_zz_add_local(self):

        assert_raises(formencode.Invalid, load_local_data, self.Donkey, {"__table": "people",
                                      "people.address_line_1" : "poo1010101",
                                      "people.address_line_2" : "poop"})
        try:
            load_local_data(self.Donkey, {"__table": "people",
                                      "people.address_line_1" : "poo1010101",
                                      "people.address_line_2" : "poop"})
        except formencode.Invalid, e:
            assert str(e.error_dict) == """{'people.postcode': Invalid(u'Please enter a value',), 'people.name': Invalid(u'Please enter a value',)}"""


        assert_raises(formencode.Invalid, load_local_data, self.Donkey, {"__table": "donkey_sponsership",
                                                                         "donkey_sponsership.amount" : 70,                                   
                                      "people.address_line_1" : "poo1010101",
                                      "people.address_line_2" : "poop"})

        try:
            load_local_data(self.Donkey, {"__table": "donkey_sponsership",
                                          "donkey_sponsership.amount" : 70,                                   
                                          "donkey.age" : u"poo",                                   
                                      "people.address_line_1" : u"poo1010101",
                                      "people.address_line_2" : u"poop"})
        except formencode.Invalid, e:
            assert str(e.error_dict) == r"""{'donkey.age': Invalid(u'Please enter an integer value\nPlease enter an integer value',), 'people.postcode': Invalid(u'Please enter a value',), 'people.name': Invalid(u'Please enter a value',)}"""

            assert str(e.error_dict["donkey.age"].error_list) == "[Invalid(u'Please enter an integer value',), Invalid(u'Please enter an integer value',)]"


        load_local_data(self.Donkey, {"__table": u"donkey_sponsership",
                                      "donkey_sponsership.amount" : 711110,                                   
                                      "donkey.age" : 12,                                   
                                      "people.name" : u"fred",
                                      "people.postcode" : u"fred",
                                      "people.address_line_1" : u"poo1010101",
                                      "people.address_line_2" : u"poop"})

        a = self.session.query(self.Donkey.t.donkey_sponsership).filter_by(amount = 711110).one()


        print get_all_local_data(a)
        assert get_all_local_data(a) == {'contact_summary.people_id': 2, 'contact_summary.transaction_count': 0, 'people.name': u'fred', '__table': 'donkey_sponsership', 'contact_summary.membership': None, 'donkey_pics.pic_name': None, 'contact_summary.modified': True, 'contact_summary.email': None, 'contact_summary.address': u'poo1010101 fred', 'donkey_sponsership.donkey_id': 12, 'people.town': None, 'donkey_sponsership.giving_date': None, 'people.postcode': u'fred', 'donkey_sponsership.people_id': 2, 'people.country': None, 'people.address_line_1': u'poo1010101', 'people.address_line_2': u'poop', 'people.address_line_3': None, 'contact_summary.total_amount': Decimal('0'), 'donkey_sponsership.amount': Decimal('711110'), 'donkey_pics.pic': None, 'donkey.donkey_type': None, 'donkey.age': 12, 'donkey_pics.donkey_id': None, 'donkey.name': None}
        
    def test_import_catagory_data(self):

        load_local_data(self.Donkey, {"__table": u"sub_sub_category",
                                      "category.category_name": u"a",
                                      "category.category_description": u"this is a",
                                      "category.category_type": u"wee",
                                      "sub_category.sub_category_name": u"ab",
                                      "sub_category.sub_category_description": u"this is ab",
                                      "sub_sub_category.sub_sub_category_name": u"abc",
                                      "sub_sub_category.sub_sub_category_description": u"this is abc"}
                       )

        results = self.session.query(self.Donkey.t.sub_sub_category).all()

        assert [get_all_local_data(a) for a in results] == [{"__table": u"sub_sub_category", 'sub_category.sub_category_name': u'ab', 'sub_sub_category.sub_sub_category_name': u'abc', 'category.category_name': u'a', 'category.category_description': u'this is a', 'sub_category.sub_category_description': u'this is ab', 'category.category_type': u'wee', 'sub_sub_category.sub_sub_category_description': u'this is abc', 'sub_sub_category.sub_category_name': u'ab', 'sub_sub_category.category_name': u'a', 'sub_category.category_name': u'a'}]

        
        load_local_data(self.Donkey, {"__table": u"sub_sub_category",
                                      "category.category_name": u"a",
                                      "sub_category.sub_category_name": u"ac",
                                      "sub_category.sub_category_description": u"this is ac",
                                      "sub_sub_category.sub_sub_category_name": u"acc",
                                      "sub_sub_category.sub_sub_category_description": u"this is acc"}
                       )

        results = self.session.query(self.Donkey.t.sub_sub_category).all()

        assert [get_all_local_data(a) for a in results] == [{"__table": u"sub_sub_category",'sub_category.sub_category_name': u'ab', 'sub_sub_category.sub_sub_category_name': u'abc', 'category.category_name': u'a', 'category.category_description': u'this is a', 'sub_category.sub_category_description': u'this is ab', 'category.category_type': u'wee', 'sub_sub_category.sub_sub_category_description': u'this is abc', 'sub_sub_category.sub_category_name': u'ab', 'sub_sub_category.category_name': u'a', 'sub_category.category_name': u'a'}, {"__table": u"sub_sub_category", 'sub_category.sub_category_name': u'ac', 'sub_sub_category.sub_sub_category_name': u'acc', 'category.category_name': u'a', 'category.category_description': u'this is a', 'sub_category.sub_category_description': u'this is ac', 'category.category_type': u'wee', 'sub_sub_category.sub_sub_category_description': u'this is acc', 'sub_sub_category.sub_category_name': u'ac', 'sub_sub_category.category_name': u'a', 'sub_category.category_name': u'a'}]



        assert_raises(custom_exceptions.InvalidData,load_local_data,
                      self.Donkey,
                      {"__table": u"sub_sub_category",
                                      "category.category_name": u"b",
                                      "sub_category.category_name": u"a",
                                      "sub_category.sub_category_name": u"ac",
                                      "sub_category.sub_category_description": u"this is ac",
                                      "sub_sub_category.sub_sub_category_name": u"acd",
                                      "sub_sub_category.sub_sub_category_description": u"this is acc"}
                       )

        load_local_data(self.Donkey, {"__table": u"sub_sub_category",
                                      "category.id": 1,
                                      "sub_category.id": 2,
                                      "sub_sub_category.sub_sub_category_name": u"acd",
                                      "sub_sub_category.sub_sub_category_description": u"this is acc"}
                       )

        results = self.session.query(self.Donkey.t.sub_sub_category).all()

        assert [get_all_local_data(a) for a in results][2]  == {"__table": u"sub_sub_category", 'sub_category.sub_category_name': u'ac', 'sub_sub_category.sub_sub_category_name': u'acd', 'category.category_name': u'a', 'category.category_description': u'this is a', 'sub_category.sub_category_description': u'this is ac', 'category.category_type': u'wee', 'sub_sub_category.sub_sub_category_description': u'this is acc', 'sub_sub_category.sub_category_name': u'ac', 'sub_sub_category.category_name': u'a', 'sub_category.category_name': u'a'}


        assert_raises(custom_exceptions.InvalidData,
                      load_local_data,
                      self.Donkey,
                      {"__table": u"sub_sub_category",
                       "category.id": 1,
                       "sub_category.id": 3,
                       "sub_sub_category.sub_sub_category_name": u"acd",
                       "sub_sub_category.sub_sub_category_description": u"this is acc"}
                       )

    def test_zzz_add_one_to_many(self):

        cat ="""
        category_name: b,
        sub_category:
            category_name: a
            sub_category_name: ac
            sub_category_description: this is ac
            sub_sub_category:
                sub_sub_category_name: acd
                sub_sub_category_description: this is acc
        """

        cat = yaml.load(cat)

        cat = SingleRecord(self.Donkey, "category", cat)

        assert_raises(custom_exceptions.InvalidData,cat.load)



class test_after_reload(test_basic_input):
    
    @classmethod
    def setUpClass(cls):
        super(test_after_reload, cls).setUpClass()
        cls.Donkey.update_sa(reload = True)
        super(test_after_reload, cls).set_up_inserts()
        
    @classmethod
    def set_up_inserts(cls):
        pass
