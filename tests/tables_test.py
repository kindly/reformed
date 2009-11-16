#!/usr/bin/env python
from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import formencode as fe
import logging
import datetime
from sqlalchemy.exc import IntegrityError

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)


class test_table_basic(object):
    
    def setUp(self):
        
        self.a = Table("poo",
                       Text("col"),
                       Text("col2"),
                       ManyToOne("rel1","table2"))
        
    def test_items(self):
        
        assert self.a.items["col"].name == "col"
        assert self.a.columns["col"].name == "col"
        assert self.a.items["col2"].name == "col2"
        assert self.a.columns["col2"].name == "col2"
        assert self.a.items["rel1"].name == "rel1"
        assert self.a.relations["rel1"].name == "rel1"         
    
    def test_fields(self):

        assert self.a.fields["col"].name == "col"
        assert self.a.fields["col2"].name == "col2"
        assert self.a.fields["rel1"].name == "rel1"
        assert self.a.fields["col"].table is self.a
        assert self.a.fields["col2"].table is self.a
        assert self.a.fields["rel1"].table is self.a

    def test_primary_key_columns(self):
        
        print self.a.primary_key_columns
        assert self.a.primary_key_columns ==  {}

    def test_defined_non_primary_key(self):
        
        assert self.a.defined_non_primary_key_columns.has_key("col")
        assert self.a.defined_non_primary_key_columns.has_key("col2")


class test_table_primary_key(object):
    
    def setUp(self):
        
        self.a = Table("poo",
                       Text("col"),
                       Text("col2"),
                       Text("col3"),
                       ManyToOne("rel1","table2"),
                       primary_key="col,col2",
                       )
        
    def test_primary_key_columns(self):
        
        assert self.a.primary_key_columns.has_key("col")
        assert self.a.primary_key_columns.has_key("col2")


    def test_defined_non_primary_key(self):
        
        assert self.a.defined_non_primary_key_columns.has_key("col3")


class test_database_default_primary_key(object):
    
    @classmethod
    def setUpClass(self):
        
        self.engine = sa.create_engine('sqlite:///:memory:', echo=True)
        self.meta1 = sa.MetaData()
        self.Session = sa.orm.sessionmaker(bind =self.engine, autoflush = False)
        self.Donkey1= Database("Donkey1",
                         Table("people",
                              Text("name"),
                              OneToMany("Email","email")
                              ),
                         Table("email",
                               Text("email")
                              ),
                           metadata = self.meta1,
                           engine = self.engine,
                           session = self.Session)

        self.Donkey1.persist()
                        

    @classmethod
    def tearDownClass(self):
        del self.Donkey1
        del self.meta1
        del self.engine
        del self.Session

    def test_foriegn_key_columns(self):
        
        assert self.Donkey1.tables["email"].\
                foriegn_key_columns.has_key("people_id")


class test_database_primary_key(object):

    @classmethod
    def setUpClass(self):

        self.engine = sa.create_engine('sqlite:///:memory:')
        self.meta = sa.MetaData()
        self.Session = sa.orm.sessionmaker(bind =self.engine, autoflush = False)
        
        self.Donkey = Database("Donkey2",
                            Table("people",
                                  Text("name"),
                                  Text("name2"),
                                  Text("name3", length = 10),
                                  Text("name4"),
                                  Text("name5"),
                                  Text("name6"),
                                  Text("name7"),
                                  Text("name8"),
                                  Text("name9"),
                                  RequireIfMissing("req_name9", field = 'name9', missing = 'name'),
                                  OneToOne("address","address"),
                                  OneToMany("Email","email", 
                                           order_by = 'email desc,name2, email_type'),
                                  Index("idx_name3_name4", "name3, name4"),
                                  UniqueIndex("idx_name5", "name5"),
                                  UniqueConstraint("name67", "name6,name7"),
                                  UniqueConstraint("con_name8", "name8"),
                                  primary_key = "name,name2",
                                 ),
                            Table("email",
                                  Email("email"),
                                  Text("email_type")
                                 ),
                            Table("address",
                                  Address("address")
                                 ),
                           metadata = self.meta,
                           engine = self.engine,
                           session = self.Session)
                        

        self.Donkey.persist()
        session = self.Donkey.Session()

        self.peopletable = self.Donkey.tables["people"].sa_table
        self.emailtable = self.Donkey.tables["email"].sa_table
        self.name2 = self.emailtable.columns["name2"].foreign_keys.pop()
        self.name = self.emailtable.columns["name"].foreign_keys.pop()
        self.email = self.Donkey.tables["email"].sa_class()
        self.email2 = self.Donkey.tables["email"].sa_class()
        self.email3 = self.Donkey.tables["email"].sa_class()
        
        self.people = self.Donkey.tables["people"].sa_class()
        self.people.name = u"david"
        self.people.name2 = u"david"
        self.email.email = u"aavid@raz.nick"
        self.email2.email = u"david@raz.nick"
        self.email3.email = u"david@raz.nick"
        self.email.email_type = u"a"
        self.email2.email_type = u"b"
        self.email3.email_type = u"a"
        self.people.Email.append(self.email)
        self.people.Email.append(self.email2)
        self.people.Email.append(self.email3)
        
        session.add(self.people)
        session.add(self.email)
        session.add(self.email2)
        session.add(self.email3)

        session.commit()

        self.session = session

        self.peoplelogged = self.Donkey.tables["_log_people"].sa_table
        
