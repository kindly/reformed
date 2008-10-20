#!/usr/bin/env python
import sqlalchemy as sa

class BaseSchema(object):
	
	
	def __init__(self, type, **kw):
		""" Defines the information needed to make an actual database field """
	
		self.type = type
		self.use_field_name=kw.pop("use_field_name", False)
	
	def _set_name(self,Field, name):
		
		if self.use_field_name:
			self.name = Field.name
		else:
			self.name = name
		


class Columns(BaseSchema):

	
	def _set_parent(self,Field, name):
		
		self._set_name(Field,name)
			
		if self.name in Field.items.iteritems():
			raise "column already in field definition"
		else:
			Field.columns[self.name] = self
			self.field = Field
		
		
class Relations(BaseSchema):
	

	def _set_parent(self,Field, name):
		
		self._set_name(Field,name)
			
		if self.name in Field.items.iteritems():
			raise "column already in field definition"
		else:
			Field.relations[self.name] = self
			self.field = Field
		


class Fields(object):
	
	def __init__(self, name, other = None, secondary =None, *args, **kw):
		""" the base class of all Fields.  A field is a composite of many real database columns"""
		
		self.name = name
		self.columns = {}
		self.relations = {}
		
		for n,v in self.__class__.__dict__.iteritems():
			if not n.startswith("_"):
				v._set_parent(self,n)
	
	def _set_items(self):
		
		items = {}
		items.update(self.columns)
		items.update(self.relations)
		return items
	
	items = property(_set_items)

	def _set_parent(self, Table):
		
		for n,v in self.items.iteritems():
			if n in Table.items.iteritems():
				raise "already an item named %s" % n
				
		Table.fields[self.name] = self
		self.Table = Table
	
class Text(Fields):
	
	text = Columns(sa.Unicode, use_field_name = True)
	
class ManyToOne(Fields):
	
	manytoone = Relations("manytoone",use_field_name = True)
	
	
class Table(object):
	
	def __init__(self,name,*args,**kw):
		
		self.name =name
		
		self.fields = {}
		
		for fields in args:
			fields._set_parent(self)
	
		
	def _set_items(self):
		
		items = {}
		for n,v in self.fields.iteritems():
			for n,v in v.items.iteritems():
				items[n]=v
		return items

	items = property(_set_items)
