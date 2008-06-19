#/usr/bin/python

#import reformed.data as data
from sqlalchemy.orm import eagerload
import formencode
from formencode.htmlfill import FillingParser
from formencode import validators
import cgi
import form_items
import re
import dbconfig
import reformed as r

# basic form cache start

form_cache = {}


def get_form_schema(form_id):

	"""read and cache form data including getting form params into __dict__"""

	global form_cache
	#form_cache = {}
	if form_cache.has_key(form_id):
		# already in the cache
		print "@@ using CACHE form(%s)" % form_id
	else:
		# we need to get the data
		session = dbconfig.Session()
		form_cache[form_id] = {}
		try:
			form_cache[form_id]['form'] = session.query(r.data.form).options(eagerload('form_param'), eagerload('form_item'), eagerload('form_item.form_item_param')).filter_by(id=form_id).one() 

			# params (form)
			form_cache[form_id]['form_params'] = get_params( form_cache[form_id]['form'] )
			# params (form_item)
			form_cache[form_id]['item_params'] = {}
			for form_item in form_cache[form_id]['form'].form_item:
				# FORM_ITEM PARAM
				form_cache[form_id]['item_params'][int(form_item.id)] = form_items.get_params(form_item)
			print "@@ CACHE form(%s)" % form_id
		except:	 
			print "CACHE nothing found"
		session.close()	
	return form_cache[form_id]

def get_form_param(form_id, param):

	# do we have the data in the cache if not get it?
	if not form_cache.has_key(form_id):
		get_form_schema(form_id)
	
	if form_cache[form_id]['form_params'].has_key(param):
		return form_cache[form_id]['form_params'][param]
	else:
		return None
		
		

def get_params(form):
	print "GETTING FORM PARAMS - %s" % form
	params = {}
	for p in form.form_param:
		if p.key:
			print "%s = '%s'" % (p.key, p.value)
			params[str(p.key)] = str(p.value)
	return params




def list():
	body=''
	session = dbconfig.Session()
	obj = r.data.form
	data = session.query(obj).all()
	for form in data:
		body += "<a href='/view/1/%s'>%s</a><br />" % (str(form.id), str(form.name) )
	body += "<a href='/view/1/0'>new</a><br />"
	session.close()
	return '<b>Forms</b><br />' + body 


class Form_Schema(formencode.Schema):
	name = validators.String(not_empty=True)

def save(environ):
	record_id = int(environ['selector.vars']['table_id'])
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
	print "@@@@@@@@ ",record_id , saved_id
	return "/view/%s/%s" % ( form_id, record_id )



def save_form(formdata, form_id, table_id, field_prefix=''):

	print "SAVING FORM DATA datasheet"
	saved_id = 0
	session = dbconfig.Session()

	# get the form data	
	form = get_form_schema(form_id)

	if form['form_params'].has_key('form_object'):
		tmp_objname = form['form_params']['form_object']
	else:
		tmp_objname = None

	print "prefix", field_prefix
	print "object", tmp_objname

	# datagrid
	# see if a save button has been pressed and force that record
	formdata_linear = ','.join(formdata)
	print formdata_linear
	m = re.search(r'$|,(\d+):save', formdata_linear )
	if m.group(1):
		print m.group(1)
		table_id = int(m.group(1))
		field_prefix = `table_id` + ':'
	# save data
	if tmp_objname and (m.group(1) or formdata.has_key(field_prefix + 'save')):
		print "gg"
		if (r.data.tables.has_key(tmp_objname)):
			my_obj = getattr(r.data, tmp_objname)
			print "table_id: %s" % table_id
			if table_id != 0:
				# get object
				print 'SAVE'
				data = session.query(my_obj).filter_by(id=table_id).one()
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
				else:
					print "suppressed id writing"
			for form_item in form['form'].form_item:
				name = str(form_item.name)
				if name.count('.'):
					(table, field) = name.split('.')
					if  form_item.active and hasattr(data, field): #FIXME need to test if the does protect inactive fields from a hack
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
			if m:
				saved_id = 0
			else:
				saved_id = data.id

	# datagrid
	# see if a delete button has been pressed and force that record
	m = re.search(r'$|,(\d+):delete', formdata_linear )
	if m.group(1):
		print "kkkkkk", m.group(1), m
		table_id = int(m.group(1))
		field_prefix = `table_id` + ':'			
	# delete record
	if tmp_objname and (m.group(1) or formdata.has_key(field_prefix + 'delete')):
		if (r.data.tables.has_key(tmp_objname)):
			my_obj = getattr(r.data, tmp_objname)
			# create object to delete it
			print 'DELETE'
			data = session.query(my_obj).filter_by(id=table_id).one()
			session.delete(data)
			session.commit()


	# look for subforms
	for form_item in form['form'].form_item:
		if str(form_item.item) == 'subform':
			# subform
			p = form['item_params'][form_item.id] 
			if (r.data.tables.has_key(p['child_object'])):
				my_obj = getattr(r.data, p['child_object'])  #FIXME if not found
	
			if p.has_key('parent_id'): # some subforms are not connected ie 'cheap datasheets'
				data = session.query(my_obj).filter_by(**{p['child_id']:table_id}).all()
			else:
				data = session.query(my_obj).all()
								

			# existing obj
			for obj in data:
				pass
				save_form(formdata, p['subformID'], obj.id, "%s%s_%s:" % (field_prefix, form_item.name, obj.id))
			# new
			save_form(formdata, p['subformID'], 0, "%s%s_0:" % (field_prefix, form_item.name))

	return saved_id





