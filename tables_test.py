#!/usr/bin/env python
from unittest import TestCase
from Columns import *
from Tables import *

class test_table(TestCase):
    
    def setUp(self):
        
        self.a = Table("poo", Text("col"))
        
    def test_table(self):
        
        assert self.a.items["col"].name == "col"
#        assert self.a.columns["col"].name == "col"
    
    
