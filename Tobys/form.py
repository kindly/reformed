import model
import http
from sqlalchemy.orm import eagerload
import formencode
from formencode.htmlfill import FillingParser
from formencode import validators
import cgi
import form_items
import re

def list(environ, start_response):
	body=''
	for form in model.session.query(model.Form_item).filter_by(form_id=2):
		body += "<a href='/view/2/%s'>%s</a><br />" % (str(form.id), str(form.name) )
	body += "<a href='/view/2/0'>new</a><br />"
	return http.render(start_response, '<b>Forms</b><br />' + body )


class Form_Schema(formencode.Schema):
	name = validators.String(not_empty=True)

def view(environ, start_response):
	tab_id = int(environ['selector.vars']['table_id'])
	formdata = cgi.FieldStorage(fp=environ['wsgi.input'],
                            	environ=environ,
                            	keep_blank_values=1)
	# save data
	save_form(formdata, environ['selector.vars']['form_id'], tab_id )

	# initiation
	form_render_data = {}
	form_render_data['form_type'] = 'normal'
	form_render_data['table_id']  = tab_id
	form_render_data['form_id'] = environ['selector.vars']['form_id']
	form_render_data['field_prefix'] = ''
	form_render_data['form_type'] = ''
	
	body='' # this will be the form
	defaults = {} # this will be the data

	# create the form 
	(form_html, form_data) = create_form(environ, form_render_data, defaults)
	body += form_html
	body = '\n<form method="post">%s\n</form>' % body

	# fill out form
	parser = FillingParser(form_data)
	parser.feed(str(body))
	parser.close()
	body = parser.text()

	return http.render(start_response, '%s' % body )

def datasheet_header(form_id):

	tmp_objname = 'Form_item'	
	body = "<tr>\n"

	session = model.Session()
	# get the form data	
	form = session.query(model.Form).options(eagerload('form_item')).filter_by(id=form_id).one()  
	# FIXME  sort order ^

	for form_item in form.form_item:
		if form_items.__dict__.has_key(str(form_item.item)): #FIXME not needed visibility param?
			if form_item.label:
				body += "<td>%s</td>\n" % form_item.label
	body += "</tr>\n"
	return body

