#!/usr/bin/env python
from reformed.columns import *
from nose.tools import assert_raises


class test_fields():
    
    def setUp(self):
        
        class Text2(Field):
        
            def __init__(self, name, *args, **kw):
                
                self.text = Column(sa.Unicode)
                self.text3 = Column(sa.Unicode)

        
        self.b = Text2("col")

        self.ord_relation = Relation("ord", "other", order_by = "a1 desc,a2 asc, a3,a4 desc")
        
    def test_text_filed_no_field_name(self):
        
        assert self.b.columns["text"].name == "text"
        assert self.b.columns["text3"].name == "text3"
    
    def test_duplicate_col_names(self):

        text = Column(sa.Unicode)
        assert_raises(AttributeError,text._set_parent,self.b,"text") 
        
    def test_col_names_added_to_items(self):

        text = Column(sa.Unicode)
        text._set_parent(self.b,"text2")
        
        assert "text2" in self.b.items.iterkeys()
        assert "text" in self.b.items.iterkeys()
    
    def test_split_order_by(self):

        assert self.ord_relation.order_by_list == [["a1","desc"], ["a2", "asc"],
                                                      ["a3",""], ["a4", "desc"]] 

