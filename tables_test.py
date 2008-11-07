#!/usr/bin/env python
from columns import *
from tables import *
from database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa

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

    def test_defined_columns(self):

        assert "col" in [a.name for a in self.a.sa_defined_columns]
        assert "col2" in [a.name for a in self.a.sa_defined_columns]

    def test_defined_primary_keys(self):

        assert "id" in [a.name for a in self.a.sa_defined_primary_keys]

    def test_check_database(self):

        assert_raises(AttributeError,self.a.sa_extra_columns)


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

    def test_defined_primary_keys(self):

        assert "col" in [a.name for a in self.a.sa_defined_primary_keys]
        assert "col2" in [a.name for a in self.a.sa_defined_primary_keys]

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

    def test_foriegn_key_columns(self):
        
        assert self.Donkey.tables["email"].\
                foriegn_key_columns.has_key("people_id")


class test_database_default_primary_key(object):

    def setUp(self):
        
        self.meta = sa.MetaData()
        self.Donkey = Database("Donkey",
                         Table("people",
                              Text("name"),
                              Text("name2"),
                              OneToMany("Email","email"),
                              primary_key = "name,name2"),
                         Table("email",
                               Text("email")
                              ),
                        metadata = self.meta
                        )

    def test_foriegn_key_columns(self):
        
        assert self.Donkey.tables["email"].\
                foriegn_key_columns.has_key("name2")
        assert self.Donkey.tables["email"].\
                foriegn_key_columns.has_key("name")


if __name__ == '__main__':
        
    from sqlalchemy import create_engine
    import copy
    engine = create_engine('sqlite:///:memory:', echo=True)

    

    meta = sa.MetaData()
    Donkey = Database("Donkey",
                     Table("people",
                          Text("name"),
                          Text("name2"),
                          OneToMany("Email","email"),
                          primary_key = "name,name2"),
                     Table("email",
                           Text("email")
                          ),
                    metadata = meta
                    )
    
    Donkey.tables["people"].sa_table
    Donkey.tables["email"].sa_table
    meta.create_all(engine) 