#    def tearDown(self):
#        self.meta.clear()
    @classmethod
    def tearDownClass(self):
        del self.Donkey
        del self.meta
        del self.engine
        del self.Session
        del self.session

    def test_foriegn_key_columns2(self):
        
        assert self.Donkey.tables["email"].\
                foriegn_key_columns.has_key("name2")
        assert self.Donkey.tables["email"].\
                foriegn_key_columns.has_key("name")
        assert self.Donkey.tables["address"].\
                foriegn_key_columns.has_key("name2")
        assert self.Donkey.tables["address"].\
                foriegn_key_columns.has_key("name")

    def test_sa_table(self):

        assert self.peopletable.columns.has_key("name")
        assert self.peopletable.columns.has_key("name2")
#        assert self.peopletable.columns["name"].primary_key is True
#        assert self.peopletable.columns["name2"].primary_key is True
        assert self.emailtable.columns.has_key("name")
        assert self.emailtable.columns.has_key("name2")
        assert self.emailtable.columns.has_key("email")
        assert self.emailtable.columns["id"].primary_key is True
        assert self.name.target_fullname == "people.name"
        assert self.name2.target_fullname == "people.name2"

    def test_index(self):

        assert "idx_name3_name4" in [a.name for a in self.peopletable.indexes] 
        assert "idx_name5" in [a.name for a in self.peopletable.indexes] 
        
    def test_unique_index(self):
        a = self.Donkey.get_instance("people") 
        a.name9 = u"poo"
        a.name5 = u"poo"
        self.session.add(a)
        self.session.commit()

        b = self.Donkey.get_instance("people") 
        b.name9 = u"poo"
        b.name5 = u"poo"
        self.session.add(b)
        assert_raises(IntegrityError, self.session.commit)

        
    def test_unique_constraints(self):


        constraint_columns = []
        for constraint in self.peopletable.constraints:
            d= set()
            for columns in constraint.columns:
                d.add(columns.name)
            constraint_columns.append(d)
        assert set(["name6","name7"]) in constraint_columns
        assert set(["name8"]) in constraint_columns


    def test_sa_table_logged(self):
        assert self.peoplelogged.columns.has_key("name")

    def test_class_and_mapper(self):
        
        assert hasattr(self.people,"name")
        assert hasattr(self.people,"name2")
        assert hasattr(self.email,"name")
        assert hasattr(self.email,"name2")
        assert hasattr(self.email,"email")
        assert hasattr(self.email,"id")
        assert hasattr(self.people,"Email")
        assert hasattr(self.email,"_people")

    def test_foreign_key_constraints(self):

        assert self.Donkey.tables["email"].\
                foreign_key_constraints[("people", "Email")] in\
               ([["name" ,"name2"],["people.name" ,"people.name2"]],
                [["name2" ,"name"],["people.name2" ,"people.name"]])

        
        assert self.Donkey.tables["address"].\
                foreign_key_constraints[("people", "address")] in\
               ([["name" ,"name2"],["people.name" ,"people.name2"]],
                [["name2" ,"name"],["people.name2" ,"people.name"]])

    def test_validation_from_field_types(self):

        email = self.Donkey.tables["email"].columns["email"] 
        email_table = self.Donkey.tables["email"] 
        assert isinstance(email_table.validation_from_field_types(email)\
                          .validators[0], fe.validators.UnicodeString)
                
        

    def test_validation_schemas(self):

        validation_schema = self.Donkey.tables["email"].validation_schema


        
        assert self.Donkey.tables["email"].validation_schema.to_python(
                                             {"email": "pop@david.com",
                                              "name2" :"david",
                                              "name" : "david"})==\
                                             {"email": "pop@david.com",
                                              "name2" :"david",
                                              "name" : "david"}
                                                
        assert_raises(formencode.Invalid,
                      self.Donkey.tables["email"].validation_schema.to_python,
                                             {"email": "popdavid.com"})

        assert self.Donkey.tables["address"].validation_schema.to_python(
                                          {"address_line_1": "56 moreland",
                                           "address_line_2": "essex",
                                           "postcode" : "IG5 0dp",
                                           "name2" :"david",
                                           "name" : "david"})==\
                                          {"address_line_1": "56 moreland",
                                           "address_line_2": "essex",
                                           "postcode" : "IG5 0dp",
                                           "name2" :"david",
                                           "name" : "david"}
        
        assert_raises(formencode.Invalid,
                    self.Donkey.tables["address"].validation_schema.to_python,
                                          {"address_line_1": "56 moreland",
                                           "address_line_2": "essex",
                                           "postcode" : None})

    def test_order(self):

        all = self.session.query(self.Donkey.tables["people"].sa_class).first()

        assert all.Email[0].email == u"david@raz.nick"
        assert all.Email[1].email == u"david@raz.nick"
        assert all.Email[2].email == u"aavid@raz.nick"
        assert all.Email[0].email_type == u"a"
        assert all.Email[1].email_type == u"b"
        assert all.Email[2].email_type == u"a"

    def test_length(self):
        
        assert self.peopletable.columns['name3'].type.length == 10

        session = self.Donkey.Session()
        long_person = self.Donkey.tables["people"].sa_class()
        long_person.name3 = u"davidfdsafsdasffdsas"
        assert_raises(fe.Invalid, session.add, long_person)

    def test_basic_validation(self):

        session = self.Donkey.Session()
        email = self.Donkey.tables["email"].sa_class()
        email.email = u"popo.com"
        assert_raises(fe.Invalid, session.add, email)

    def test_validation_of_mandatory_fk(self):

        session = self.Donkey.Session()
        email = self.Donkey.tables["email"].sa_class()
        email.email = u"po@po.com"
        assert_raises(fe.Invalid, session.add, email)

    def test_chained_validation(self):

        people = self.Donkey.tables["people"].sa_class()

        assert_raises(fe.Invalid, self.session.add, people)

        people = self.Donkey.tables["people"].sa_class()

        people.name9 = u"pop"
        assert self.session.add(people) is None
        
        people = self.Donkey.tables["people"].sa_class()
        people.name = u"pop"

        self.session.add(people) is None



        
