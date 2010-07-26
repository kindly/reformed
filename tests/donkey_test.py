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
import application
import reformed.fshp as fshp
from decimal import Decimal
import formencode as fe
import yaml
import os
import logging
import reformed.user_tables
from reformed.resultset import ResultSet
from reformed.events import Event
import reformed.actions as actions

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.debug)
sqllogger.addHandler(sqlhandler)

class test_donkey(object):

    @classmethod
    def setUpClass(cls):
        if not hasattr(cls, "engine"):
            cls.engine = 'sqlite:///:memory:'

        class Options(object):
            pass

        options = Options()
        options.connection_string = False
        options.logging_tables = True
        options.quiet = False

        cls.application = application.Application("test_donkey", options)
        cls.application.logging_tables = True

        cls.application.delete_database()

        cls.application.create_database()

        cls.Donkey = cls.application.database

        entity("people", cls.Donkey,
              Text("name", mandatory = True, length = 30),
              ManyToOne("gender", "code", foreign_key_name = "gender_id", backref = "gender", many_side_not_null = False), ##enumeration look up table
              Address("supporter_address"),
              OneToMany("email","email", 
                        eager = True, 
                        cascade = "all, delete-orphan"),
              OneToMany("donkey_sponsership",
                        "donkey_sponsership"),
              OneToOne("contact_summary",
                       "contact_summary", relation_name = "summary" ),
              OneToMany("transactions",
                       "transactions", foreign_key_name = "pop"),
              ManyToOne("over_18", "code", foreign_key_name = "over_18_id", backref = "over_18", many_side_not_null = False), ##enumeration look up table
              
              Event("new", actions.AddRow("contact_summary")),

              entity = True,
              summary_fields = "name,address_line_1,postcode"
              )

        table("contact_summary", cls.Donkey,
              Money("total_amount", default = 0),
              Integer("transaction_count", default = 0),
#              SumDecimal("total_amount", "transactions.amount", base_level = "people"),
#              AddRow("new_row", "people", initial_event = True),
#              CountRows("transaction_count", "transactions.id", base_level = "people"),
#              MaxDate("membership", "membership", base_level = "people"),
#              CopyText("email", "email", 
#                       base_level = "people", 
#                       fields = "email,email", 
#                       update_when_flag = "active_email",
#                       counter = "email_number"),
#              CopyTextAfter("address", "people",
#                            base_level = "people",
#                            fields = "address_line_1,postcode",
#                            changed_flag = "modified"),
#              Boolean("modified", default = True),
#              logged = False, validated = False
             )

        table("transactions", cls.Donkey,
               DateTime("date"),
               Money("amount"),
               Text("Type", default = u"payment"),
               Event("new,delete,change", 
                     actions.SumEvent("contact_summary.total_amount",
                                        "amount")
                    ),
               Event("new,delete", 
                     actions.CountEvent("contact_summary.transaction_count",
                                        "amount")
                    )
             )

        table("email", cls.Donkey,
              Email("email"),
              #Counter("email_number", base_level = "people"),
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
              #entity_relationship = True
             )
        table("payments", cls.Donkey,
              DateTime("giving_date"),
              Password("password"),
              Money("amount"),
              Text("source")
             )
        info_table("membership", cls.Donkey,
               DateTime("start_date"),#, mandatory = True),
               DateTime("end_date" ),
               CheckNoTwoNulls("val_duplicate_membership", parent_table = "_core", field = "end_date"),  
               valid_core_types  = 'people'
              )

        relation("donkey_people", cls.Donkey,
                 primary_entities = "people",
                 secondary_entities = "donkey"
                )


