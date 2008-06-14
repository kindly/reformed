from sqlalchemy import Table, Column, String, Integer, ForeignKey, Boolean, DateTime
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
	def __init__(self, key = None, value = None, form_id = None):
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
		Column('form_id', Integer, ForeignKey('form.id')),
		Column('sort_order', Integer),
		Column('active', Boolean)
         )


class Form_item(object):
	def __init__(self, name = None, label = None, item = None, form_id = None, sort_order = None, active  = None):
		self.name = name
		self.label = label
		self.item = item
		self.form_id = form_id
		self.sort_order = sort_order
		self.active = active

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


# User
user_table = Table('user', dbconfig.metadata,
		Column('id', Integer, primary_key=True),
		Column('username', String(40)),
		Column('password', String(40)),
		Column('active', Boolean),
		Column('last_login', String(40)),
		Column('user_group_id', Integer, ForeignKey('user_group.id'))
          )

class User(object):
	def __init__(self, username = None, password = None, active = None, last_login = None, group_id = None ):
		self.username = username
		self.password = password
		self.active = active
		self.last_login = last_login
		self.group_id = group_id
	def __repr__(self):
		return "<User('%s','%s')>" % (self.username, self.password)

# User group
user_group_table = Table('user_group', dbconfig.metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String(40)),
		Column('description', String(250))
          )

class User_group(object):
	def __init__(self, name = None, description=None ):
		self.name = name
		self.description = description
	def __repr__(self):
		return "<User_group('%s','%s')>" % (self.name, self.description)


# User permission 
user_permission_table = Table('user_permission', dbconfig.metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String(40)),
		Column('description', String(250))
          )

class User_permission(object):
	def __init__(self, name = None, description=None ):
		self.name = name
		self.description = description
	def __repr__(self):
		return "<User_permission('%s','%s')>" % (self.name, self.description)


# User group permission 
user_group_permission_table = Table('user_group_permission', dbconfig.metadata,
		Column('user_group_id', Integer, ForeignKey('user_group.id')),
		Column('user_permission_id', Integer, ForeignKey('user_permission.id'))
          )

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

mapper(Form, form_table, properties={'form_item':relation(Form_item, backref='form'), 'form_param':relation(Form_param, backref='form'), 'form_item':relation(Form_item, order_by=[form_item_table.c.sort_order]) } )

mapper(User_group, user_group_table, properties={
	'user_permission':relation(User_permission, secondary = user_group_permission_table, backref='user_group')
})

mapper(User_permission, user_permission_table)

mapper(User, user_table, properties={'user_group':relation(User_group, backref='user')})

mapper(Test, test_table) 


# session
Session = sessionmaker(bind=dbconfig.engine, autoflush=True, transactional=True)
session = Session()

