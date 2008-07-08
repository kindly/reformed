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
			if len(self.columns()) == 1:
				return Validate(getattr(object,self.name),validation,self.name, table_name, database)
			else:
				colnames = {}
				for col in self.columns():
					colnames[col.name] = getattr(object,col.name)
					
				return Validate(colnames,validation,self.name,table_name,database)




class Integer(Fields):

	def __init__(self,name, mandatory = True, **kw):
		
		attributesfromdict(locals())

	def columns (self):
		
		return [sa.Column(self.name,sa.Integer, nullable = not self.mandatory),]

	
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
		
		return [sa.Column(self.name,sa.Date, nullable = not self.mandatory),]
	
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
	
		return [sa.Column(self.name,sa.Boolean, nullable = not self.mandatory),]

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
		
		return [sa.Column(self.name,sa.String(self.length), nullable = not self.mandatory),]

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
	
	def external_column (self,table_name,database):
		
		if database.tables[table_name].kw.has_key("primary_key"):
			columns = []
			for col in database.tables[table_name].table.columns:
				if col.primary_key == True:
					columns.append(sa.Column(col.name, col.type))
			return columns
				
		return  [sa.Column(table_name+"_id", sa.Integer, sa.ForeignKey("%s.id"%(table_name))),]
	
	def external_constraints(self,table_name,database):
		
		if database.tables[table_name].kw.has_key("primary_key"):
			primary_keys = database.tables[table_name].kw["primary_key"].split(",")
			return [sa.ForeignKeyConstraint(primary_keys,
										["%s.%s" % (table_name,a) for a in primary_keys])
					]
			
		
		
		
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
		return  [sa.Column(self.other+"_id", sa.Integer, sa.ForeignKey("%s.id"%(self.other))),]
	
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

class Address(Fields):
	
	def __init__(self,name, **kw):
		attributesfromdict(locals())
		
	def columns (self):
		return [sa.Column("Address_line_1" ,sa.String(100)),
			sa.Column("Address_line_2" ,sa.String(100)),
			sa.Column("Address_line_3" ,sa.String(100))
			]
	

		
		
		
	def paramset (self,table_name):
		
		params = []
		
		for n,v in self.kw.iteritems():
			params.append(Field_param(n,v))
			   
		return Field(self.name,self.__class__.__name__,
					 params
					)
	
