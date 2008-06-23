from formencode.validators import *
import formencode
import dbconfig

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








