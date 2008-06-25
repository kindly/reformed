import sqlalchemy as sa
from sqlalchemy import orm
from validation import Validate
from util import *
from boot_tables import *

class Fields(object):

	def validator (self,object, table_name, database):
		try:
			validation = self.kw["validation"]
		except KeyError:
			return {}
		else:
			return Validate(getattr(object,self.name),validation,self.name, table_name, database)




class Integer(Fields):

	def __init__(self,name, mandatory = True, **kw):
		
		attributesfromdict(locals())

	def columns (self):
		
		return sa.Column(self.name,sa.Integer, nullable = not self.mandatory)

	
	def paramset (self,table_name):
		
		params = [Field_param(  "mandatory" , repr(self.mandatory)),]
		
		for n,v in self.kw.iteritems():
			params.append(Field_param(n,v))
			   
		return Field(self.name,self.__class__.__name__,
					 params
					)

class Date(Fields):
	def __init__(self,name, mandatory = True, **kw):
		attributesfromdict(locals())

	def columns (self):
		
		return sa.Column(self.name,sa.Date, nullable = not self.mandatory)
	
	def paramset (self,table_name):
		
		params = [Field_param(  "mandatory" , repr(self.mandatory)),]
	
		for n,v in self.kw.iteritems():
			params.append(Field_param(n,v))
			   
		return Field(self.name,self.__class__.__name__,
				 params
				)

class Boolean(Fields):

	def __init__(self,name, mandatory = True, **kw):
		
		attributesfromdict(locals())

	def columns (self):
	
		return sa.Column(self.name,sa.Boolean, nullable = not self.mandatory)

	def paramset (self,table_name):
		
		params = [Field_param(  "mandatory" , repr(self.mandatory)),]

		for n,v in self.kw.iteritems():
			params.append(Field_param(n,v))
			 
		return Field(self.name,self.__class__.__name__,
					params
					)


class TextBox(Fields):
	
	def __init__(self,name,length =100, mandatory = True, **kw):
		
		attributesfromdict(locals())
	
	def columns (self):
		
		return sa.Column(self.name,sa.String(self.length), nullable = not self.mandatory)

	def paramset (self,table_name):
		
		params = [Field_param(  "length" , repr(self.length)),
					  Field_param(  "mandatory" , repr(self.mandatory))]
		
		for n,v in self.kw.iteritems():
			params.append(Field_param(n,v))
			   
		return Field(self.name,self.__class__.__name__,
					 params
					)


class OneToMany(Fields):
	
	def __init__(self,name,other, **kw):
		attributesfromdict(locals())
	
	def external_column (self,table_name):
		return  sa.Column(table_name+"_id", sa.Integer, sa.ForeignKey("%s.id"%(table_name)))
	
	def parameters (self, table_name, database):
		kw = self.kw
		params = {}
		mapped_class = getattr(database.tables[self.other], self.other) 

		params[self.name]=orm.relation(mapped_class,**kw)
		return params


	def paramset (self,table_name):

		params = [Field_param(  "other" , self.other)]
		
		for n,v in self.kw.iteritems():
			params.append(Field_param(n,v))
			   
		return Field(self.name,self.__class__.__name__,
				 params)

class ManyToMany(Fields):


	def __init__(self,name,other, **kw):
		attributesfromdict(locals())

	def external_table(self, table_name):
	
		self.table= sa.Table(table_name+"_manytomany_"+self.other, dbconfig.metadata,
				sa.Column(table_name+"_id", sa.Integer, sa.ForeignKey("%s.id"%(table_name))),
				sa.Column(self.other+"_id", sa.Integer, sa.ForeignKey("%s.id"%(self.other))))
		
	def parameters (self, table_name, database):
		params = {}
		mapped_class = getattr(database.tables[self.other], self.other) 
		kw = self.kw
		params[self.name]=orm.relation(mapped_class,secondary=self.table,backref = table_name,**kw) 
		return params

	def paramset (self,table_name):

		params = [Field_param(  "other", self.other)]
		
		for n,v in self.kw.iteritems():
			params.append(Field_param(n,v))
			
		return Field(self.name,self.__class__.__name__,
				 params)
	
	
class ManyToOne(Fields):
	
	def __init__(self,name,other, **kw):
		attributesfromdict(locals())
	
	def columns (self):
		return  sa.Column(self.other+"_id", sa.Integer, sa.ForeignKey("%s.id"%(self.other)))
	
	def parameters (self, table_name, database):
		kw = self.kw
		params = {}
		mapped_class = getattr(database.tables[self.other], self.other) 

		params[self.other]=orm.relation(mapped_class,**kw)
		return params


	def paramset (self,table_name):

		params = [Field_param(  "other" , self.other)]
		
		for n,v in self.kw.iteritems():
			params.append(Field_param(n,v))
			   
		return Field(self.name,self.__class__.__name__,
				 params)
