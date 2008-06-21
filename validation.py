from formencode.validators import *
import formencode

def Validate(value, validation,name):

	validation_array = validation.split("||")
	errors = []

	for validation in validation_array:


		exec ("valid = %s" %(validation))
	
		try:
			valid.to_python(value)
		except formencode.Invalid,e :
			errors.append(e.msg)
		

	if errors:
		return {name: errors}
	else:
		return {}








