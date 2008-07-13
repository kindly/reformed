#!/usr/bin/python

import formencode
from formencode.htmlfill import FillingParser 
#from formencode import validators
import cgi
from form_items import Form_Item_Maker
import re
import dbconfig
import reformed as r

from form_cache import FormCache
from html import html_wrapper
from wsgistate.memory import session


class Form_Schema(formencode.Schema):

	""" used by the form filler """
	
	name = formencode.validators.String(not_empty=True)

class FormBuilder(object):

	""" this is the parent class of forms and grids  """

	def __init__(self, form_id, form_prefix='', variables={}, base_url=None, caller=None):
	
		if caller:
			self.caller = caller
		else:
			self.caller = None
			
		self.variables = caller.variables
		self.form_id = int(form_id)
		self.form_prefix = form_prefix
		self.base_url = base_url
		self.record_id = int(self.variables['record_id'])
		self.form = self.caller.form_cache.get_form(form_id)
		self.body = ''
		self.defaults = {}
		self.action = ''
		self.subform_params = None
		self.parent_field = '' 
		self.parent_id = ''
	
	def format(self, value):
	
		""" so far this just replaces None with '' """
		
		if value:
			return str(value)
		else:
			return ''
	
	def add_data(self, form_item, data, form_prefix=''):
	
		""" put the data into the defaults for form population """
		
		if str(form_item.name).count('.'):
			(table, field) = form_item.name.split('.')
		else:
			table = field = None
		if data and field and hasattr(data, field):
			self.defaults[form_prefix + str(form_item.name)] = self.format(getattr(data, field))
		else:
			self.defaults[form_prefix + str(form_item.name)] = ""


	def get_form_object(self): 
	
		""" helper function to find the object """
		
		form_object = self.form.params('form_object')
		if (r.data.tables.has_key(form_object)):
			return getattr(r.data, form_object)
		else:
			return None
			

	def set_subform_params(self, params, parent_id):
	
		self.subform_params = params
		self.parent_id = parent_id



	def get_data(self):
	
		""" gets the data for a record or a blank object """
		
		if self.record_id != None and self.rowcount > self.record_id:
			return self.data[self.record_id]
		else:
			if self.rowcount != 0:
				return self.obj()
			else:
				return None



	def process(self):
	
		# FIXME split this up
		
		if self.subform_params:
			filter_by = {self.subform_params['child_id']:self.parent_id}
		else:
			filter_by = None
	
		# get the recordset
		session = dbconfig.Session()
		self.obj = self.get_form_object()
		if self.obj:
			if filter_by:
				self.data = session.query(self.obj).filter_by(**filter_by)
			else:
				self.data = session.query(self.obj)  #.filter_by(**{'id':self.record_id})
			self.data = self.data.order_by(self.obj.c.id)
			session.close()	
			# number of rows in recordset
			self.rowcount = self.data.count() #- 1
		else:
			self.rowcount = 0
		# FIXME this needs to be changed
		# sub/sub/sub forms need to work with the pulling ids out
		# only the las form gets control
		# this should be easy by splitting the sub forms
		# then hive this off into a function :)

		# get the record id
		if self.form_prefix == '': 
			# top level form
			self.record_id = int(self.variables['record_id'])
		else:
			# sub form
			matches = re.findall("%s/%s(\d+):.*" % (self.base_url, self.form_prefix), self.caller.url )
			if matches:
				self.record_id = int(matches[0])
			else:
				self.record_id = 0
			
			
		# record movement
		
		# is this the record that will move?
		if self.variables['sub_data'] == self.form_prefix:
			url_match = True
		elif re.match("%s/%s(\d*):$" % (self.base_url, self.form_prefix), self.caller.url ):
			url_match = True
		else:
			url_match = False

		# only happens on the correct form ;)
		if url_match:
			if self.variables['cmd']:
				if self.variables['cmd'] == 'prev':
					self.record_id -= 1
				elif self.variables['cmd'] == 'next':
					self.record_id += 1
				if self.variables['cmd'] == 'first':
					self.record_id = 0
				elif self.variables['cmd'] == 'last':
					self.record_id = self.rowcount - 1
				elif self.variables['cmd'] == 'new':
					self.record_id = None

			
		# sanity check record_id
		if self.record_id:
			if self.record_id >= self.rowcount:
				self.record_id = self.rowcount - 1
			if self.record_id < 0:
				self.record_id = 0		
	
		if self.form_prefix == '':
			if self.record_id != None:
				self.base_url = '/form/%s/%s' % (self.form_id, self.record_id)
			else: # new record
				self.base_url = self.caller.url[:-1]
		else:
			if self.record_id:
				self.form_prefix += str(self.record_id) + ":"
			else:
				self.form_prefix += ":"
		
		self.href = self.base_url
		if self.form_prefix:
			self.href = self.href +'/' + self.form_prefix



