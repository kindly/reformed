#/usr/bin/python

import formencode
from formencode.htmlfill import FillingParser 
from formencode import validators
import cgi
from form_items import Form_Item_Maker
import re
import dbconfig
import reformed as r
from form_cache import FormCache

form_cache = FormCache()
form_item_maker = Form_Item_Maker()


class FormData(object):

	""" this does some magic I should understand ;)
		somewhere to pass some variables"""
	
	pass		
		
def list():
	body=''
	session = dbconfig.Session()
	obj = r.data.form
	data = session.query(obj).all()
	for form in data:
		body += " <a href='/view/%s/1'>1</a>" % str(form.name)
		body += " <a href='/view/%s/0'>new</a>" % str(form.name)
		body += " <a href='/view/form/%s'>%s</a><br />" % (str(form.id), str(form.name) )
	body += "<a href='/view/1/0'>new</a><br />"
	session.close()
	return '<b>Forms</b><br />' + body 


class Form_Schema(formencode.Schema):
	name = validators.String(not_empty=True)

def save(environ):
	record_id = int(environ['selector.vars']['record_id'])
#	form_name = environ['selector.vars']['form_name']
	form_id = environ['selector.vars']['form_id']
	formdata = cgi.FieldStorage(fp=environ['wsgi.input'],
                            	environ=environ,
                            	keep_blank_values=1)

	# save data if there is some form data
	if formdata.keys():
		saved_id = save_form(formdata, form_id, record_id)
		
	# our redirect
	if record_id == 0 and saved_id:
		record_id = saved_id
		
	environ['selector.vars']['record_id'] = record_id
	return view(environ)
	#return "/view/%s/%s" % ( form_id, record_id )


def save_form(formdata, form_id, record_id, field_prefix=''):

	saved_id = 0
	form = form_cache.get_form(form_id)

	formdata_linear = ','.join(formdata)
	tmp_objname = form.params('form_object')
	
	session = dbconfig.Session()

	# my_field_prefix allows different prefixes, 
	# grids on their own (not subforms) having a 'special' prefix
	m =	re.search(r'^(.*_)0:',field_prefix)
	if m and m.group(1):
		my_field_prefix = m.group(1)
	else:
		my_field_prefix = field_prefix


	# SAVE
	# see if a save button has been pressed and force that record
	m = re.search(r'(^|,)(\d+):save', formdata_linear )
	if m:
		record_id = int(m.group(2))
		field_prefix = `record_id` + ':'
	# save data
	if tmp_objname and (m or formdata.has_key(field_prefix + 'save')):
		saved_id = save_record(session, tmp_objname, record_id, field_prefix, bool(m), form, formdata)

	# grid save selected
	if formdata.has_key(my_field_prefix + '_::_save_selected'):

		matches = re.findall(r'(^|,|_)(\d+):_::_selected', formdata_linear )
		if matches:	
			for	m in matches:
				print "save selected", int(m[1])
				save_record(session, tmp_objname, int(m[1]), my_field_prefix + str(m[1]) + ":", True, form, formdata)

				
	# DELETE
	# see if a delete button has been pressed and force that record
	m = re.search(r'(^|,)(\d+):delete', formdata_linear )
	if m:
		record_id = int(m.group(2))
		field_prefix = `record_id` + ':'		
	# delete record
	if tmp_objname and (m or formdata.has_key(field_prefix + 'delete')):
		delete_record(session, tmp_objname, record_id)

	# grid delete selected
	if formdata.has_key(my_field_prefix + '_::_delete_selected'):
		matches = re.findall(r'(^|,)' + my_field_prefix + '(\d+):_::_selected', formdata_linear )
		if matches:	
			for	m in matches:
				if int(m[1]) != 0:
					print "delete selected", int(m[1])
					delete_record(session, tmp_objname, int(m[1]) )

	# look for subforms
	for form_item in form.form_items:
		if str(form_item.item) == 'subform':
			child_object = form_item.params("child_object")
			if r.data.tables.has_key(child_object):
				my_obj = getattr(r.data, child_object)  #FIXME if not found
	
				if form_item.params('parent_id'): # some subforms are not connected ie 'cheap grids'
					child_id = form_item.params('child_id')
					data = session.query(my_obj).filter_by(**{child_id:record_id}).all()
				else:
					data = session.query(my_obj).all()
			
				subform_id = form_cache.get_id_from_name(form_item.params('subform_name'))
				# existing obj
				for obj in data:
					save_form(formdata, subform_id, obj.id, "%s%s_%s:" % (field_prefix, form_item.name, obj.id))
				# new
				save_form(formdata, subform_id, 0, "%s%s_0:" % (field_prefix, form_item.name))

	return saved_id


