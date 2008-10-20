#!/usr/bin/env python
from Columns import *

class test_fields(object):
	
	def setUp(self):
		
		self.a = Text("col")
		
		class Text2(Fields):
		
			text = Columns(sa.Unicode)
		
		self.b = Text2("col")
		
		self.c = ManyToOne("many")
			
	def test_text_field_fieldname(self):
		
		assert self.a.columns["col"].name == "col"
		
	def test_text_filed_no_field_name(self):
		
		assert self.b.columns["text"].name == "text"
	
	def test_many_to_one(self):
	
		assert self.c.relations["many"].name == "many"

class test_table(object):
	
	def setup(self):
		
		self.a = Table("poo", Text("col"))
		
	def test_table(self):
		
		assert self.a.items["col"].name == "col"
	
	