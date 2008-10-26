#!/usr/bin/env python
from unittest import TestCase
from columns import *
from tables import *

class test_table(TestCase):
    
    def setUp(self):
        
        self.a = Table("poo", Text("col"), Text("col2"),ManyToOne("rel1"))
        
    def test_table(self):
        
        assert self.a.items["col"].name == "col"
        assert self.a.columns["col"].name == "col"
        assert self.a.items["col2"].name == "col2"
        assert self.a.columns["col2"].name == "col2"
        assert self.a.items["rel1"].name == "rel1"
        assert self.a.relations["rel1"].name == "rel1"         
if __name__ == '__main__':

   a = Table("poo", Text("col"), Text("col2"),ManyToOne("rel1"))
