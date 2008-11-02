#!/usr/bin/env python
from columns import *
from tables import *
from nose.tools import assert_raises,raises

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
    
    def test_defined_columns(self):

        assert "col" in [a.name for a in self.a.sa_defined_columns]
        assert "col2" in [a.name for a in self.a.sa_defined_columns]

    def test_defined_primary_keys(self):

        assert "id" in [a.name for a in self.a.sa_defined_primary_keys]

    def test_sa_extra_columns(self):

        assert_raises(AttributeError,self.a.sa_extra_columns)


class test_table_primary_key():
    
    def setUp(self):
        
        self.a = Table("poo",
                       Text("col"),
                       Text("col2"),
                       ManyToOne("rel1","table2"),
                       primary_key="col,col2")
        
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

if __name__ == '__main__':
 
    a = Table("poo",
              Text("col"),
              Text("col2"),
              ManyToOne("rel1","table2"),
              primary_key="col1,col2")