class Grid(FormBuilder):

	""" this is the grid creation class """
	
	def create(self):

		""" called to create the grid 
			the form will be added to the grid's body """
			
		self.child_field = "id"
		# grid header
		self.body += "\n<table border='1'>"
		# header row
		self.header()

		session = dbconfig.Session()
		
#		my_obj = self.get_form_object()

	#	if parent_id and child_field: # some subforms are not connected ie 'cheap grid'
	#		data = session.query(my_obj).filter_by(**{child_field:parent_id})
	#	else:
	#	data = session.query(my_obj)	
	
		self.process()
		
		for row in self.data:
			self.row(row)
		session.close()
		self.row()
		self.body += "\n</table>\n"
		
		# add the buttons
		self.body += self.caller.form_item_maker.make_item(template_name = 'save_delete',
										  data = {'name':self.form_prefix},
										  form_type = 'normal') 

	def header(self):

		""" create the grid table header """
		
		self.body += "\n<tr>"
		self.body += "\n<td>id</td>\n<td>select</td>"  # FIXME i18n
		for form_item in self.form.form_items:
			if form_item.label:
				self.body += "\n<td>%s</td>" % form_item.label
			else:
				self.body += "\n<td>&nbsp;</td>"
		self.body += "\n</tr>"


	def row(self, row=None):	
		
		""" create the individual grid row """
		
		if row:
			record_id = str(getattr(row, self.child_field))
		else:
			record_id = "0" # new row

		form_prefix = self.form_prefix + record_id + ":"
		
		# create the row selector
		self.selector(record_id, form_prefix)
		
		for form_item in self.form.form_items:
			if form_item.name:
				# create item
				self.body += self.caller.form_item_maker.make_item(form_item = form_item,
												  prefix = form_prefix,
												  form_type = 'grid')
				# add data
				self.add_data(form_item, row, form_prefix)			  

		self.body += "\n</tr>"


	def selector(self, record_id, form_prefix):
	
		""" creates the row selector """
		
		self.body += "\n<tr>"
		if record_id != "0":
			self.body += "\n<td>%s</td>" % record_id
		else:
			self.body += "\n<td>+"
			# need to get the parent joining info
			self.body += "\n<input name='%s_::_id_field' type='hidden' value='%s'/><input name='%s_::_id_value' type='hidden' value='%s'/>\n" % (form_prefix, self.parent_field, form_prefix, self.parent_id)
			self.body += "</td>"
			
		self.body += "<td>"
		self.body += "<input type='checkbox' name='%s_::_selected' id='%s_::_selected' value='True' />" % (form_prefix, form_prefix)
		
		self.body += "</td>"