def view(environ):
	tab_id = int(environ['selector.vars']['table_id'])


	# initiation
	form_render_data = {}
	form_render_data['form_type'] = 'normal'
	form_render_data['table_id']  = tab_id
	form_render_data['form_id'] = environ['selector.vars']['form_id']
	form_render_data['field_prefix'] = ''
	form_render_data['form_type'] = ''
	
	body='' # this will be the form
	defaults = {} # this will be the data

	# FIXME check if the form exists, also we want to know the action at this point for the form
	# this is a dirty hack that wants to be sorted
	if form_render_data['form_id'] == "5":
		form_action  = "/login"
	else:
		form_action = "/save/%s/%s"  % (form_render_data['form_id'], tab_id)
	# create the form 
	if get_form_param(form_render_data['form_id'], 'form_view') == 'grid':
		(form_html, form_data) = datasheet(form_render_data['form_id'], tab_id, 'id', '', defaults) #FIXME want to have 'straight' datasets
	else:
		(form_html, form_data) = create_form(environ, form_render_data, defaults)
	
	body += form_html 
	body += " " # need this to stop parser removing final tag
	

	# fill out form
	parser = FillingParser(form_data)
	parser.feed(str(body))
	parser.close()
	body = parser.text()
	#print repr(defaults)
	
	body = '\n<form action="%s" method="post">%s\n</form>' % (form_action, body)
	return '%s' % body

def datasheet(form_id, parent_id = None, child_field = None, field_prefix = '', defaults = {}):

	print "@@@@",  parent_id, child_field
	form = get_form_schema(form_id)
		# datasheet header
	body = "\n<table border='1'>"
	# header row
	body += datasheet_header(form_id, form)

	# ok get the data to spit out
	session = dbconfig.Session()
	
	p = form['form_params']
	print repr(p)
	if (r.data.tables.has_key(p['form_object'])):
		my_obj = getattr(r.data, p['form_object'])
	#my_obj = r.data.user_group
	if parent_id and child_field: # some subforms are not connected ie 'cheap datasheets'
		data = session.query(my_obj).filter_by(**{child_field:parent_id}).all()
	else:
		data = session.query(my_obj).all()	
	for row in data:
		(html, defaults) = datasheet_row(row, field_prefix, 'id', form, defaults, parent_id, child_field) #FIXME assumed always 'id' that is the key
		body += html
	# extra row
	# need to get the parent joining info
	#body += "\n<input name='%s0:_::_id_field' type='hidden' value='%s'/><input name='%s0:_::_id_value' type='hidden' value='%s'/>" % (field_prefix, child_field, field_prefix, parent_id)
	(html, defaults) = datasheet_row(None, field_prefix, 'id', form, defaults, parent_id, child_field) #FIXME assumed always 'id' that is the key
	body += html		
	body += "\n</table>\n"
	
	return (body, defaults)

def datasheet_row(row, field_prefix, child_field, form, defaults, parent_id, parent_field):	
		
		if row:
			record_id = str(getattr(row, child_field))
		else:
			record_id = "0" # new row

		my_field_prefix = field_prefix + record_id + ":"
		body = "\n<tr>"
		if record_id != "0": # FIXMEtable_id:
			body += "\n<td>%s</td>" % record_id
		else:
			body += "\n<td>+"
			# need to get the parent joining info
			body += "\n<input name='%s_::_id_field' type='hidden' value='%s'/><input name='%s_::_id_value' type='hidden' value='%s'/>" % (my_field_prefix, parent_field, my_field_prefix, parent_id)
			body += "\n</td>"
		
		for form_item in form['form'].form_item:
			if form_item.active and hasattr(form_items, str(form_item.item) + "_datasheet"): #FIXME str
				# normal controls
				if form_item.name:
					print form_item.item
					my_form_item = getattr(form_items, str(form_item.item) + "_datasheet") #FIXME str
					body += my_form_item(form_item, my_field_prefix) 
		body += "\n</tr>"

		# get data
		for form_item in form['form'].form_item:
			if str(form_item.name).count('.'):
				(table, field) = form_item.name.split('.')
			else:
				table = field = None
			if row and field and hasattr(row, field):
				defaults[my_field_prefix + str(form_item.name)] = str(getattr(row, field))
			else:
				defaults[my_field_prefix + str(form_item.name)] = ""
				
		return (body, defaults)
			
