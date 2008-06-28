from formencode.validators import *
import formencode
import dbconfig
import sqlalchemy as sa

class State:
	pass

def Validate(value, validation,name, table_name, database):
	
	state = State()
	state.name =name
	state.table_name = table_name
	state.database = database
	validation_array = validation.split("||")
	state.full_dict = value
	errors = {}
		
	for validation in validation_array:


		exec ("valid = %s" %(validation))
	
		try:
			valid.to_python(value,state)
		
		except formencode.Invalid,e :
			if e.error_dict == None:
				if errors.has_key(name):
					errors[name].append(e)
				else:
					errors[name] = [e,]
			else:
				for n, v in e.error_dict.iteritems():
					
					if errors.has_key(n):
						errors[n].append(v)
					
					else:
						errors[n] = [v,]
				
	
	return errors


	
	

class Unique(FancyValidator):
	
	def _to_python(self, value, state):
		
		session =dbconfig.Session()
		object_class = getattr(state.database,state.table_name)
		try:
			query = session.query(object_class).filter("%s=='%s'"%( state.name,value)).one()
		except sa.exceptions.InvalidRequestError:
			return value
		
		raise formencode.Invalid("value not unique", value, state)
			
class Address_valid(formencode.Schema):
	
	Address_line_1 = MaxLength(4)
	Address_line_2 = MaxLength(3)
	Address_line_3 = MaxLength(3, not_empty = True)
	