class test_field_type_validation(object):

    @classmethod
    def setUpClass(self):

        self.engine = sa.create_engine('sqlite:///:memory:', echo=True)
        self.meta = sa.MetaData()
        self.Session = sa.orm.sessionmaker(bind =self.engine, autoflush = False)
        
        self.Donkey = Database("Donkey",
                            Table("people",
                                  Email("name1", length = 10, mandatory = True),
                                  Money("name2", mandatory = True),
                                  Integer("name3", mandatory = True),
                                  DateTime("name4", mandatory = True),
                                  Boolean("name5", mandatory = True),
                                  Binary("name6", mandatory = True),
                                  Text("name7", validation = r"Email"),
                                  Text("name8", validation = r"__poo.*")
                                 ),
                           metadata = self.meta,
                           engine = self.engine,
                           session = self.Session)
                        

        self.Donkey.persist()
        self.session = self.Donkey.Session()

    def test_all_fields(self):

        person = self.Donkey.tables["people"].sa_class()
        person.name2 = 10.2
        person.name3 = 7
        person.name4 = datetime.datetime.now()
        person.name5 = True
        pic = file("tests/jim.xcf", mode = "rb").read()
        person.name6 = pic
        
        assert_raises(fe.Invalid, self.session.add, person)

        person.email = "p@pl.com"
        self.session.add(person)
        person.email = u'pop'
        assert_raises(fe.Invalid, self.session.add, person)
        person.email = "p@pl.com"
        person.name2 = u"plop"
        assert_raises(fe.Invalid, self.session.add, person)
        person.name2 = 10.2
        person.name3 =  "plop"
        assert_raises(fe.Invalid, self.session.add, person)
        person.name3 = 7
        person.name4 = ''
        assert_raises(fe.Invalid, self.session.add, person)
        person.name4 = datetime.datetime.now()
        person.name5 = ''
        assert_raises(fe.Invalid, self.session.add, person)
        person.name5 = True
        person.name6 = None
        assert_raises(fe.Invalid, self.session.add, person)

    def test_field_validation(self):

        person = self.Donkey.tables["people"].sa_class()
        person.email = "pop@pop.com"
        person.name2 = 10.2
        person.name3 = 7
        person.name4 = datetime.datetime.now()
        person.name5 = True
        pic = file("tests/jim.xcf", mode = "rb").read()
        person.name6 = pic
        person.name7 = "poop@poop.com"
        person.name8 = "poop"
        self.session.add(person)
        person.name7 = "plop"
        assert_raises(fe.Invalid, self.session.add, person)
        person.name7 = "poop@poop.com"
        person.name8 = "pop"
        assert_raises(fe.Invalid, self.session.add, person)


if __name__ == '__main__':

    engine = sa.create_engine('sqlite:///:memory:', echo=True)
    meta = sa.MetaData()
    Donkey = Database("Donkey",
                        Table("people",
                              Text("name"),
                              Text("name2", default = "poo"),
                              OneToOne("address","address"),
                              OneToMany("Email","email"),
                             ),
                        Table("email",
                              Text("email")
                             ),
                        Table("address",
                             Text("address_line1"),
                             Text("address_line2")
                             ),
                    metadata = meta
                    )

    Donkey.update_sa()

    a = Donkey.tables["people"]

    meta.create_all(engine)
