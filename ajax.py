import sys
import os.path
import simplejson as json
import cgi
import reformed.dbconfig as dbconfig
import reformed.reformed as r
from sqlalchemy.orm import eagerload
from form_cache import FormCache
from paste.session import SessionMiddleware

#from wsgistate.memory import session

## rather than a recursive form generation
# do it via a list
# this way the records are easily seperated
# duplicates can be squashed
# i think this may be agood approach for the front end too ;)


class AjaxThing(object):

	 # FIXME hmm I don't really like the cache but we can see leave it for now
	form_cache = FormCache()



	def process_html(self, data, parent):
		file_name = data['file']
		path = '%s/content/mockup/%s' % (sys.path[0], file_name) # does this work in windows?
		print path
		if os.path.isfile(path):
			f = open(path, 'r')
			html = f.read()
		else:
			html = 'ERROR NO FILE'
		items = []		
		parent.output.append({'type':'page', 'data':html, 'items':items})
					
	def process_page(self, data, parent):
		if 'username' in parent.http_session:
			html = '<b>hello</b><br />%s' % parent.http_session['username']
			items = []		
		else:
			html = '<b>hello</b><br />you need to log in<div id = "moo"></div>'
			items = [{'type': 'form',
					  'root':'moo',
					  'form_id':'logon',
					  'command':''}]
		parent.output.append({'type':'page', 'data':html, 'items':items})
	
	
	def process_action(self, data, parent):
	
		command = data['command']
		my_object = data['object']

		# FIXME this is just for testing move it out of here
		print "####### ACTION ########"
		print "%s - %s" % (my_object, command)
		
		if  data['data']['username'] == 'moo':
			parent.http_session['username'] = data['data']['username']
			status = {'username': parent.http_session['username']}
			parent.output.append({'type':'status', 'data':status})
			action = {'showForm': 'Codes'}
			parent.output.append({'type':'action', 'data':action})
		else:
			error = {'@main': 'username and password no good :('}
			parent.output.append({'type':'error', 'data':error})
		
		
	def get_form(self, data, parent):
		
		""" this function returns the structure of a given form """

		if 'command' in data:
			# we want to get the form data too
			info = { 'form': data['form'],
				 'field':'id',
				 'value':'',
				 'command': data['command'],
				 'parent_id':'',
				 'parent_field':'',
				 'form_type': None}
			parent.add_command('data', info)
					
		form_name = data['form']
		print "##### %s" % form_name
		# FIXME does form_name want to be form_ref or something more like that.
		
		# FIXME I'd like this session to be repeatedly used
		session = dbconfig.Session()
		form = session.query(r.reformed.get_class('_core_form')).options(eagerload('_core_form_param')).filter_by(name=form_name).one()
		print repr(form)
		form_params = get_params(form._core_form_param)
		print repr(form_params)
		# FIXME not all items are wanted.  what bit field do we use for this (already have active)
		# FIXME want working sort order do we have it??
		form_items = session.query(r.reformed.get_class('_core_form_item')).options(eagerload('_core_form_item_param')).filter_by(_core_form_id=form.id, active=True).order_by(r.reformed.get_class('_core_form_item').sort_order)
	
		form_data = {}
		
		form_security_allowed  = True
		# FIXME security needs re integration
#		if 'form_security' in form_params:
#			if form_params['form_security'] == 'private':
#				if not 'username' in self.http_session:
#					form_security_allowed  = False
					
		if form_security_allowed:
			# this form is allowed
			form_data['fields'] = {}
			form_data['order'] = []
			form_data['params'] = form_params;
			for form_item in form_items:
		
				item_data = {}
			
				# FIXME make all these the same throughout the whole script
				 
				item_data['name'] = form_item.name # FIXME name -> ref?
				item_data['title'] = form_item.label
				item_data['type'] = form_item.item
				print repr(form_item)
				params = get_params(form_item._core_form_item_param)
				if params:
					item_data['params'] = params
				form_data['fields'][form_item.name] = item_data

				form_data['order'].append(form_item.name)
	#			form_item.name
				if form_item.item == 'subform':
			
					# FIXME I don't like this. 
					# we need to have a fixed form_name structure.
					# I think this may mess up some of the tables though.  
					# will have to see plus push through the changes
					print "add subform %s" % item_data['params']['subform_name']
					my_data = {'form':item_data['params']['subform_name']}
					self.get_form(my_data, parent)
		else:
			# we are no allowed to see this form
			item_data = {}
		session.close()
		
		parent.output.append({'type':'form', 'id': form_name, 'data':form_data})



	##  DATA
	def get_data(self, data, parent):
		""" retrieves data for a recordset """
		# want to have a cleaner call
	# need form, id (+ movement eg next prev record first/last/new)
		form_name = data['form']
		field = str(data['field'])
		value = data['value']
		command = data['command']
		parent_id = data['parent_id']
		parent_field = data['parent_field']
		form_type = data['form_type']
		if parent_field:
			parent_field = str(parent_field)

		print "DATA request \n%s\ncommand %s" % (repr(data), command)
		# form

		# FIXME I'd like this session to be repeatedly used

		session = dbconfig.Session()
		form = session.query(r.reformed.get_class('_core_form')).options(eagerload('_core_form_param')).filter_by(name=form_name).one()

		params = get_params(form._core_form_param)
		
		if form_type == None: # need to get it from the form
			if 'form_type' in params:
				form_type = params['form_type']
			else:
				form_type = 'normal'
