#!/usr/bin/env python
from columns import *
from tables import *
from database import *
import sqlalchemy as sa

class test_database(object):
    
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
                        metadata = self.meta)

    def test_basic(self):

        assert self.Donkey.name == "Donkey"
        assert "people" in self.Donkey.tables
        assert "email" in  self.Donkey.tables
        assert len(self.Donkey.tables["people"].fields) == 2
        assert len(self.Donkey.tables["email"].fields) == 1

    def test_relations(self):

        assert self.Donkey.relations[0].name == "Email" 

    def test_checkrelations(self):

        assert self.Donkey.checkrelations() is None

    def test_related_tables(self):

        
        assert self.Donkey.related_tables(self.Donkey.tables["people"])\
                                         ["email"] == "onetomany"
        assert self.Donkey.related_tables(self.Donkey.tables["email"])\
                                         ["people"] == "manytoone"




if __name__ == '__main__':

     Donkey = Database("Donkey",
                         Table("people",
                              Text("name"),
                              OneToMany("Email","email")
                              ),
                         Table("email",
                               Text("email")
                              )
                        )
     print Donkey.related_tables(Donkey.tables["people"]) 
     print Donkey.related_tables(Donkey.tables["email"]) 


 


