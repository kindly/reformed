#!/usr/bin/env python
from fields import *
from tables import *
from database import *

class test_database(object):
     
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
                               metadata = self.meta)
        self.Donkey.update_sa()
    
    
 #   def tearDown(self):
 #       self.meta.clear()

    def test_basic(self):

        assert self.Donkey.name == "Donkey"
        assert "people" in self.Donkey.tables
        assert "email" in  self.Donkey.tables
        assert len(self.Donkey.tables["people"].fields) == 3 # modified field
        assert len(self.Donkey.tables["email"].fields) == 2


    def test_relations(self):

        print self.Donkey.relations
        assert self.Donkey.relations[2].name == "Email" 

    def test_checkrelations(self):

        assert self.Donkey.checkrelations() is None

    def test_related_tables(self):

        
        assert self.Donkey.related_tables(self.Donkey.tables["people"])\
                                         ["email"] == "onetomany"
        assert self.Donkey.related_tables(self.Donkey.tables["email"])\
                                         ["people"] == "manytoone"


    def test_table_with_relations(self):

        d = self.Donkey

        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             ["email"].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             ["people"].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             ["email"].type == "onetomany"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             ["people"].type == "onetomany"
