from sqlalchemy import Table, Column, String, Integer, ForeignKey
from sqlalchemy.orm import mapper, eagerload, relation, sessionmaker
import dbconfig


# form
form_table = Table('form', dbconfig.metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String(40))
         )

class Form(object):
	def __init__(self, name = None):
		self.name = name

	def __repr__(self):
		return "<Form('%s')>" % (self.name)

# form_param
form_param_table = Table('form_param', dbconfig.metadata,
		Column('id', Integer, primary_key=True),
		Column('key', String(100)),
		Column('value', String(1000)),
		Column('form_id', Integer, ForeignKey('form.id'))
         )


class Form_param(object):
	def __init__(self, key = None, value = None, form_item_id = None):
		self.key = key
		self.value = value
		self.form_id = form_id

	def __repr__(self):
		return "<Form_item_param('%s','%s','%s')>" % (self.key, self.value, self.form_id)

# form_item
form_item_table = Table('form_item', dbconfig.metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String(100)),
		Column('label', String(40)),
		Column('item', String(40)),
		Column('form_id', Integer, ForeignKey('form.id'))
         )


class Form_item(object):
	def __init__(self, name = None, label = None, item = None, form_id = None):
		self.name = name
		self.label = label
		self.item = item
		self.form_id = form_id

	def __repr__(self):
		return "<Form_item('%s','%s','%s','%s')>" % (self.name, self.label, self.item, self.form_id)


# form_item_param
form_item_param_table = Table('form_item_param', dbconfig.metadata,
		Column('id', Integer, primary_key=True),
		Column('key', String(100)),
		Column('value', String(1000)),
		Column('form_id', Integer, ForeignKey('form_item.id'))
         )


class Form_item_param(object):
	def __init__(self, key = None, value = None, form_id = None):
		self.key = key
		self.value = value
		self.form_id = form_id

	def __repr__(self):
		return "<Form_item_param('%s','%s','%s')>" % (self.key, self.value, self.form_id)


# test
test_table = Table('test', dbconfig.metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String(40)),
		Column('item', String(40))
          )

class Test(object):
	def __init__(self, name = None, item=None ):
		self.name = name
		self.item = item
	def __repr__(self):
		return "<Test('%s','%s')>" % (self.name, self.item)




# mapper stuff
mapper = mapper

mapper(Form_item_param, form_item_param_table) 

mapper(Form_item, form_item_table, properties={'form_item_param':relation(Form_item_param, backref='form_item')}) 

mapper(Form_param, form_param_table) 

#mapper(Form, form_table, properties={'form_param':relation(Form_param, backref='form')}) 

mapper(Form, form_table, properties={'form_item':relation(Form_item, backref='form'), 'form_param':relation(Form_param, backref='form')} )

mapper(Test, test_table) 


# session
Session = sessionmaker(bind=dbconfig.engine, autoflush=True, transactional=True)
session = Session()

