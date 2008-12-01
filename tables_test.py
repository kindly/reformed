#!/usr/bin/env python
from columns import *
from tables import *
from database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine

class test_table_basic():
    
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


class test_table_primary_key():
    
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
        
        self.b = Table("poo",
                       Text("col"),
                       Text("col2"),
                       ManyToOne("rel1","table2"),
                       primary_key="col,col1")

class test_database_default_primary_key(object):
    
    def setUp(self):
        
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

    def tearDown(self):
        del self.meta
        del self.Donkey

    def test_foriegn_key_columns(self):
        
        assert self.Donkey.tables["email"].\
                foriegn_key_columns.has_key("people_id")


class test_database_primary_key(object):

    def setUp(self):
        
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
                                  Text("email")
                                 ),
                            Table("address",
                                  Text("address_line1"),
                                  Text("address_line2")
                                 ),
                        metadata = self.meta
                        )


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

        people = self.Donkey.tables["people"].sa_table
        email = self.Donkey.tables["email"].sa_table

        assert people.columns.has_key("name")
        assert people.columns.has_key("name2")
        assert people.columns["name"].primary_key is True
        assert people.columns["name2"].primary_key is True
        assert email.columns.has_key("name")
        assert email.columns.has_key("name2")
        assert email.columns.has_key("email")
        assert email.columns["id"].primary_key is True
        name2 = email.columns["name2"].foreign_keys.pop()
        name = email.columns["name"].foreign_keys.pop()
        assert name.target_fullname == "people.name"
        assert name2.target_fullname == "people.name2"

    def test_class_and_mapper(self):

        people = self.Donkey.tables["people"].sa_class()
        email = self.Donkey.tables["email"].sa_class()
        
        assert hasattr(people,"name")
        assert hasattr(people,"name2")
        assert hasattr(email,"name")
        assert hasattr(email,"name2")
        assert hasattr(email,"email")
        assert hasattr(email,"id")
        assert hasattr(people,"Email")
        assert hasattr(email,"people")

    def test_join_conditiontions_from_this_table(self):


        people = self.Donkey.tables["people"]

        assert people.join_conditions_from_this_table["email"] in\
               ([["name" ,"name2"],["name" ,"name2"]],
                [["name2" ,"name"],["name2" ,"name"]])

        
        assert people.join_conditions_from_this_table["address"] in\
               ([["name" ,"name2"],["name" ,"name2"]],
                [["name2" ,"name"],["name2" ,"name"]])


if __name__ == '__main__':
        
    engine = create_engine('sqlite:///:memory:', echo=True)

    meta = sa.MetaData()
    Donkey = Database("Donkey",
                     Table("people",
                          Text("name"),
                          Text("name2"),
                          OneToMany("Email","email"),
                          primary_key = "name,name2"),
                     Table("email",
                           Text("email"),
                           Text("email2")

                          ),
                    metadata = meta
                    )
    
    a = Donkey.tables["people"]
    b = Donkey.tables["email"]