def save_record(session, obj, record_id, field_prefix, return_zero, form, formdata):
	if (r.data.tables.has_key(obj)):
		my_obj = getattr(r.data, obj)
		print "record_id: %s" % record_id
		if record_id != 0:
			# get object
			print 'SAVE'
			data = session.query(my_obj).filter_by(id=record_id).one()
		else:
			# create object
			print 'NEW'
			data = my_obj()
			# set the link data

			if field_prefix:
				id_field = str(formdata.getfirst(field_prefix + '_::_id_field'))
				id_value = str(formdata.getfirst(field_prefix + '_::_id_value'))
			else:
				id_field = str(formdata.getfirst('_::_id_field'))
				id_value = str(formdata.getfirst('_::_id_value'))
			if id_value != "0": # FIXME this is a quick hack for none linked forms like the user groups it may come back to haunt me ;p
				print data, ':', id_field, '=', id_value
				setattr(data, id_field, id_value )

		for form_item in form.form_items:
			name = str(form_item.name)
			if name.count('.'):
				(table, field) = name.split('.')
		
				if str(form_item.item) == 'codelist':
					# we want to get the data for our code list
					# need to find the query to make and the object etc
					flag_table = form_item.params("flag_table")
					flag_table_id_field = form_item.params("flag_table_id_field")
					code_table_id_field = form_item.params("code_table_id_field")
					code_table = form_item.params("code_table")
					
					if (r.data.tables.has_key(code_table)):
						code_table_obj = getattr(r.data, code_table)
						flag_table_obj = getattr(r.data, flag_table)
						if record_id != 0:
							#session = dbconfig.Session()
							code_table_data = session.query(code_table_obj).all() 

							#session.close()
							# ok so now we have the record for this code list
							# lets set the defaults
							for row in code_table_data:
								form_name = field_prefix + str(form_item.name) + ":" + str(row.id)
								flag_table_data = session.query(flag_table_obj).filter_by(**{flag_table_id_field:record_id, code_table_id_field:row.id}).all() 
								if flag_table_data:
									if not formdata.getvalue(form_name):
										session.delete(flag_table_data[0])
								else:
									if formdata.getvalue(form_name):
										flag_table_data = flag_table_obj()
										setattr(flag_table_data, code_table_id_field, row.id)
										setattr(flag_table_data, flag_table_id_field, record_id)
										setattr(flag_table_data, 'active', True)
										setattr(flag_table_data, 'sort_order', 0)
										session.save(flag_table_data)
				
				elif hasattr(data, field):
					# update object
					if form_item.name:
						name = field_prefix + name
					value = str(formdata.getvalue(name))
					# checkboxes are a pain ;)
					if form_item.item == 'checkbox' and value != "True":
						value = False
					
					print "update: %s=%s" % (field, value)
					setattr(data, field, value )
						
		session.save_or_update(data)
		session.commit()
		if return_zero:
			saved_id = 0
		else:
			saved_id = data.id
		return saved_id
					
				
def delete_record(session, obj, record_id):

	if (r.data.tables.has_key(obj)):
		my_obj = getattr(r.data, obj)
		try:
			# create object to delete it
			data = session.query(my_obj).filter_by(id=record_id).one()
			session.delete(data)
			session.commit()
		except:
			print "record doesn't exist"

	
			
			
				
def view(environ):

	record_id = int(environ['selector.vars']['record_id'])
	# initiation
	
	form_data = FormData()
	form_data.form_type = 'normal'
	form_data.record_id  = record_id
