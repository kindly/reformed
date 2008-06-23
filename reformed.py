#!/usr/bin/env python

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import sessionmaker
import dbconfig
from fields import *
from util import *
from boot_tables import *




class Table(object):
	
	def __init__(self, name, *arg, **kw):
		
		attributesfromdict(locals())  ## args need instance checking
		
	def paramset(self):
		
		columns = []
		
		for column in self.arg:
			columns.append(column.paramset(self.name))
		
		table_params = []
	
		for n,v in self.kw.iteritems():
			table_params.append(Table_param(n,v))

		session =dbconfig.Session()
		
		try :
			params = session.query(Tables).filter_by(name =self.name).one()
		except sa.exceptions.InvalidRequestError:
			params =Tables(self.name,columns,table_params)
			
		session.save_or_update(params)
		session.commit()
		
		session.close()
	
	def create_table_def(self):
		
		columns = []
		
		for column in self.arg:
			if hasattr(column,"columns"):
				columns.append(column.columns())
		
		self.table = sa.Table(self.name, dbconfig.metadata,
							  sa.Column('id' ,   sa.Integer,    primary_key=True),
							  *columns )
	
	def create_class(self,database, table_name):
		
		class table_class(object):
			
			def __init__(self,**kw):
				attributesfromkw(locals())
			
			def validate(self):
				val= {}
				for column in database.tables[table_name].arg:
					if hasattr(column,"validator"):
						for n,v in column.validator(self, table_name, database).iteritems():
							val[n]=v    
				return val 

		setattr(self, self.name,table_class)
		
	def create_mappings(self,database,table_name):
	
		prop = {}
		for column in self.arg:
			if hasattr(column,"parameters"):
				for n,v in column.parameters(table_name, database).iteritems():
					prop[n]=v
				
		orm.mapper(getattr(self, self.name), self.table, properties = prop)
	
	def add_external_columns(self,database, table_name):
	
		for column in self.arg:
			if hasattr(column,"external_column"):
				database.tables[column.other].table.append_column(column.external_column(table_name))

	def add_external_tables(self,database, table_name):
	
		for column in self.arg:
			if hasattr(column,"external_table"):
				column.external_table(table_name)


class Database(object):
	
	def __init__ (self):
		
		session =dbconfig.Session()
		
		self.tables = {}
		
		systables = session.query(Tables)
		
		for tab in systables:
			
			flds = []
			tab_param ={}
			for fld in tab.field:
				
				params = {}
				
				for param in fld.field_param:
					
					params[param.field_param_type.encode("ascii")] = param.field_param_value.encode("ascii")
			
				flds.append(globals()[fld.field_type.encode("ascii")](fld.name, **params))
			
			for tab_par in tab.table_param:
		
				tab_param[tab_par.table_param_type.encode("ascii")] = tab_par.table_param_value.encode("ascii")

			self.tables[tab.name.encode("ascii")] = Table(tab.name.encode("ascii"), *flds, **tab_param)
		
		session.close()

	def __getattr__(self, table):

		return getattr(self.tables[table],table)

	def create_tables(self):
		
		for v in self.tables.itervalues():
			
			v.create_table_def()
	
	
		for v in self.tables.itervalues():
				
				v.add_external_tables(self,v.name)
	

		for v in self.tables.itervalues():

			v.add_external_columns(self,v.name)

		dbconfig.metadata.create_all(dbconfig.engine)

		for v in self.tables.itervalues():

			v.create_class(self,v.name)

		for v in self.tables.itervalues():
			v.create_mappings( self,v.name)
			
	
if __name__ == "__main__":
	
	aa= Table("main_table",
			TextBox("main_text_1", validation = "MaxLength(5)||MaxLength(4)"),
			Integer("main_int"),
			OneToMany("join_one_many","one_many", cascade='all,delete-orphan'),
			ManyToMany("join_many_many","many_many"),
			Index = 'main_text_1')
	bb= Table("one_many", TextBox("one_many_text_1"))
	cc= Table("many_many",TextBox("many_many_text_1"))

	aa.paramset()
	bb.paramset()
	cc.paramset()

	form = Table("form", TextBox("name"),
			OneToMany("form_param","form_param"), OneToMany("form_item","form_item"))
	fromparam = Table("form_param", TextBox("key"), TextBox("value"))
	formitem = Table("form_item" ,TextBox("name") ,
			TextBox("label"),TextBox("item"),
						OneToMany("form_item_param","form_item_param"))

	formitemparam = Table("form_item_param", TextBox("key"),TextBox("value"))

	form.paramset()
	fromparam.paramset()
	formitem.paramset()
	formitemparam.paramset()
	
	data=Database()
	data.create_tables()

	nn = data.main_table(main_text_1="t14324",main_int = 16,
			join_one_many = [data.one_many( one_many_text_1= "one"),
					data.one_many( one_many_text_1= "many")],
			join_many_many = [data.many_many( many_many_text_1= "many"),
				data.many_many( many_many_text_1= "many")])

	session =dbconfig.Session()
	session.save_or_update(nn)
	session.commit()
	session.close()
	