class Form(FormBuilder):

	""" Form object creates the form in it's body """
							
	def buttons(self):
	
		# FIXME move and get so active or not
		self.body += '<p>'
		self.body += '<a href="%s;first">first</a> ' % self.href
		self.body += '<a href="%s;prev">prev</a> ' % self.href
		self.body += '<a href="%s;next">next</a> ' % self.href
		self.body += '<a href="%s;last">last</a> ' % self.href
		self.body += '<a href="%s">refresh</a> ' % self.href
		self.body += '<a href="%s;new">new</a> ' % self.href
		self.body += '</p>'
		
				 	
	def create(self):
	
		""" actually create the form """
	
		self.body += "<div style='border:1px solid #F00;margin:3px 10px;'>"
		
		self.process()
		data = self.get_data()
		
		if data and hasattr(data, 'id'):
			actual_id = str(getattr(data, 'id'))
		else:
			actual_id = 0
		if actual_id=='None':
			actual_id = 0
		self.body += "<input type='hidden' name='%s__id__' value='%s' />" % (self.form_prefix,actual_id)
			
		self.buttons()
		
		for form_item in self.form.form_items:
			
			if form_item.item == 'subform':
				self.subform(form_item, data)
			elif  form_item.name:
				# normal controls
				self.body += self.caller.form_item_maker.make_item(form_item = form_item, prefix = self.form_prefix, form_type = 'normal')
				#add the data
				self.add_data(form_item, data, self.form_prefix)
			else:
				# unknown
				self.body += form_items.unknown(form_item, form_data.field_prefix)
		
		
		self.body += "\n</div>"
		
	def subform(self, form_item, data):
	
		""" called to add in a sub form """
		
		subform_id = self.caller.form_cache.get_id_from_name(form_item.params('subform_name'))
		form_prefix = "%s%s_" % (self.form_prefix, form_item.name)

		# pass the subform some data
		field = form_item.params('parent_id')
		if data and field and hasattr(data, field):
			record_id = str(getattr(data, field))
		else:
			record_id = None
		
		child_id = form_item.params('child_id')
					
		if form_item.params('form_type') == 'grid':
			form = Grid(subform_id, form_prefix, caller=self.caller, base_url=self.base_url)
			form.parent_field = child_id
			form.parent_id = record_id
			pass
		else:
			# join info
			self.body += "\n<input name='%s:_::_id_field' type='hidden' value='%s'/><input name='%s:_::_id_value' type='hidden' value='%s'/>" % (form_prefix, child_id, form_prefix, record_id)
			
			form = Form(subform_id, form_prefix, caller=self.caller, base_url=self.base_url)
			

		
		form.set_subform_params(form_item.form_item_params, record_id)
		
		form.create()	
		self.body += str(form.body)
		self.defaults.update(form.defaults)