#        cls.Donkey.add_relation_table(Table("donkey_relation",
#                                     valid_entities1 = "people",
#                                     valid_entities2 = "donkey")
#                                     )

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
                             #Counter("category_number", base_level = "_core_entity"),
                             ManyToOne("entity", "_core",
                                       backref = "categories"),
                             CheckOverLappingDates("check_dates", parent_table = "_core"))
                            )

        table("code", cls.Donkey,
           Text("type"), ## name of relationship
           Text("code"), 
           Text("desctiption", length = 2000),
           Created("created_date"), ## when data was gathered
           CreatedBy("created_by"),
           lookup = True
        ) 

        table('communication', cls.Donkey,
              ForeignKey('_core_id', '_core'),
              Text('communication_type'),
        )

        table('telephone', cls.Donkey,
              ForeignKey('communication_id', 'communication'),
              Text('number'),
              Event('new', actions.AddCommunication())
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
        cls.application.release_all()

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
        assert [a.name for a in self.Donkey["people"].ordered_fields] == ['name', 'gender_id', 'supporter_address', 'over_18_id', '_version', '_modified_date', '_modified_by', '_core_id']

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


    def test_table_paths(self):
        import pprint

        pprint.pprint(self.Donkey.tables["people"].paths)

        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey")].node == "donkey"
        
        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey")].join == "manytoone"
        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey", "donkey_pics",)].node == "donkey_pics"
        assert self.Donkey.tables["people"].paths[("donkey_sponsership", "_donkey", "donkey_pics",)].join == "onetoone"
        assert self.Donkey.tables["donkey"].paths[("donkey_sponsership", "_people", "email")].node == "email"
        assert self.Donkey.tables["donkey"].paths[("donkey_sponsership", "_people", "email")].join == "onetomany"

        assert self.Donkey.tables["donkey"].paths[("donkey_sponsership",)].path == ["_rel_donkey_sponsership"]

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

        assert get_all_local_data(result, internal = True) == {'contact_summary.people_id': 1, 'giving_date': None, 'contact_summary.transaction_count': 0, 'people.name': u'david', '__table': 'donkey_sponsership', 'primary_entity._core_entity.summary': u'name: david -- address_line_1: 43 union street -- postcode: es388', 'people.address_line_1': u'43 union street', 'people.town': None, 'people_id': 1, 'people.postcode': u'es388', 'people.country': None, 'people.address_line_2': None, 'people.over_18_id': None, 'people.address_line_3': None, 'primary_entity._core_entity.title': u'david', 'contact_summary.total_amount': Decimal('0'), 'amount': Decimal('50'), 'donkey_id': 1, 'people.gender_id': None, 'donkey.donkey_type': None, 'primary_entity._core_entity.table': u'people', 'donkey.age': 13, 'primary_entity._core_entity.thumb': None, 'donkey.name': u'jim'} 


        print get_all_local_data(result, fields = ["donkey_id", "contact_summary.total_amount", "donkey.name"])
        assert get_all_local_data(result, fields = ["donkey_id", "contact_summary.total_amount", "donkey.name"]) == {'contact_summary.total_amount': '0', '__table': 'donkey_sponsership', 'donkey.name': u'jim', 'donkey_id': 1, 'id': 1} 

        
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

        a = self.session.query(self.Donkey.get_class("donkey_sponsership")).filter_by(amount = 711110).one()


        print get_all_local_data(a, internal = True)
        assert get_all_local_data(a, internal = True) == {'contact_summary.people_id': 2, 'giving_date': None, 'contact_summary.transaction_count': 0, 'people.name': u'fred', '__table': 'donkey_sponsership', 'primary_entity._core_entity.summary': u'name: fred -- address_line_1: poo1010101 -- postcode: fred', 'people.address_line_1': u'poo1010101', 'people.town': None, 'people_id': 2, 'people.postcode': u'fred', 'people.country': None, 'people.address_line_2': u'poop', 'people.over_18_id': None, 'people.address_line_3': None, 'primary_entity._core_entity.title': u'fred', 'contact_summary.total_amount': Decimal('0'), 'amount': Decimal('711110'), 'donkey_id': 12, 'people.gender_id': None, 'donkey.donkey_type': None, 'primary_entity._core_entity.table': u'people', 'donkey.age': 12, 'primary_entity._core_entity.thumb': None, 'donkey.name': None}

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

        results = self.session.query(self.Donkey.get_class("sub_sub_category")).all()

        print [get_all_local_data(a) for a in results]

        assert [get_all_local_data(a) for a in results] == [{'sub_sub_category_name': u'abc', 'sub_category_id': 1, 'sub_category.sub_category_name': u'ab', '__table': 'sub_sub_category', 'sub_category.sub_category_description': u'this is ab', 'category.category_type': u'wee', 'category.category_description': u'this is a', 'sub_category.category_name': u'a', 'category.category_name': u'a', 'sub_category.category_id': 1, 'sub_sub_category_description': u'this is abc', 'sub_category_name': u'ab', 'category_name': u'a'}]

        
        load_local_data(self.Donkey, {"__table": u"sub_sub_category",
                                      "category.category_name": u"a",
                                      "sub_category.sub_category_name": u"ac",
                                      "sub_category.sub_category_description": u"this is ac",
                                      "sub_sub_category.sub_sub_category_name": u"acc",
                                      "sub_sub_category.sub_sub_category_description": u"this is acc"}
                       )

        results = self.session.query(self.Donkey.get_class("sub_sub_category")).all()

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

        results = self.session.query(self.Donkey.get_class("sub_sub_category")).all()

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

        print self.Donkey.search("people", session = self.session, fields = ["contact_summary.total_amount", "name", "address_line_1"], internal = True, keep_all = False).results[0]

        print self.Donkey.search("people", session = self.session, fields = ["contact_summary.total_amount", "name", "address_line_1"], internal = True, keep_all = False).data

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

    def test_z_info_table(self):

        resultset = self.Donkey.search("people", session = self.session, order_by = "id")
        membership = self.Donkey.get_instance("membership")
        core_id = resultset.get("_core_id")
        membership._core_id = core_id
        self.session.save(membership)
        self.session.commit()
        assert membership._core_id == core_id


        resultset = self.Donkey.search("donkey", session = self.session, order_by = "id")
        membership = self.Donkey.get_instance("membership")
        core_id = resultset.get("_core_id")
        membership._core_id = core_id
        self.session.save(membership)
        assert_raises(AssertionError, self.session.commit)

        self.session.rollback()


    def test_resultset_iter(self):

        resultset = self.Donkey.search("donkey", session = self.session)
        #resultset = ResultSet(search)
        #resultset.collect()
        print len(resultset.results)

        for num, _ in enumerate(resultset):
            continue

        assert num + 1 == len(resultset.results)

    def test_result_get(self):

        resultset = self.Donkey.search("donkey", session = self.session, order_by = "id")
        assert resultset.get("id") == 1


    def test_default(self):

        a = self.session.query(self.Donkey.get_class("people")).first()

        b = self.Donkey.get_instance("transactions")
        b.amount = 0
        b.Type = None
        a._rel_transactions.append(b)

        email = self.Donkey.get_instance("email")
        email.email = "poop@poop.com"

        a._rel_email.append(email)

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


        print self.Donkey["people"].dependant_attributes.keys()
        assert set(self.Donkey["people"].dependant_attributes.keys()) == set(['_rel_email', '_rel_summary', '_rel_donkey_sponsership', '_rel_transactions'])

        print self.Donkey["_core"].dependant_attributes.keys()

        assert set(self.Donkey["_core"].dependant_attributes.keys()) == set(['membership', 'donkey', 'people', 'donkey_people', 'upload', '_communication__core', 'user', 'user_group', 'categories'])

    def test_dependant_tables(self):

        assert set(self.Donkey["people"].dependant_tables) == set(['contact_summary', 'transactions', 'donkey_sponsership', 'email'])

        print set(self.Donkey["_core"].dependant_tables)

        assert set(self.Donkey["_core"].dependant_tables) == set(['donkey', 'people', 'communication', 'donkey_people', 'upload', 'entity_categories', 'membership', 'user', 'user_group'])

    def test_parant_col_attributes(self):

        assert self.Donkey["people"].parent_columns_attributes == {}

        assert self.Donkey["entity_categories"].parent_columns_attributes == {'sub_sub_category_name': 'category', 'sub_category_name': 'category', 'category_name': 'category'}

    def test_z_get_values_from_parent(self):

        cat = self.Donkey.get_instance("category")
        cat.category_name = u"go down"

        sub_cat = self.Donkey.get_instance("sub_category")
        sub_cat.sub_category_name = u"and this"
        cat._rel_sub_category.append(sub_cat)

        sub_sub_cat  = self.Donkey.get_instance("sub_sub_category")      
        sub_sub_cat.sub_sub_category_name = u"wee"
        sub_cat._rel_sub_sub_category.append(sub_sub_cat)

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

        first_donkey = self.session.query(self.Donkey.get_class("donkey"))[1]

    def test_relation_table(self):
        person = self.session.query(self.Donkey.get_class("people")).first()
        donkey = self.session.query(self.Donkey.get_class("donkey")).first()
        user = self.session.query(self.Donkey.get_class("user")).first()


        donkey_people = self.Donkey.get_instance("donkey_people")
        donkey_people._primary = person._rel__core.primary_entity_id
        donkey_people._secondary = donkey._rel__core.primary_entity_id

        self.session.save(donkey_people)
        self.session.commit()

        assert donkey_people._rel__core.primary_entity_id == person._rel__core.primary_entity_id

        assert donkey_people._rel__core.secondary_entity_id == donkey._rel__core.primary_entity_id

        donkey_people = self.Donkey.get_instance("donkey_people")
        donkey_people._primary = user._rel__core.primary_entity_id
        donkey_people._secondary = user._rel__core.primary_entity_id

        self.session.save(donkey_people)

        assert_raises(AssertionError, self.session.commit)
        
        self.session.rollback()
    
    def test_communication_table(self):

        person = self.session.query(self.Donkey.get_class("people")).first()

        telephone = self.Donkey.get_instance("telephone")
        
        core_id = person._core_id

        telephone._core_id = core_id
        telephone.number = '121321434334'

        self.session.save(telephone)

        self.session.commit()

    
    def test_set_option(self):

        self.Donkey.set_option("people", "default_node", "people.people")

        print self.Donkey["people"].default_node
        assert self.Donkey["people"].default_node == "people.people"

        self.Donkey.set_option("people.over_18_id", "cat", "internal")

        assert self.Donkey["people"].fields["over_18_id"].category == "internal"


        connection = self.Donkey.zodb.open()
        root = connection.root()

        people = root["tables"]["people"]

        assert people["params"]["default_node"] == "people.people"
        assert people["fields"]["over_18_id"]["params"]["cat"] == "internal"



    def test_hashed_password(self):

        payment = self.Donkey.get_instance("payments")

        payment.password = "fhdsfhaoifeio9"

        assert not fshp.check("fhdsfhaoifeio", payment.password)

        assert fshp.check("fhdsfhaoifeio9", payment.password)

        payment._from_load = True

        payment.password = "fhdsfhaoifeio9"

        assert payment.password == "fhdsfhaoifeio9"

    def test_local_tables(self):

        import pprint
        #pprint.pprint(self.Donkey["people"].local_tables)
        #print self.Donkey["people"].local_tables.keys()

        assert set(self.Donkey["people"].local_tables.keys()) == \
                set(['over_18.code', '_core', 'gender.code', 
                     'contact_summary', 'primary_entity._core_entity',
                     'secondary_entity._core_entity'])




    def test_no_auto_path(self):
        import pprint

        pprint.pprint(self.Donkey["people"].table_path)

        aa = get_paths(self.Donkey.graph, "people")



