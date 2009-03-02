#!/usr/bin/env python
from reformed.columns import *
from nose.tools import assert_raises


class test_fields():
    
    def setUp(self):
        
        class Text2(Field):
        
            def __init__(self, name, *args, **kw):
                
                self.text = Column(sa.Unicode)
                self.text3 = Column(sa.Unicode)

                super(Text2,self).__init__(name, *args, **kw)
        
        self.b = Text2("col")
        
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