def datasheet_header(form_id, form):

	tmp_objname = 'Form_item'	
	body = "\n<tr>"

	# get the form data	
	
	body += "\n<td>id</td>"  # FIXME i18n
	for form_item in form['form'].form_item:
		if hasattr(form_items, str(form_item.item)): #FIXME not needed visibility param?
			if form_item.label:
				body += "\n<td>%s</td>" % form_item.label
	body += "\n</tr>"
	return body


def create_form(environ, form_render_data, defaults):

	tmp_objname = 'Form_item'	
	msg = ''
	body = ""

	#formdata = form_render_data['formdata']
	table_id = form_render_data['table_id']
	form_id = form_render_data['form_id']
	field_prefix = form_render_data['field_prefix']
	form_type = form_render_data['form_type']

	print "###### NEW FORM"
	print table_id, form_id 


	# get the form data	
	form = get_form_schema(form_id)	
	if form: # FIXME  I really need to split this bugger up some more
		if form['form_params'].has_key('form_object'):
			tmp_objname = form['form_params']['form_object']
		else:
			tmp_objname = None

		# create the form


		body += "<div style='border:1px solid #F00;margin:3px 10px;'>"
		for form_item in form['form'].form_item:
			# see if we know this form item eg dropdown
			# if we do then call it passing the form_item
			if  form_item.active and hasattr(form_items, str(form_item.item)):
				# normal controls
				if form_item.name:
					my_form_item = getattr(form_items, str(form_item.item)) #FIXME str
					body += my_form_item(form_item, field_prefix)
			
			elif  form_item.active and str(form_item.item) == 'subform':
				p = form['item_params'][form_item.id]
				if table_id or ( p.has_key('show') and p['show'] == "true" ):  # we don't want child forms that have no immediate parent
					if p.has_key('form_type') and p['form_type'] == 'datasheet':
					
						# DATASHEET
						my_field_prefix =  "%s%s_" % (form_render_data['field_prefix'], form_item.name)
						
						(form_html, defaults) = datasheet(p['subformID'], table_id, p['child_id'], my_field_prefix, defaults)
						#, parent_id = None, child_field = None, field_prefix = '', defaults = {}
						body += form_html
						pass
						#  data sheet
					else:				
						# contiuous
						body += "<p>%s</p>" % form_item.label
						print "SUBFORM" , form_item, form_item.id
						# subform
						
						sub_form_render_data = {}
						sub_form_render_data['form_id'] = p['subformID']
		
						if (r.data.tables.has_key(p['child_object'])):
							my_obj = getattr(r.data, p['child_object'])
							print "#### %s found" % p['child_object']
						else:
							print "#### %s NOT found" % p['child_object']
				
						if table_id or ( p.has_key('show') and p['show'] == "true" ):  # we don't want child forms that have no immediate parent
							sub_form_render_data['form_type'] = 'continuous'

							session = dbconfig.Session()
							if p.has_key('parent_id'): # some subforms are not connected ie 'cheap datasheets'
								data = session.query(my_obj).filter_by(**{p['child_id']:table_id}).all()
							else:
								data = session.query(my_obj).all()
							session.close()
							for obj in data:
								sub_form_render_data['table_id'] = obj.id
								sub_form_render_data['field_prefix'] = "%s%s_%s:" % (form_render_data['field_prefix'], form_item.name, obj.id)
								(form_html, defaults) = create_form(environ, sub_form_render_data, defaults)
								body += form_html
							if p.has_key('child_id'):
								sub_form_render_data['table_id']= 0
								sub_form_render_data['field_prefix'] = "%s%s_%s:" % (form_render_data['field_prefix'], form_item.name, 0)
								body += "\n<input name='%s_::_id_field' type='hidden' value='%s'/><input name='%s_::_id_value' type='hidden' value='%s'/>" % (sub_form_render_data['field_prefix'], p['child_id'], sub_form_render_data['field_prefix'], form_render_data['table_id'])
								(form_html, defaults) = create_form(environ, sub_form_render_data, defaults)
								body += form_html

			elif  form_item.active:
				# unknown
				body += form_items.unknown(form_item, field_prefix)

		body += "\n</div>"


		# get data or defaults
		form_data = None
		if (r.data.tables.has_key(tmp_objname)):
			my_obj = getattr(r.data, tmp_objname)
			if table_id != 0:
				try:	
					#print 	'looking for %s' % table_id
					#print repr(my_obj)
					session = dbconfig.Session()
					form_data = session.query(my_obj).filter_by(id=table_id).one()
					session.close()
				except: #FIXME better handeling of this as save buggered by this i imagine
					print "## ERROR ## record not found or something"

		for form_item in form['form'].form_item:
		
			if str(form_item.name).count('.'):
				(table, field) = form_item.name.split('.')
			else:
				table = field = None
			
			if form_data and field and hasattr(form_data, field):
				defaults[field_prefix + str(form_item.name)] = str(getattr(form_data, field))
			else:
				defaults[field_prefix + str(form_item.name)] = ""
		
			msg += "<br />"
	else:
		body += "<p>nothing to show</p>"	
		
	return (body, defaults)







