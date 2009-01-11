#!/usr/bin/env python
from fields import *
from tables import *
from database import *
from nose.tools import assert_raises,raises

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
        
        assert self.a.primary_key_columns.has_key("id")

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
                       primary_key="col,col2")
        
    def test_primary_key_columns(self):
        
        assert self.a.primary_key_columns.has_key("col")
        assert self.a.primary_key_columns.has_key("col2")

    def test_defined_non_primary_key(self):
        
        assert self.a.defined_non_primary_key_columns.has_key("col3")

    @raises(AttributeError)
    def test_defined_primary_keyssetUp(self):
        
        a= Table("poo",
            Text("col"),
            Text("col2"),
            ManyToOne("rel1","table2"),
            primary_key="col,col1")

class test_database_default_primary_key(object):
    
    def setUp(self):
        
        self.engine = sa.create_engine('sqlite:///:memory:', echo=True)
        self.meta = sa.MetaData()
        self.Donkey = Database("Donkey",
                         Table("people",
                              Text("name"),
                              OneToMany("Email","email")
                              ),
                         Table("email",
                               Text("email")
                              ),
                        metadata = self.meta
                        )


    def test_foriegn_key_columns(self):
        
        assert self.Donkey.tables["email"].\
                foriegn_key_columns.has_key("people_id")


class test_database_primary_key(object):

    def setUp(self):

        self.engine = sa.create_engine('sqlite:///:memory:', echo=True)
        self.meta = sa.MetaData()
        
        self.Donkey = Database("Donkey",
                            Table("people",
                                  Text("name"),
                                  Text("name2"),
                                  OneToOne("address","address"),
                                  OneToMany("Email","email"),
                                  primary_key = "name,name2"
                                 ),
                            Table("email",
                                  Email("email")
                                 ),
                            Table("address",
                                  Address("address")
                                 ),
                        metadata = self.meta
                        )

        self.Donkey.update_sa()

        self.peopletable = self.Donkey.tables["people"].sa_table
        self.emailtable = self.Donkey.tables["email"].sa_table
        self.name2 = self.emailtable.columns["name2"].foreign_keys.pop()
        self.name = self.emailtable.columns["name"].foreign_keys.pop()
        self.people = self.Donkey.tables["people"].sa_class()
        self.email = self.Donkey.tables["email"].sa_class()
        
        self.email.email = "david@raz.nick"

#    def tearDown(self):
#        self.meta.clear()

    def test_foriegn_key_columns(self):
        
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
        assert self.peopletable.columns["name"].primary_key is True
        assert self.peopletable.columns["name2"].primary_key is True
        assert self.emailtable.columns.has_key("name")
        assert self.emailtable.columns.has_key("name2")
        assert self.emailtable.columns.has_key("email")
        assert self.emailtable.columns["id"].primary_key is True
        assert self.name.target_fullname == "people.name"
        assert self.name2.target_fullname == "people.name2"

    def test_class_and_mapper(self):
        
        assert hasattr(self.people,"name")
        assert hasattr(self.people,"name2")
        assert hasattr(self.email,"name")
        assert hasattr(self.email,"name2")
        assert hasattr(self.email,"email")
        assert hasattr(self.email,"id")
        assert hasattr(self.people,"Email")
        assert hasattr(self.email,"people")

    def test_foreign_key_constraints(self):

        assert self.Donkey.tables["email"].\
                foreign_key_constraints["people"] in\
               ([["name" ,"name2"],["people.name" ,"people.name2"]],
                [["name2" ,"name"],["people.name2" ,"people.name"]])

        
        assert self.Donkey.tables["address"].\
                foreign_key_constraints["people"] in\
               ([["name" ,"name2"],["people.name" ,"people.name2"]],
                [["name2" ,"name"],["people.name2" ,"people.name"]])

    def test_validation_schemas(self):

        validation_schema = self.Donkey.tables["email"].validation_schema

        assert self.Donkey.tables["email"].validation_schema.to_python(
                                             {"email": "pop@david.com"})==\
                                             {"email": "pop@david.com"}
                                                
        assert_raises(formencode.Invalid,
                      self.Donkey.tables["email"].validation_schema.to_python,
                                             {"email": "popdavid.com"})

        assert self.Donkey.tables["address"].validation_schema.to_python(
                                          {"address_line_1": "56 moreland",
                                           "address_line_2": "essex",
                                           "postcode" : "IG5 0dp"})==\
                                          {"address_line_1": "56 moreland",
                                           "address_line_2": "essex",
                                           "postcode" : "IG5 0dp"}
        
        assert_raises(formencode.Invalid,
                    self.Donkey.tables["address"].validation_schema.to_python,
                                          {"address_line_1": "56 moreland",
                                           "address_line_2": "essex"
                                           })
        

if __name__ == '__main__':
    
    Donkey = Database("Donkey",
                        Table("people",
                              Text("name"),
                              Text("name2"),
                              OneToOne("address","address"),
                              OneToMany("Email","email"),
                              primary_key = "name,name2"
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
    b = Donkey.tables["email"]
    c = Donkey.tables["address"]

    meta.create_all(engine)
    people = Donkey.tables["people"].sa_class()