class FormObject(object):

	""" this object processes a form 
		saves and deletes as needed
		and creates the form
		holds objects for the FormBuilder objects it produces """
		
	form_cache = FormCache()
	form_item_maker = Form_Item_Maker()
	
		
	def __init__(self, environ):
		self.variables = environ['selector.vars']
		
		self.formdata = cgi.FieldStorage(fp=environ['wsgi.input'],
                        	environ=environ,
                        	keep_blank_values=1)
      	
		self.formdata_linear = ','.join(self.formdata)
		if self.formdata_linear:
			self.save()
			self.delete()           	

		if not self.variables['sub_data']:
			self.variables['sub_data'] = ''
		
		self.url = '/form/%s/%s/%s' % (self.variables['form_id'],
											 self.variables['record_id'],
											 self.variables['sub_data'])
		self.action =''

	def process_single(self, prefix, action):
	
		""" processes a single form (delete or save) """
			
		# get the record_id
		# see if this is a normal form
		if re.search('(^|,)%s__id__($|,)' % prefix,self.formdata_linear):
			record_id = int(self.formdata.getfirst(prefix + '__id__'))
		else:
			# or is it a grid
			matches = re.search(r'.*:(?P<record_id>\d+):$', prefix)
			if matches:
				record_id = int(matches.group('record_id'))

		# find the form object
		form_id = self.find_form(prefix,int(self.variables['form_id']))
		form = self.form_cache.get_form(form_id)
		form_object = form.params('form_object')
		if (r.data.tables.has_key(form_object)):
			obj = getattr(r.data, form_object)
			if action == "save":
				self.save_item(obj, record_id, prefix, form)
			elif action == 'delete':
				self.delete_item(obj, record_id)
		else:
			print "NO OBJECT"	



	def process_multiple(self, prefix, action):
		
		""" processes multiple forms (delete or save) """
		
		# find the form object	
		form_id = self.find_form(prefix,int(self.variables['form_id']))
		form = self.form_cache.get_form(form_id)
		form_object = form.params('form_object')
		if (r.data.tables.has_key(form_object)):
			obj = getattr(r.data, form_object)		
			matches = re.findall(r'(^|,)%s(\d+):_::_selected' % prefix, self.formdata_linear )
			if matches:	
				for	m in matches:
					record_id = int(m[1])
					if action == "save":
						row_prefix = '%s%s:' % (prefix, record_id)
						self.save_item(obj, record_id, row_prefix, form)
					elif action == 'delete':
						self.delete_item(obj, record_id)
		else:
			print "NO OBJECT"
			
				
	def save(self):

		"""see if a save button was pressed and save that thing"""

		matches = re.search(r'(^|,)(?P<prefix>[^,]*)save($|,)',self.formdata_linear) 
		if matches:
			self.process_single(matches.group('prefix'), 'save')
		else: # save many
			matches = re.search(r'(^|,)(?P<prefix>[^,]*)_::_save_selected($|,)',self.formdata_linear) 
			if matches:
				self.process_multiple(matches.group('prefix'), 'save')
				
				
	def save_item(self, obj, record_id, prefix, form):
	
		"""this does the actual saving"""
		
		session = dbconfig.Session()
		if record_id:
			# existing record
			# FIXME check exists
			data = session.query(obj).filter_by(id=record_id).one()
		else:
			# new record
			data = obj()
			
			if prefix:
				id_field = str(self.formdata.getfirst(prefix + '_::_id_field'))
				id_value = str(self.formdata.getfirst(prefix + '_::_id_value'))
			else:
				id_field = str(self.formdata.getfirst('_::_id_field'))
				id_value = str(self.formdata.getfirst('_::_id_value'))

			print "SAVE NEW", ':', id_field, '=', id_value
			setattr(data, id_field, id_value )
			
		for form_item in form.form_items:
			name = str(form_item.name)
			if name.count('.'):
				(table, field) = name.split('.')
				value =  self.formdata.getfirst( prefix + form_item.name)

				# checkboxes are a pain ;)
				if form_item.item == 'checkbox' and value != "True":
					value = False
				print field, '=', value
				setattr(data, field, value )
		session.save_or_update(data)
		session.commit()
		session.close()
		
	def delete(self):

		"""see if a delete button was pressed and save that thing"""

		matches = re.search(r'(^|,)(?P<prefix>[^,]*)delete($|,)',self.formdata_linear) 
		if matches:
			self.process_single(matches.group('prefix'), 'delete')
		else: # save many
			matches = re.search(r'(^|,)(?P<prefix>[^,]*)_::_delete_selected($|,)',self.formdata_linear) 
			if matches:
				self.process_multiple(matches.group('prefix'), 'delete')
		
		
		
	def delete_item(self, obj, record_id):
	
		"""this does the actual delete"""
		
		session = dbconfig.Session()
		# FIXME check exists
		data = session.query(obj).filter_by(id=record_id).one()
		session.delete(data)
		session.commit()
		session.close()
		
		
	
	def find_form(self,prefix, form_id):

		""" given a form items prefix returns the form_id """
		
		if prefix == '':
			# top form
			return(form_id)
		else:
			matches = re.search(r'(?P<prefix>[^:]*)_\d*(?P<remainder>.*)$', prefix)
			if matches:
				form = self.form_cache.get_form(form_id)
				if form.subforms.has_key(matches.group('prefix')):
					form_id = self.form_cache.get_id_from_name(form.subforms[matches.group('prefix')])
					return self.find_form(matches.group('remainder'), form_id)
			return form_id	
				
				
	
	def action_form(self):
	
		""" called to process and create the form """
		
		form_id = self.variables['form_id']
		if self.form_cache.get_form(form_id).params('form_view') == 'grid':
			form = Grid(form_id, caller=self)
		else:
			form = Form(form_id, caller=self)
		form.create()
		self.body = form.body
		self.defaults = form.defaults
		self.populate_data()
	
	def populate_data(self):

		""" populates the forms fiel data """
		
		# fill out form
		# if the HTML is broken an error is thrown
		# we'll display the broken HTML to aid debugging
		
		self.body += " " # need this to stop parser removing final tag
		try:
			parser = FillingParser(self.defaults)
			parser.feed(str(self.body))
			parser.close()
			self.body = parser.text()
			self.body = '\n<form action="%s" method="post">%s\n</form>' % (self.action, self.body)
		except:
			print "PARSER ERROR:"
			self.body = str(self.body)
			self.body = '\n<h1>Parser error encountered</h1><p>html that triggered error is...</p><pre>%s</pre>' % cgi.escape(self.body)
	
	
@session()
@html_wrapper
def save(environ, start_response):

	""" this is called by our application """
	
	form_object = FormObject(environ)
	form_object.action_form()
	environ['reformed']['body'] = form_object.body
	return(environ, start_response)
	
@session()
@html_wrapper	
def list(environ, start_response):

	body=''
	session = dbconfig.Session()
	obj = r.data.form
	data = session.query(obj).all()
	for form in data:
		body += " <a href='/form/%s/1'>1</a>" % str(form.id)
		body += " <a href='/form/%s/0'>new</a>" % str(form.id)
		body += " <a href='/form/1/%s'>%s</a><br />" % (str(int(form.id) - 1), str(form.name) )
	body += "<a href='/form/1/0'>new</a><br />"
	session.close()
	body = '<b>Forms</b><br />' + body 
	environ['reformed']['body'] = body
	pass
	
	
	
