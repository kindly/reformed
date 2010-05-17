from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
import reformed.custom_exceptions
from reformed.data_loader import SingleRecord
from sqlalchemy import create_engine
from reformed.util import get_paths, get_table_from_instance, create_data_dict, make_local_tables, get_all_local_data, load_local_data
import datetime
import reformed.fshp as fshp
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
            cls.engine = create_engine('sqlite:///:memory:' )
            #cls.engine = create_engine('sqlite:///:memory:')

        try:
            os.remove("tests/zodb.fs")
            os.remove("tests/zodb.fs.lock")
            os.remove("tests/zodb.fs.index")
            os.remove("tests/zodb.fs.tmp")
        except OSError:
            pass
        
#        cls.engine = create_engine('mysql://localhost/test_donkey', echo = True)
        cls.meta = sa.MetaData()
        cls.Sess = sa.orm.sessionmaker(bind =cls.engine, autoflush = False)
        cls.Donkey = Database("Donkey", 
                        metadata = cls.meta,
                        engine = cls.engine,
                        session = cls.Sess,
                        entity = True,
                        zodb_store = "tests/zodb.fs"
                        )


        entity("people", cls.Donkey,
              Text("name", mandatory = True, length = 30),
              ManyToOne("gender", "code", foreign_key_name = "gender_id", backref = "gender", many_side_not_null = False), ##enumeration look up table
              Address("supporter_address"),
              OneToMany("email","email", 
                        order_by = "email",
                        eager = True, 
                        cascade = "all, delete-orphan"),
              OneToMany("donkey_sponsership",
                        "donkey_sponsership"),
              OneToOne("contact_summary",
                       "contact_summary" ),
              OneToMany("transactions",
                       "transactions", foreign_key_name = "pop"),
              ManyToOne("over_18", "code", foreign_key_name = "over_18_id", backref = "over_18", many_side_not_null = False), ##enumeration look up table

              entity = True,
              summary_fields = "name,address_line_1,postcode"
              )

        table("contact_summary", cls.Donkey,
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
             )

        table("transactions", cls.Donkey,
               DateTime("date"),
               Money("amount"),
               Text("Type", default = u"payment"))
        table("email", cls.Donkey,
              Email("email"),
              Counter("email_number", base_level = "people"),
              Boolean("active_email", default = False)
             )
        entity("donkey", cls.Donkey,
              Text("name", validation = '__^[a-zA-Z0-9]*$'),
              Integer("age", validation = 'Int'),
              LookupTextValidated("donkey_type", "donkey_types.donkey_type", filter_field = "donkey_type_type", filter_value = "looks"),
              OneToOne("donkey_pics","donkey_pics",
                       foreign_key_name = "donkey",
                       many_side_not_null = False
                       ),
              OneToMany("donkey_sponsership",
                        "donkey_sponsership"),
              Index("idx_name", "name"),
              summary_fields = "name,age",
              entity = True
             )
        table("donkey_types", cls.Donkey,
              Text("donkey_type"),
              Text("donkey_type_type")),
        table("donkey_pics", cls.Donkey,
              Binary("pic"),
              Text("pic_name"),
              Integer("donkey")
             )
        table("donkey_sponsership", cls.Donkey,
              Money("amount"),
              DateTime("giving_date"),
              entity_relationship = True
             )
        table("payments", cls.Donkey,
              DateTime("giving_date"),
              Password("password"),
              Money("amount"),
              Text("source")
             )
        table("membership", cls.Donkey,
               DateTime("start_date", mandatory = True),
               DateTime("end_date" ),
               ManyToOne("_core_entity", "_core_entity"),
               CheckNoTwoNulls("val_duplicate_membership", parent_table = "_core_entity", field = "end_date"),  
              )

        cls.Donkey.add_relation_table(Table("relation",
                             Text("relation_type")
                                          )
                                     )

        cls.Donkey.add_relation_table(Table("donkey_relation",
                                     valid_entities1 = "people",
                                     valid_entities2 = "donkey")
                                     )

        cls.Donkey.add_table(Table("category",
                             Text("category_name"),
                             Text("category_description"),
                             Text("category_type"),
                             OneToManyEager("sub_category", "sub_category", many_side_mandatory = True),
                             primary_key = 'category_name')
                            )

        cls.Donkey.add_table(Table("sub_category",
                             Text("sub_category_name"),
                             Text("sub_category_description"),
                             OneToManyEager("sub_sub_category", "sub_sub_category", many_side_mandatory = True),
                             primary_key = 'category_name,sub_category_name')
                            )

        cls.Donkey.add_table(Table("sub_sub_category",
                             Text("sub_sub_category_name"),
                             Text("sub_sub_category_description"),
                             OneToManyEager('entity_categories', 'entity_categories',
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

        table("code", cls.Donkey,
           Text("type"), ## name of relationship
           Text("code"), 
           Text("desctiption", length = 2000),
           Created("created_date"), ## when data was gathered
           CreatedBy("created_by"),
           lookup = True
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
        jimimage.pic = jimpic


        cls.session.save_or_update(cls.david)
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
        cls.Donkey.status = "terminated"


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

    def test_ordered_fields(self):

        print [a.name for a in self.Donkey["people"].ordered_fields]
        assert [a.name for a in self.Donkey["people"].ordered_fields] == ['name', 'gender_id', 'supporter_address', 'over_18_id', '_version', '_modified_date', '_modified_by', '_core_entity_id']

        print [a.name for a in self.Donkey["people"].ordered_user_fields]

        assert [a.name for a in self.Donkey["people"].ordered_user_fields] == ['name', 'gender_id', 'supporter_address', 'over_18_id']

    def test_validation_empty_string(self):

        self.david = self.Donkey.tables["people"].sa_class()
        print self.Donkey.tables["people"].fields["name"].kw
        print self.Donkey.tables["people"].fields["name"].mandatory
        print self.Donkey.tables["people"].fields["name"].column.mandatory
        self.david.name = u""
        self.david.address_line_1 = u"43 union street"
        self.david.postcode = u"es388"
        assert_raises(formencode.Invalid, self.session.add, self.david)

    def test_logged_attribute(self):

        assert self.david_logged.name == u"david"
        assert self.david_logged.address_line_1 == u"43 union street"
        assert self.david_logged.postcode == u"es388"


    def test_table_paths(self):
        import pprint

        pprint.pprint(self.Donkey.tables["people"].table_path)

        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey")].node == "donkey"
        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey")].join == "manytoone"
        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey", "donkey_pics",)].node == "donkey_pics"
        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey", "donkey_pics",)].join == "onetoone"
        assert self.Donkey.tables["donkey"].paths[("donkey_sponsership", "_people", "email")].node == "email"
        assert self.Donkey.tables["donkey"].paths[("donkey_sponsership", "_people", "email")].join == "onetomany"

    def test_z_make_table_paths(self):

        people = self.Donkey.tables["people"]
        people.paths = None
        people.make_paths()

        #assert self.Donkey.aliases == {} 

    def test_create_data_dict(self):

        results = self.session.query(self.Donkey.tables["donkey"].sa_class)[:2]
        print create_data_dict(results) 
        assert create_data_dict(results) == {1: {'donkey_type': None, 'age': 13, 'name': u'jim'}, 2: {'donkey_type': None, 'age': 131, 'name': u'jim1'}}

        results2 = self.session.query(self.Donkey.tables["donkey"].sa_class).first()
        print create_data_dict(results2) 
        assert create_data_dict(results2) == {1: {'donkey_type': None, 'age': 13, 'name': u'jim'}}

    def test_create_local_data(self):

        result = self.session.query(self.Donkey.tables["donkey_sponsership"].sa_class).first()


        print get_all_local_data(result, internal = True)

        assert get_all_local_data(result, internal = True) == {'contact_summary.people_id': 1, 'giving_date': None, 'contact_summary.transaction_count': 0, 'people.name': u'david', '__table': 'donkey_sponsership', 'contact_summary.membership': None, 'people.address_line_1': u'43 union street', 'contact_summary.modified': True, 'contact_summary.email': None, 'contact_summary.address': u'43 union street es388', 'people.town': None, 'people_id': 1, 'people.postcode': u'es388', 'people.country': None, 'people.address_line_2': None, 'people.over_18_id': None, 'people.address_line_3': None, 'contact_summary.total_amount': Decimal('0'), 'amount': Decimal('50'), 'donkey_id': 1, 'people.gender_id': None, 'donkey.donkey_type': None, 'donkey.age': 13, 'donkey.name': u'jim'} 


        print get_all_local_data(result, fields = ["donkey_id", "contact_summary.total_amount", "donkey.name"])
        assert get_all_local_data(result, fields = ["donkey_id", "contact_summary.total_amount", "donkey.name"]) == {'contact_summary.total_amount': '0', '__table': 'donkey_sponsership', 'donkey.name': u'jim', 'donkey_id': 1, 'id': 1} 

        
    def test_local_tables(self):

        print make_local_tables(self.Donkey.tables["people"].paths)

        assert make_local_tables(self.Donkey.tables["people"].paths) == [{'_core_entity': ('_entity',), 'contact_summary': ('contact_summary',), 'over_18.code': ('over_18',), 'gender.code': ('gender',)}, {'donkey_relation': ('_entity', 'donkey_relation_primary'), 'transactions': ('transactions',), 'email': ('email',), 'entity_categories': ('_entity', 'categories'), 'membership': ('_entity', '_membership'), 'relation': ('_entity', 'relation_primary'), 'donkey_sponsership': ('donkey_sponsership',)}] 

        print make_local_tables(self.Donkey.tables["donkey"].paths)
        assert make_local_tables(self.Donkey.tables["donkey"].paths) == [{'_core_entity': ('_entity',), 'donkey_pics': ('donkey_pics',)}, {'donkey_relation': ('_entity', 'donkey_relation_secondary'), 'entity_categories': ('_entity', 'categories'), 'membership': ('_entity', '_membership'), 'relation': ('_entity', 'relation_primary'), 'donkey_sponsership': ('donkey_sponsership',)}] 
        
##FIXME need these to be corrected

        print self.Donkey.tables["relation"].local_tables 
        assert self.Donkey.tables["relation"].local_tables == {'relation.over_18.code': ('_secondary', 'people', 'over_18'), 'relation.donkey': ('_secondary', 'donkey'), 'relation.user_group': ('_secondary', 'user_group'), 'relation.people': ('_secondary', 'people'), 'relation.user': ('_secondary', 'user'), 'relation.contact_summary': ('_secondary', 'people', 'contact_summary'), 'relation.gender.code': ('_secondary', 'people', 'gender'), 'relation._core_entity': ('_secondary',), 'relation.donkey_pics': ('_secondary', 'donkey', 'donkey_pics')} 

        print self.Donkey.tables["relation"].one_to_many_tables

        assert self.Donkey.tables["relation"].one_to_many_tables == {'relation.relation': ('_secondary', 'relation_primary'), 'relation.membership': ('_secondary', '_membership'), 'relation.donkey_sponsership': ('_secondary', 'donkey', 'donkey_sponsership'), 'relation.email': ('_secondary', 'people', 'email'), 'relation.entity_categories': ('_secondary', 'categories'), 'relation.user_group_user': ('_secondary', 'user_group', '_user_group'), 'relation.transactions': ('_secondary', 'people', 'transactions'), 'relation.user_group_permission': ('_secondary', 'user_group', '_user_group_name')}
        
    def test_zz_add_local(self):

        assert_raises(formencode.Invalid, load_local_data, self.Donkey, {"__table": "people",
                                      "people.address_line_1" : "poo1010101",
                                      "people.address_line_2" : "poop"})
        try:
            load_local_data(self.Donkey, {"__table": "people",
                                      "people.address_line_1" : "poo1010101",
                                      "people.address_line_2" : "poop"})
        except formencode.Invalid, e:
            print e.error_dict
            assert str(e.error_dict) == """{'people.name': [Invalid(u'Please enter a value',)], 'people.postcode': [Invalid(u'Please enter a value',)]}"""


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
            assert str(e.error_dict) == r"""{'donkey.age': [Invalid(u'Please enter an integer value',), Invalid(u'Please enter an integer value',)], 'people.name': [Invalid(u'Please enter a value',)], 'people.postcode': [Invalid(u'Please enter a value',)]}"""

            assert str(e.error_dict["donkey.age"]) == "[Invalid(u'Please enter an integer value',), Invalid(u'Please enter an integer value',)]"


        load_local_data(self.Donkey, {"__table": u"donkey_sponsership",
                                      "donkey_sponsership.amount" : 711110,                                   
                                      "donkey.age" : 12,                                   
                                      "people.name" : u"fred",
                                      "people.postcode" : u"fred",
                                      "people.address_line_1" : u"poo1010101",
                                      "people.address_line_2" : u"poop"})

        a = self.session.query(self.Donkey.aliases["donkey_sponsership"]).filter_by(amount = 711110).one()


        print get_all_local_data(a, internal = True)
        assert get_all_local_data(a, internal = True) == {'contact_summary.people_id': 2, 'giving_date': None, 'contact_summary.transaction_count': 0, 'people.name': u'fred', '__table': 'donkey_sponsership', 'contact_summary.membership': None, 'people.address_line_1': u'poo1010101', 'contact_summary.modified': True, 'contact_summary.email': None, 'contact_summary.address': u'poo1010101 fred', 'people.town': None, 'people_id': 2, 'people.postcode': u'fred', 'people.country': None, 'people.address_line_2': u'poop', 'people.over_18_id': None, 'people.address_line_3': None, 'contact_summary.total_amount': Decimal('0'), 'amount': Decimal('711110'), 'donkey_id': 12, 'people.gender_id': None, 'donkey.donkey_type': None, 'donkey.age': 12, 'donkey.name': None}

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

        results = self.session.query(self.Donkey.aliases["sub_sub_category"]).all()

        print [get_all_local_data(a) for a in results]

        assert [get_all_local_data(a) for a in results] == [{'sub_sub_category_name': u'abc', 'sub_category_id': 1, 'sub_category.sub_category_name': u'ab', '__table': 'sub_sub_category', 'sub_category.sub_category_description': u'this is ab', 'category.category_type': u'wee', 'category.category_description': u'this is a', 'sub_category.category_name': u'a', 'category.category_name': u'a', 'sub_category.category_id': 1, 'sub_sub_category_description': u'this is abc', 'sub_category_name': u'ab', 'category_name': u'a'}]

        
        load_local_data(self.Donkey, {"__table": u"sub_sub_category",
                                      "category.category_name": u"a",
                                      "sub_category.sub_category_name": u"ac",
                                      "sub_category.sub_category_description": u"this is ac",
                                      "sub_sub_category.sub_sub_category_name": u"acc",
                                      "sub_sub_category.sub_sub_category_description": u"this is acc"}
                       )

        results = self.session.query(self.Donkey.aliases["sub_sub_category"]).all()

        print [get_all_local_data(a) for a in results]

        assert [get_all_local_data(a) for a in results] == [{'sub_sub_category_name': u'abc', 'sub_category_id': 1, 'sub_category.sub_category_name': u'ab', '__table': 'sub_sub_category', 'sub_category.sub_category_description': u'this is ab', 'category.category_type': u'wee', 'category.category_description': u'this is a', 'sub_category.category_name': u'a', 'category.category_name': u'a', 'sub_category.category_id': 1, 'sub_sub_category_description': u'this is abc', 'sub_category_name': u'ab', 'category_name': u'a'}, {'sub_sub_category_name': u'acc', 'sub_category_id': 2, 'sub_category.sub_category_name': u'ac', '__table': 'sub_sub_category', 'sub_category.sub_category_description': u'this is ac', 'category.category_type': u'wee', 'category.category_description': u'this is a', 'sub_category.category_name': u'a', 'category.category_name': u'a', 'sub_category.category_id': 1, 'sub_sub_category_description': u'this is acc', 'sub_category_name': u'ac', 'category_name': u'a'}]



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

        results = self.session.query(self.Donkey.aliases["sub_sub_category"]).all()

        print [get_all_local_data(a) for a in results][2]

        assert [get_all_local_data(a) for a in results][2]  == {'sub_sub_category_name': u'acd', 'sub_category_id': 2, 'sub_category.sub_category_name': u'ac', '__table': 'sub_sub_category', 'sub_category.sub_category_description': u'this is ac', 'category.category_type': u'wee', 'category.category_description': u'this is a', 'sub_category.category_name': u'a', 'category.category_name': u'a', 'sub_category.category_id': 1, 'sub_sub_category_description': u'this is acc', 'sub_category_name': u'ac', 'category_name': u'a'}


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


    def test_search_internal(self):

        print self.Donkey.search("people", session = self.session, fields = ["contact_summary.total_amount", "name", "address_line_1"], internal = True, keep_all = False)

        assert self.Donkey.search("people", session = self.session, fields = ["contact_summary.total_amount", "name", "address_line_1"], internal = True, keep_all = False).data ==  [{'__table': 'people', 'address_line_1': u'43 union street', 'contact_summary.total_amount': Decimal('0'), 'id': 1, 'name': u'david'}]

    def test_search_with_convert(self):

        print self.Donkey.search("people", session = self.session, fields = ["contact_summary.total_amount", "name", "address_line_1"], keep_all = False) 
        assert self.Donkey.search("people", session = self.session, fields = ["contact_summary.total_amount", "name", "address_line_1"], keep_all = False).data == [{'__table': 'people', 'address_line_1': u'43 union street', 'contact_summary.total_amount': '0', 'id': 1, 'name': u'david'}]

        print self.Donkey.search("people", session = self.session, fields = ["contact_summary.total_amount", "name", "address_line_1"], count = True, keep_all = False) 
        assert self.Donkey.search("people", session = self.session, fields = ["contact_summary.total_amount", "name", "address_line_1"], count = True, keep_all = False).data == [{'__table': 'people', 'address_line_1': u'43 union street', 'contact_summary.total_amount': '0', 'id': 1, 'name': u'david'}]

        assert self.Donkey.search("donkey",  count = True).row_count == 11

        
        assert self.Donkey.search("donkey", "name > {}", params = {"name": "jim5"},  count = True).row_count == 4

    def test_search_single_result(self):


        assert_raises(custom_exceptions.SingleResultError, self.Donkey.search_single, "donkey")
        assert_raises(custom_exceptions.SingleResultError, self.Donkey.search_single, "membership")



    def test_default(self):

        a = self.session.query(self.Donkey.aliases["people"]).first()

        b = self.Donkey.get_instance("transactions")
        b.amount = 0
        b.Type = None
        a.transactions.append(b)

        email = self.Donkey.get_instance("email")
        email.email = "poop@poop.com"

        a.email.append(email)

        self.session.add(a)
        self.session.add(b)
        self.session.add(email)

        self.session.commit()

        assert b.Type == "payment"
        assert email.active_email is False


    def test_all_fields_have_different_numbers(self):


        for table in self.Donkey.tables.values():
            if table.name.startswith("__") or table.name.startswith("_log_"):
                continue
            field_ids = []
            print table

            for field in table.fields.values():
                print field.name,field.field_id
                field_ids.append(field.field_id)

            
            print field_ids
            assert len(field_ids) == len(set(field_ids))

    def test_dependant_attributes(self):


        assert set(self.Donkey["people"].dependant_attributes.keys()) == set(['contact_summary', 'transactions', 'donkey_sponsership', 'email'])

        print self.Donkey["_core_entity"].dependant_attributes.keys()

        assert set(self.Donkey["_core_entity"].dependant_attributes.keys()) == set(['_membership', 'donkey', 'people', 'relation_primary', 'relation_secondary', 'donkey_relation_secondary', 'user', 'user_group', 'categories', 'donkey_relation_primary'])

    def test_dependant_tables(self):

        assert set(self.Donkey["people"].dependant_tables) == set(['contact_summary', 'transactions', 'donkey_sponsership', 'email'])

        print set(self.Donkey["_core_entity"].dependant_tables)

        assert set(self.Donkey["_core_entity"].dependant_tables) == set(['donkey_relation', 'donkey', 'people', 'entity_categories', 'membership', 'relation', 'user', 'user_group'])

    def test_parant_col_attributes(self):

        assert self.Donkey["people"].parent_columns_attributes == {}

        assert self.Donkey["entity_categories"].parent_columns_attributes == {'sub_sub_category_name': 'category', 'sub_category_name': 'category', 'category_name': 'category'}

    def test_z_get_values_from_parent(self):

        cat = self.Donkey.get_instance("category")
        cat.category_name = u"go down"

        sub_cat = self.Donkey.get_instance("sub_category")
        sub_cat.sub_category_name = u"and this"
        cat.sub_category.append(sub_cat)

        sub_sub_cat  = self.Donkey.get_instance("sub_sub_category")      
        sub_sub_cat.sub_sub_category_name = u"wee"
        sub_cat.sub_sub_category.append(sub_sub_cat)

        self.session.save(cat)
        self.session.save(sub_cat)
        self.session.save(sub_sub_cat)

        self.session.commit()

        assert sub_cat.category_name == u"go down"
        assert sub_sub_cat.category_name == u"go down"
        assert sub_sub_cat.sub_category_name == u"and this"

        cat.category_name = u"go down2"
        sub_cat.sub_category_name = u"and this2"

        self.session.save(cat)
        self.session.save(sub_cat)
        self.session.commit()

        assert sub_cat.category_name == u"go down2"
        assert sub_sub_cat.category_name == u"go down2"
        assert sub_sub_cat.sub_category_name == u"and this2"

    def test_zzz_version_id(self):

        donkey = self.Donkey.get_instance("donkey")

        donkey.name = u"poo"

        self.session.save(donkey)
        self.session.commit()
        
        donkey.name = u"poo2"
        donkey._version = u"1"

        self.session.save(donkey)
        self.session.commit()

    def test_hashed_password(self):

        payment = self.Donkey.get_instance("payments")

        payment.password = "fhdsfhaoifeio9"

        assert not fshp.check("fhdsfhaoifeio", payment.password)

        assert fshp.check("fhdsfhaoifeio9", payment.password)

        payment._from_load = True

        payment.password = "fhdsfhaoifeio9"

        assert payment.password == "fhdsfhaoifeio9"


    def test_no_auto_path(self):
        import pprint

        pprint.pprint(self.Donkey["people"].table_path)

        aa = get_paths(self.Donkey.graph, "people")




        


        
        




class test_after_reload(test_basic_input):
    
    @classmethod
    def setUpClass(cls):
        super(test_after_reload, cls).setUpClass()
        cls.Donkey.update_sa(reload = True)
        super(test_after_reload, cls).set_up_inserts()
        
    @classmethod
    def set_up_inserts(cls):
        pass
