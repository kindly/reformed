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
		saved_id = save_form(formdata, form_id, record_id )
	# our redirect
	if record_id == 0 and saved_id:
		record_id = saved_id
	print "@@@@@@@@ ",record_id , saved_id
	return "/view/%s/%s" % ( form_id, record_id )

def save_form(formdata, form_id, table_id, field_prefix=''):

	print "SAVING FORM DATA"
	saved_id = 0
	session = dbconfig.Session()

	# get the form data	
	form = get_form_schema(form_id)

	if form['form_params'].has_key('form_object'):
		tmp_objname = form['form_params']['form_object']
	else:
		tmp_objname = None

	print "prefix", field_prefix
	# save data
	if tmp_objname and formdata.has_key(field_prefix + 'save'):
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
				m = re.match(r'^.*:(?=[^:]*:$)', field_prefix)
				if m:
					id_field = str(formdata.getfirst(m.group(0) + '_::_id_field'))
					id_value = str(formdata.getfirst(m.group(0) + '_::_id_value'))
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
			saved_id = data.id
			
	# delete record
	if formdata.getvalue(field_prefix + 'delete'):
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
	(form_html, form_data) = create_form(environ, form_render_data, defaults)
	body += form_html
	

	# fill out form
	parser = FillingParser(form_data)
	parser.feed(str(body))
	parser.close()
	body = parser.text()
	#print repr(defaults)
	
	body = '\n<form action="%s" method="post">%s\n</form>' % (form_action, body)
	return '%s' % body

def datasheet_header(form_id):

	tmp_objname = 'Form_item'	
	body = "\n<tr>"

	# get the form data	
	form = get_form_schema(form_id)
	body += "\n<td>id</td>"  # FIXME i18n
	for form_item in form['form'].form_item:
		if form_items.__dict__.has_key(str(form_item.item)): #FIXME not needed visibility param?
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

		if form_type == "datasheet":
			# datasheets are simple no subforms etc ;)
			body += "\n<tr>"
			if table_id:
				body += "\n<td>%s</td>" % table_id
			else:
				body += "\n<td>+</td>"
			for form_item in form['form'].form_item:
				# see if we know this form item eg dropdown
				# if we do then call it passing the form_item
				if form_item.active and form_items.__dict__.has_key(str(form_item.item) + "_datasheet"):
					# normal controls
					if form_item.name:
						body += form_items.__dict__[str(form_item.item) + "_datasheet"](form_item, field_prefix)
			body += "\n</tr>"

		else:
			body += "<div style='border:1px solid #F00;margin:3px 10px;'>"
			for form_item in form['form'].form_item:
				# see if we know this form item eg dropdown
				# if we do then call it passing the form_item
				if  form_item.active and form_items.__dict__.has_key(str(form_item.item)):
					# normal controls
					if form_item.name:
						body += form_items.__dict__[str(form_item.item)](form_item, field_prefix)
				
				elif  form_item.active and str(form_item.item) == 'subform':
					print "WTF WTF WTF"
					body += "<p>%s</p>" % form_item.label
					print "SUBFORM" , form_item, form_item.id
					# subform
					p = form['item_params'][form_item.id]
					print p
					sub_form_render_data = {}
				
					sub_form_render_data['form_id'] = p['subformID']
					#sub_form_render_data['formdata'] = form_render_data['formdata']
			
					if (r.data.tables.has_key(p['child_object'])):
						my_obj = getattr(r.data, p['child_object'])
						print "#### %s found" % p['child_object']
					else:
						print "#### %s NOT found" % p['child_object']
					
					#print "~~", tmp_objname
					#print p['child_id']
					if table_id or ( p.has_key('show') and p['show'] == "true" ):  # we don't want child forms that have no immediate parent
						if p.has_key('form_type') and p['form_type'] == 'datasheet':
							# datasheet header
							body += "\n<table border='1'>"
							# header row
							body += datasheet_header(p['subformID'])
							sub_form_render_data['form_type'] = 'datasheet'
						else:
							sub_form_render_data['form_type'] = 'continuous'
						print "<p>####</p>"
						session = dbconfig.Session()
						if p.has_key('parent_id'): # some subforms are not connected ie 'cheap datasheets'
							print "MOOOOOOOO %s" % p['child_id'],form_id,p['parent_id']
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
							body += "\n<input name='%s_::_id_field' type='hidden' value='%s'/><input name='%s_::_id_value' type='hidden' value='%s'/>" % (form_render_data['field_prefix'], p['child_id'], form_render_data['field_prefix'], form_render_data['table_id'])
							(form_html, defaults) = create_form(environ, sub_form_render_data, defaults)
							body += form_html

						if p.has_key('form_type') and p['form_type'] == 'datasheet':
							# datasheet footer
							body += "\n</table>\n"
				elif  form_item.active:
					# unknown
					body += form_items.unknown(form_item, field_prefix)

		body += "</div>"


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
			
			if form_data and form_data.__dict__.has_key(field):
				defaults[field_prefix + str(form_item.name)] = str(form_data.__dict__[field])
			else:
				defaults[field_prefix + str(form_item.name)] = ""
		
			msg += "<br />"
	else:
		body += "<p>nothing to show</p>"	
		
	return (body, defaults)