#
		if 'form_object' in params:
			form_object_name = params['form_object']
		else:
			form_object_name = None
			
		if form_object_name and form_type != 'action':
		
			# form object
			
			
		
			# record movement

			if command:
				(value, recordset_id, rowcount) = record_movement(form_object_name, data);
			else:
				recordset_id = None
				rowcount = None
				value = None
			print "record_id = %s" % value
		
			obj_filter = {}
		
			if parent_field and parent_field != None:
				obj_filter[parent_field] = parent_id
				
				if form_type == 'normal':
					obj_filter[field] = value
				# we need to make sure we pass the corect value with the data
				value = parent_id
			else:
				if form_type == 'normal':
					obj_filter[field] = value
			print "form object: %s" % form_object_name
			print "field: %s, value: %s\n%s" % (field, value, repr(obj_filter))

			obj = r.reformed.get_class(form_object_name)
			# get the data here
			print "OBJECT: %s" % repr(obj)
			if obj_filter:
				data = session.query(obj).filter_by(**obj_filter).all()
			else:
				data = session.query(obj).all()

			# items	
			form_items = session.query(r.reformed.get_class('_core_form_item')).options(eagerload('_core_form_item_param')).filter_by(_core_form_id=form.id, active=1).order_by(r.reformed.get_class('_core_form_item').sort_order)

			data_out_array = []
			records = []
			for data_row in data:		

				data_out = {}
				data_out['__id'] = data_row.id
				if recordset_id != None:
					data_out['__recordset_id'] = recordset_id
				records.append(data_row.id)
				for form_item in form_items:
					if form_item.name.count('.'):
						(table, field) = form_item.name.split('.')
						field_value = getattr(data_row, field)
					#	print form_item.name, field_value
						data_out[form_item.name] = field_value
					if form_item.item == 'subform':
						# force the subform to be see in form filling FIXME hack
						data_out[form_item.name] = 0;
						params = get_params(form_item._core_form_item_param)
					#	print "add data %s" % params['subform_name']
				
						# FIXME this data structure is horrid make this an object?
						info = { 'form': params['subform_name'],
							 'field':params['child_id'],
							 'value':getattr(data_row, params['parent_id']),
							 'command':'first',
							 'parent_id':data_row.id,
							 'parent_field':params['child_id'],
							 'form_type':params['form_type']}
						parent.add_command('data', info)
				data_out_array.append(data_out)
				
				
				# if not a grid we only want he first record so let's quit here
				if form_type != 'grid':
					break
			# if a top level form grid then we need to clear the value
			# if not the data gets sent to the wrong place
			if form_type == 'grid' and parent_field == None:
				value = 0
			if rowcount == None:
				rowcount = len(records)
			parent.output.append({'type':'data',
								'form': form_name,
								'data':data_out_array,
								'data_id':value,
								'records':records,
								'rowcount':rowcount})

	def process_edit(self, data, parent):

		""" processes a single form (delete or save) """

		form_name = data['field_data']['form']
		action = data['action']
		parent_data = {}
		

		form = self.form_cache.get_form(form_name)
		form_object = form.params('form_object')
		print "## looking for %s ##" % form_object
		if (True): ## FIXME botch r.data.tables.has_key(form_object)):
			print '## %s' % form_object
			obj = r.reformed.get_class(form_object)
			if action == "save":
				field_data = data['field_data']
				result = self.save_item(form, obj, field_data)
				# was this an 'autosave'? if so lets do our record movement
				if 'command' in data and data['command'] != '':
					print "GET DATA AFTER AUTOSAVE"
					info = { 'form': form_name,
						 'field': 'id',
						 'value': data['value'],
						 'command': data['command'],
						 'parent_id': data['parent_id'],   #None,
						 'parent_field': data['parent_field'],   #None,
						 'form_type':data['form_type']}
					self.add_command('data', info, False)
					# block the save_id data
					result = {};
								
			elif action == 'delete':
				result = self.delete_item(obj, data['field_data']['record_id'])

				# now return to first record
				info = { 'form': form_name,
					 'field': 'id',
					 'value': None,
					 'command': 'first',
					 'parent_id': data['parent_id'],   #None,
					 'parent_field': data['parent_field'],   #None,
					 'form_type':data['form_type']}
				parent.add_command('data', info)

		else:
			print "NO OBJECT"
			result = {}
		
		if result:
			parent.output.append(result)
	
	def delete_item(self, obj, record_id):
	
		"""this does the actual delete"""
		print 'DELETE ', record_id
		session = dbconfig.Session()
		# FIXME check exists
		data = session.query(obj).filter_by(id=record_id).one()
		session.delete(data)
		session.commit()
		session.close()

		return {'type':'delete', 'deleted':True, 'record_id':record_id} # FIXME check for sucess ;)

	def save_item(self, form, obj, field_data):
	
		"""this does the actual saving"""

		record_id = int(field_data['record']['id'])
		parent_data = {}
		if 'parent_field' in field_data['record']:
			parent_data['field'] = field_data['record']['parent_field']
			parent_data['id'] = field_data['record']['parent_id']

		
		session = dbconfig.Session()
		if record_id:
			# existing record
			# FIXME check exists
			data = session.query(obj).filter_by(id=record_id).one()
		else:
			# new record
			data = obj()
			
			if parent_data:
				# FIXME check has attr or put in try: except:
				setattr(data, parent_data['field'],parent_data['id'])
			print "SAVED NEW"
			
			
		for form_item in form.form_items:
			name = str(form_item.name)
			# FIXME I don't like this looking for a . in the name.
			# how to do this better?
			# talk to razza
			if name.count('.'):
				(table, field) = name.split('.')
				if form_item.name in field_data['data']:
					value = field_data['data'][form_item.name]
					print field, '=', value
					# FIXME try; except:
					setattr(data, field, value )
		session.save_or_update(data)
		session.commit()
		record_id = data.id
		session.close()
		return {'type':'save', 'record_id':record_id}


