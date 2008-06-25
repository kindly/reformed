from formencode.validators import *
import formencode
import dbconfig
import sqlalchemy as sa

def Validate(value, validation,name, table_name, database):
	
	state = {"name" :name, "table_name" : table_name, "database": database}
	validation_array = validation.split("||")
	errors = []

	for validation in validation_array:


		exec ("valid = %s" %(validation))
	
		try:
			valid.to_python(value,state)
		except formencode.Invalid,e :
			errors.append(e.msg)
		

	if errors:
		return {name: errors}
	else:
		return {}


class Unique(FancyValidator):
	
	def _to_python(self, value, state):
		
		session =dbconfig.Session()
		object_class = getattr(state["database"],state["table_name"])
		try:
			query = session.query(object_class).filter("%s=='%s'"%( state["name"],value)).one()
		except sa.exceptions.InvalidRequestError:
			return value
		
		raise formencode.Invalid("value not unique", value, state)
			