#	form_data.form_name = environ['selector.vars']['form_name']
	form_data.field_prefix = ''
	form_data.form_type = ''
	form_data.form_id = environ['selector.vars']['form_id']
	body='' # this will be the form
	defaults = {} # this will be the data

	# FIXME check if the form exists, also we want 
	# to know the action at this point for the form
	# this is a dirty hack that wants to be sorted
	if form_data.form_id == "5":
		form_action  = "/login"
	else:
		form_action = "/save/%s/%s"  % (form_data.form_id, form_data.record_id)
	# create the form 
	form = form_cache.get_form(form_data.form_id) #FIX ME THIS ONLY USED TO GET PARAMS

	if form.params('form_view') == 'grid':
		(form_html, form_data) = grid(form_data.form_id, form_data.record_id, 'id', '', defaults) 
	else:
		(form_html, form_data) = create_form(environ, form_data, defaults)
	
	body += form_html 
	body += " " # need this to stop parser removing final tag

	# fill out form
	# if the HTML is broken an error is thrown
	# we'll display the broken HTML to aid debugging
	try:
		parser = FillingParser(form_data)
		parser.feed(str(body))
		parser.close()
		body = parser.text()
		body = '\n<form action="%s" method="post">%s\n</form>' % (form_action, body)
	except:
		print "PARSER ERROR:"
		body = str(body)
		body = '\n<h1>Parser error encountered</h1><p>html that triggered error is...</p><pre>%s</pre>' % cgi.escape(body)
	return '%s' % body

def grid(form_id, parent_id = None, child_field = None, field_prefix = '', defaults = {}):

	form = form_cache.get_form(form_id)
	# grid header
	body = "\n<table border='1'>"
	# header row
	body += grid_header(form)

	# ok get the data to spit out
	session = dbconfig.Session()
	form_object = form.params('form_object')
	if (r.data.tables.has_key(form_object)):
		my_obj = getattr(r.data, form_object)

	if parent_id and child_field: # some subforms are not connected ie 'cheap grid'
		data = session.query(my_obj).filter_by(**{child_field:parent_id}).all()
	else:
		data = session.query(my_obj).all()	
	for row in data:
		(html, defaults) = grid_row(row, field_prefix, 'id', form, defaults, parent_id, child_field) #FIXME assumed always 'id' that is the key
		body += html
	# extra row
	# need the parent joining info
	(html, defaults) = grid_row(None, field_prefix, 'id', form, defaults, parent_id, child_field) #FIXME assumed always 'id' that is the key
	body += html		
	body += "\n</table>\n"
	# add the buttons
	body += form_item_maker.make_item(template_name = 'save_delete',
									  data = {'name':field_prefix},
									  form_type = 'normal') 
	return (body, defaults)

def grid_row(row, field_prefix, child_field, form, defaults, parent_id, parent_field):	
		
		if row:
			record_id = str(getattr(row, child_field))
		else:
			record_id = "0" # new row

		my_field_prefix = field_prefix + record_id + ":"
		body = "\n<tr>"
		if record_id != "0":
			body += "\n<td>%s</td>" % record_id
		else:
			body += "\n<td>+"
			# need to get the parent joining info
			body += "\n<input name='%s_::_id_field' type='hidden' value='%s'/><input name='%s_::_id_value' type='hidden' value='%s'/>\n" % (my_field_prefix, parent_field, my_field_prefix, parent_id)
			body += "</td>"
			
		body += "<td>"
		body += "<input type='checkbox' name='%s_::_selected' id='%s_::_selected' value='True' />" % (my_field_prefix, my_field_prefix)
		
		body += "</td>"
		
		
		for form_item in form.form_items:
			if form_item.name:
				body += form_item_maker.make_item(form_item = form_item,
												  prefix = my_field_prefix,
												  form_type = 'grid')
		body += "\n</tr>"

		# get data
		for form_item in form.form_items:
			if str(form_item.name).count('.'):
				(table, field) = form_item.name.split('.')
			else:
				table = field = None
			if row and field and hasattr(row, field):
				defaults[my_field_prefix + str(form_item.name)] = str(getattr(row, field))
			else:
				defaults[my_field_prefix + str(form_item.name)] = ""
				
		return (body, defaults)
			
def grid_header(form):

	body = "\n<tr>"
	body += "\n<td>id</td>\n<td>select</td>"  # FIXME i18n
	for form_item in form.form_items:
		if form_item.label:
			body += "\n<td>%s</td>" % form_item.label
		else:
			body += "\n<td>&nbsp;</td>"
	body += "\n</tr>"
	return body