def record_movement(form_object, data):

	form_name = data['form']
	field = str(data['field'])
	recordset_id = data['value']
	command = data['command']
	parent_id = data['parent_id']
	parent_field = data['parent_field']
	if parent_field:
		parent_field = str(parent_field)
	try:
		parent_id = int(parent_id)
	except:
		parent_id = 0
		
		
	obj_filter = {}
	
	if parent_field and parent_field != 'id':
		obj_filter[parent_field]=parent_id

	print '@@ filter\n%s' % repr(obj_filter)
	# get the recordset
	session = dbconfig.Session()
	obj = r.reformed.get_class(form_object)
	if obj:
		print "OBJECT FILTER", repr(obj_filter)
		if obj_filter:
			data = session.query(obj).filter_by(**obj_filter)
		else:
			data = session.query(obj)  #.filter_by(**{'id':self.record_id})
		#data = data.order_by(obj.c.id)
		session.close()	
		# number of rows in recordset
		rowcount = data.count() #- 1
		
	else:
		print "NO OBJECT FOUND"
		rowcount = 0
	print "rowcount", rowcount
	# FIXME this needs to be changed
	# sub/sub/sub forms need to work with the pulling ids out
	# only the las form gets control
	# this should be easy by splitting the sub forms
	# then hive this off into a function :)



	# we have an incorrect offset ;)
	try:
		recordset_id = int(recordset_id)
	except:
		recordset_id = 0
	
	if command:
		if command == 'prev':
			recordset_id -= 1
		elif command == 'next':
			recordset_id += 1
		elif command == 'first':
			recordset_id = 0
		elif command == 'last':
			recordset_id = rowcount - 1
		elif command == 'new':
			recordset_id = None
			record_id = None
			#rowcount = None
		
	# sanity check record_id
	if rowcount and recordset_id != None:
		if recordset_id >= rowcount:
			recordset_id = rowcount - 1
		if recordset_id < 0:
			recordset_id = 0
		record_id = data[recordset_id].id
	else:
		record_id = None		
	print "Record ID = %s, %s" % (recordset_id, record_id)
	return (record_id, recordset_id, rowcount)



def get_params(items):

	""" helper function to transform list into __dict__ 
		doesn't python have a natural way to do this?? """
	
	params = {}
	for p in items:
		if p.key:
			params[str(p.key)] = str(p.value)
	return params


# our object we can then use
ajax = AjaxThing()

