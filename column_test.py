#!/usr/bin/env python
from unittest import TestCase
from columns import *

class test_fields(TestCase):
    
    def setUp(self):
        
        self.a = Text("col")
        
        class Text2(Fields):
        
            def __init__(self, name, *args, **kw):
                
                self.text = Columns(sa.Unicode)
                self.text3 = Columns(sa.Unicode)

                super(Text2,self).__init__(name, *args, **kw)
        
        self.b = Text2("col")
        
        self.c = ManyToOne("many")
            
    def test_text_field_fieldname(self):
        
        assert self.a.columns["col"].name == "col"
        
    def test_text_filed_no_field_name(self):
        
        assert self.b.columns["text"].name == "text"
        assert self.b.columns["text3"].name == "text3"
    
    def test_many_to_one(self):
    
        assert self.c.relations["many"].name == "many"

    def test_duplicate_col_names(self):

        text = Columns(sa.Unicode)
        self.assertRaises(AttributeError,text._set_parent,self.b,"text") 
        
    def test_col_names_added_to_items(self):

        text = Columns(sa.Unicode)
        text._set_parent(self.b,"text2")
        
        assert "text2" in self.b.items.iterkeys()
        assert "text" in self.b.items.iterkeys()
        

