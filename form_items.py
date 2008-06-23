from string import Template
from form_item_functions import * 


class Form_Item_Maker(object):

	instance = None
	
	def __new__(self):
	
		"""singleton"""
		
		if not self.instance:
			self.instance = object.__new__(self)
		return self.instance


	# templates are the simple stuff
	templates = {

	'textbox' : "<input $class name='$name' id='$name' type='text' onkeypress='select_box(this)' onchange='select_box(this)' value='fill' />",

	'password' : "<input $class name='$name' id='$name' type='password' onkeypress='select_box(this)' onchange='select_box(this)'  value='' />",

	'checkbox' : "<input $class name='$name' id='$name' type='checkbox' onchange='select_box(this)'  value='True' />",

	'submit' : "<input $class name='$name' id='$name' type='submit' value='$label' />",

	'hidden' : "<input name='$name' name='$name' type='hidden' value='fill' />",

	'label' : "<label $class for='$name'>$label</label> ",

	'save_delete' : "<input $class name='${name}_::_save_selected' type='submit' value='save selected' /> <input $class name='${name}_::_delete_selected' type='submit' value='delete selected' />"

	}

	# functions are more complicated they will get passed (form_item, data)
	functions = { 'dropdown' : dropdown,
				  'codelist' : codelist }

	# these are used to set defaults for form item rendering
	# 'class' must be set or else the HTML parser will die '' is fine
	data_defaults = {'class': 'style="color:#900;"'}


	def make_item(self, form_item = None, prefix = None, form_type = None, template_name = None, data = None):

		""" create the HTML for the form item 
			item can be from the templates or functions collections """
	
		# process form_item
		if form_item:
			# auto set data
			data = {
			'name' : prefix + str(form_item.name),
			'label' : str(form_item.label)}
			# get template name
			template_name = str(form_item.item)
		
		# set defaults
		for key in self.data_defaults.keys():
			if not data.has_key(key):
				data[key] = self.data_defaults[key]

		# look up the form item we want
		if self.templates.has_key(template_name):
			out = Template(self.templates[template_name]).safe_substitute(data)	
		elif self.functions.has_key(template_name):
			out = self.functions[template_name](form_item, data)
		else:
			out = "unknown: %s" % template_name
	
		# return the form item html
		if form_type == "grid":
			return "\n<td>%s</td>" % out
		else:
			if data.has_key('label'):
				label = Template(self.templates['label']).safe_substitute(data)
				return "\n<p>%s%s</p>" % (label, out)
			else:
				return "\n<p>%s</p>" % out
	