def create_form(environ, form_data, defaults):

	tmp_objname = 'Form_item'	
	msg = ''
	body = ""

	print "###### NEW FORM", form_data.record_id, form_data.form_id 

	# get the form data	
	form = form_cache.get_form(form_data.form_id)	
	if form: # FIXME  I really need to split this bugger up some more
		tmp_objname = form.params('form_object')

		# create the form


		body += "<div style='border:1px solid #F00;margin:3px 10px;'>"
		for form_item in form.form_items: 
			# subforms
			if form_item.item == 'subform':

				if form_data.record_id or form_item.params('show') == "true":  
				# we don't want child forms that have no immediate parent
				# unless 'show' param = true
					if form_item.params('form_type') == 'grid':
						# grid
						my_field_prefix =  "%s%s_" % (form_data.field_prefix, form_item.name)

						(form_html, defaults) = grid(form_cache.get_id_from_name(form_item.params('subform_name')),
													form_data.record_id,
													form_item.params('child_id'),
													my_field_prefix,
													defaults)
						body += form_html
					else:				
						# normal
						body += "<p>%s</p>" % form_item.label
						
						sub_form_data = FormData()
						sub_form_data.form_id = form_cache.get_id_from_name(form_item.params('subform_name'))
						child_object = form_item.params('child_object')
						if (r.data.tables.has_key(child_object)):
							my_obj = getattr(r.data, child_object)
				
							sub_form_data.form_type = 'continuous'

							child_id = form_item.params('child_id')
							session = dbconfig.Session()
							if form_item.params('parent_id'): # some subforms are not connected ie 'cheap grids'
								data = session.query(my_obj).filter_by(**{child_id:form_data.record_id}).all()
							else:
								data = session.query(my_obj).all()
							session.close()
							for obj in data:
								sub_form_data.record_id = obj.id
								sub_form_data.field_prefix = "%s%s_%s:" % (form_data.field_prefix, form_item.name, obj.id)
								(form_html, defaults) = create_form(environ, sub_form_data, defaults)
								body += form_html
							if child_id:
								sub_form_data.record_id = 0
								sub_form_data.field_prefix = "%s%s_%s:" % (form_data.field_prefix, form_item.name, 0)
								body += "\n<input name='%s_::_id_field' type='hidden' value='%s'/><input name='%s_::_id_value' type='hidden' value='%s'/>" % (sub_form_data.field_prefix, child_id, sub_form_data.field_prefix, form_data.record_id)
								(form_html, defaults) = create_form(environ, sub_form_data, defaults)
								body += form_html

			elif  form_item.name:
				# normal controls
				body += form_item_maker.make_item(form_item = form_item, prefix = form_data.field_prefix, form_type = 'normal')
			
			else:
				# unknown
				body += form_items.unknown(form_item, form_data.field_prefix)

		body += "\n</div>"


		# get data or defaults
		formdata = None
		if (r.data.tables.has_key(tmp_objname)):
			my_obj = getattr(r.data, tmp_objname)
			
			if form_data.record_id != 0:
				try:	
					print 	'looking for %s' % form_data.record_id
					session = dbconfig.Session()
					formdata = session.query(my_obj).filter_by(id=form_data.record_id).one() 
					session.close()
				except: #FIXME better handeling of this as save buggered by this i imagine
						# seems this may be useful behaviour with code tables for now
						# needs keeping an eye on
					print "## ERROR ## record not found or something"

		for form_item in form.form_items:
		
			if str(form_item.name).count('.'):
				(table, field) = form_item.name.split('.')
			else:
				table = field = None
				
			# have we got a special item like a code list?
			if str(form_item.item) == 'codelist':
			
				# we want to get the data for our code list
				# need to find the query to make and the object etc
				code_list_table = form_item.params("flag_table")
				code_list_id_field = form_item.params("flag_table_id_field")
				code_table_id_field = form_item.params("code_table_id_field")
						
				if (r.data.tables.has_key(code_list_table)):
					code_list_obj = getattr(r.data, code_list_table)
					if form_data.record_id != 0:

						session = dbconfig.Session()
						# FIXME want to do a; code_table_id_field is not null on this next line
						code_list_data = session.query(code_list_obj).filter_by(**{code_list_id_field:form_data.record_id}).all() 
						session.close()
						# ok so now we have the record for this code list
						# lets set the defaults
						for row in code_list_data:
							defaults[form_data.field_prefix + str(form_item.name) + ":" + str(getattr(row, code_table_id_field))] = "True"
					
			# normal items				
			elif form_item.active and formdata and field and hasattr(formdata, field):
				defaults[form_data.field_prefix + str(form_item.name)] = str(getattr(formdata, field))
				
			# no item found
			else:
				defaults[form_data.field_prefix + str(form_item.name)] = ""
		
			msg += "<br />"
	else:
		body += "<p>nothing to show</p>"	
		
	return (body, defaults)


