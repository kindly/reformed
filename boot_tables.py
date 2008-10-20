import sqlalchemy as sa
from sqlalchemy import orm
import dbconfig
from util import *


if "tables" not in dbconfig.metadata.tables:
	tables = sa.Table("tables", dbconfig.metadata,
			sa.Column('id', sa.Integer, primary_key=True),
			sa.Column("name", sa.types.String(100), nullable=False, unique = True)
			)

	table_param = sa.Table("table_param", dbconfig.metadata,
			sa.Column( 'id' ,   sa.Integer,    primary_key=True),     
			sa.Column('table_id', sa.Integer, sa.ForeignKey("tables.id")),
			sa.Column('table_param_type', sa.String(100), nullable = False),
			sa.Column('table_param_value', sa.String(100), nullable = False))


	field  = sa.Table("field", dbconfig.metadata,
			sa.Column('id', sa.Integer, primary_key=True),
			sa.Column("name", sa.types.String(100), nullable=False),
			sa.Column("field_type", sa.types.String(100), nullable =False),
			sa.Column("table_id", sa.Integer, sa.ForeignKey("tables.id")))

	field_param = sa.Table("field_param", dbconfig.metadata,
			sa.Column( 'id' ,   sa.Integer,    primary_key=True),     
			sa.Column('field_id', sa.Integer, sa.ForeignKey("field.id")),
			sa.Column('field_param_type', sa.String(100), nullable = False),
			sa.Column('field_param_value', sa.String(100), nullable = False))
	dbconfig.metadata.create_all(dbconfig.engine)
else:
	tables = dbconfig.metadata.tables["table"]
	table_param = dbconfig.metadata.tables["table_param"]
	field = dbconfig.metadata.tables["field"]
	field_param = dbconfig.metadata.tables["field_param"]



class Tables(object):
	def __init__(self,name, field,table_param):
		attributesfromdict(locals())
	def __repr__(self):
		return repr(self.__class__) + self.name
	
class Table_param(object):
	def __init__(self,table_param_type,table_param_value):
		attributesfromdict(locals())
	def __repr__(self):
		return repr(self.__class__) + self.name
	
class Field(object):
	def __init__(self,name,field_type, field_param):
		attributesfromdict(locals())
	def __repr__(self):
		return repr(self.__class__) + self.name +self.field_type

class Field_param(object):
	def __init__(self,field_param_type,field_param_value):
		attributesfromdict(locals())
	def __repr__(self):
		return repr(self.__class__) +   self.field_param_type + self.field_param_value   
	
	
orm.mapper(Tables, tables, properties={
		'field':orm.relation(Field),
		'table_param':orm.relation(Table_param)
	})

orm.mapper(Table_param, table_param)


orm.mapper(Field, field, properties={
		'field_param':orm.relation(Field_param)
		  })

orm.mapper(Field_param,field_param)