def save_form(formdata, form_id, table_id, field_prefix=''):

	session = model.Session()
	# get the form data	
	form = session.query(model.Form).options(eagerload('form_item'), eagerload('form_item.form_item_param')).filter_by(id=form_id).one() #FIXME sort order
	form_p = get_params(form)

	tmp_objname= form_p['form_object']
	print "prefix", field_prefix
	# save data
    	if formdata.getvalue(field_prefix + 'save'):
		if (model.__dict__.has_key(tmp_objname)):
			my_obj = model.__dict__[tmp_objname]
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
					id_field = str(formdata.getvalue(m.group(0) + '_::_id_field'))
					id_value = str(formdata.getvalue(m.group(0) + '_::_id_value'))
				else:
					id_field = str(formdata.getvalue('_::_id_field'))
					id_value = str(formdata.getvalue('_::_id_value'))
				print data, ':', id_field, '=', id_value
				setattr(data, id_field, id_value )
			for form_item in form.form_item:
				name = str(form_item.name)
				if name.count('.'):
					(table, field) = name.split('.')
					if data.__dict__.has_key(field):
						# update object
						if form_item.name:
							name = field_prefix + name
						print "update: %s=%s" % (field,formdata.getvalue(name))
						setattr(data, field, str(formdata.getvalue(name)) )
			session.save_or_update(data)
			session.commit()
	
	for form_item in form.form_item:
		if str(form_item.item) == 'subform':
			# subform
			p = form_items.get_params(form_item)
			if (model.__dict__.has_key(p['child_object'])):
				my_obj = model.__dict__[p['child_object']]  #FIXME if not found
			
			data = session.query(my_obj).filter_by(**{p['child_id']:table_id}).all()
			# existing obj
			for obj in data:
				pass
				save_form(formdata, p['subformID'], obj.id, "%s%s_%s:" % (field_prefix, form_item.name, obj.id))
			# new
			save_form(formdata, p['subformID'], 0, "%s%s_0:" % (field_prefix, form_item.name))

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

	session = model.Session()
	# get the form data	
	form = session.query(model.Form).options(eagerload('form_param'), eagerload('form_item'), eagerload('form_item.form_item_param')).filter_by(id=form_id).one() #FIXME sort order
	form_p = get_params(form)

	tmp_objname= form_p['form_object']

	# create the form

	if form_type == "datasheet":
		# datasheets are simple no subforms etc ;)
		body += "<tr>"
		for form_item in form.form_item:
			# see if we know this form item eg dropdown
			# if we do then call it passing the form_item
			if form_items.__dict__.has_key(str(form_item.item) + "_datasheet"):
				# normal controls
				if form_item.name:
					body += form_items.__dict__[str(form_item.item) + "_datasheet"](form_item, field_prefix)
		body += "</tr>"

	else:
		body += "<div style='border:1px solid #F00;margin:3px 10px;'>"
		for form_item in form.form_item:
			# see if we know this form item eg dropdown
			# if we do then call it passing the form_item
			if form_items.__dict__.has_key(str(form_item.item)):
				# normal controls
				if form_item.name:
					body += form_items.__dict__[str(form_item.item)](form_item, field_prefix)

			elif str(form_item.item) == 'subform':
				# subform
				p = form_items.get_params(form_item)

				sub_form_render_data = {}
			

				
				sub_form_render_data['form_id'] = p['subformID']
				#sub_form_render_data['formdata'] = form_render_data['formdata']
			
				if (model.__dict__.has_key(p['child_object'])):
					my_obj = model.__dict__[p['child_object']]
				print "~~", tmp_objname
				print p['child_id']
				if table_id:  # we don't want child forms that have no imediate parent
					if p.has_key('form_type') and p['form_type'] == 'datasheet':
						# datasheet header
						body += "<table border='1'>\n"
						# header row
						body += datasheet_header(p['subformID'])
						sub_form_render_data['form_type'] = 'datasheet'
					else:
						sub_form_render_data['form_type'] = 'continuous'

					data = session.query(my_obj).filter_by(**{p['child_id']:table_id}).all()
					for obj in data:
						sub_form_render_data['table_id']= obj.id
						sub_form_render_data['field_prefix'] = "%s%s_%s:" % (form_render_data['field_prefix'], form_item.name, obj.id)
						(form_html, defaults) = create_form(environ, sub_form_render_data, defaults)
						body += form_html
					if p['child_id']:
						sub_form_render_data['table_id']= 0
						sub_form_render_data['field_prefix'] = "%s%s_%s:" % (form_render_data['field_prefix'], form_item.name, 0)
						body += "\n<input name='%s_::_id_field' type='hidden' value='%s'/><input name='%s_::_id_value' type='hidden' value='%s'/>" % (form_render_data['field_prefix'], p['child_id'], form_render_data['field_prefix'], form_render_data['table_id'])
						(form_html, defaults) = create_form(environ, sub_form_render_data, defaults)
						body += form_html

					if p.has_key('form_type') and p['form_type'] == 'datasheet':
						# datasheet footer
						body += "</table>\n"

		body += "</div>"


	# get data or defaults
	if (model.__dict__.has_key(tmp_objname)):
		my_obj = model.__dict__[tmp_objname]
		if table_id != 0:
			form_data = model.session.query(my_obj).filter_by(id=table_id).one()
		for form_item in form.form_item:
			if str(form_item.name).count('.'):
				(table, field) = form_item.name.split('.')
				if table_id != 0 and form_data.__dict__.has_key(field):
					defaults[field_prefix + str(form_item.name)] = str(form_data.__dict__[field])
				else:
					defaults[field_prefix + str(form_item.name)] = ""
		
		msg += "<br />"
	
	return (body, defaults)


# utils
def get_params(form):
	params = {}
	for p in form.form_param:
		if p.key:
			params[str(p.key)] = str(p.value)
	return params




