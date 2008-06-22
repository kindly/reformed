import dbconfig


# FIXME I want to combine the controls but have some way to suppress ones used in the wrong context

def _textbox(name):
	return ("<input class='x' name='%s' id='%s' type='text' onkeypress='select_box(this)' onchange='select_box(this)' value='fill'/>" % (name, name) )


def _password(name): # doesn't get filled
	return ("<input class='x' name='%s' id='%s' type='password' onkeypress='select_box(this)' onchange='select_box(this)'  value=''/>" % (name, name) )

def _checkbox(name):
	return ("<input class='x' name='%s' id='%s' type='checkbox' onchange='select_box(this)'  value='True'/>" % (name, name) )
	
def _submit(form_item, field_prefix):
	return ("<input class='x' name='%s%s' id='%s%s' type='submit' value='%s'/>" % (field_prefix, str(form_item.name), field_prefix, str(form_item.name), str(form_item.label)) )

def _label(form_item, field_prefix):
	return "<label class='x' for='%s%s'>%s</label> " % (field_prefix, str(form_item.name), str(form_item.label))

def _dropdown(form_item, field_prefix):
	
	options = pairs = None
	p = get_params(form_item)
	if p.has_key('type'):
		if p['type'] == 'list':
			if p.has_key('values'):
				options = p['values'].split('|')
			else:
				options = ('',)
		elif p['type'] == 'sql':
			session = dbconfig.Session()
			out = session.execute(p['sql']) # FIXME we trust anything what madness you could put a DROP DATABASE here
			pairs = []
			for row in out.fetchall():
				pairs.append( ( str(row[0]), str(row[1]) ) )
			session.close()
	
	tmp = "\n<select onchange='select_box(this)' class='x' name='%s%s'>"  % ( field_prefix, str(form_item.name) ) 
	if options:
		for option in options:
			tmp += "\n<option value='%s'>%s</option>" % (option, option)
	elif len(pairs)>0:
		for (value, option) in pairs:
			tmp += "\n<option value='%s'>%s</option>" % (value, option)	
	else:
		pass # FIXME aledgedly an empty dropdown will kill IE should at least have a 'fucked' option
	tmp += "\n</select>"
	return (tmp)
	
	
# normal

def unknown(form_item, field_prefix):  # FIXME do we need one for grids?
	return ("\n<p>unknown &lt;type='%s' label='%s' name='%s%s'&gt</p>" % (str(form_item.item), str(form_item.label), field_prefix, str(form_item.name)) )


def textbox(form_item, field_prefix):
	return "\n<p>" + _label(form_item, field_prefix) + _textbox(field_prefix + str(form_item.name)) + "</p>"

def password(form_item, field_prefix): 
	return "\n<p>" + _label(form_item, field_prefix) + _password(field_prefix + str(form_item.name)) + "</p>"

def checkbox(form_item, field_prefix):
	return "\n<p>" + _label(form_item, field_prefix) + _checkbox(field_prefix + str(form_item.name)) + "</p>"


def submit(form_item, field_prefix):
	return ("\n<p>" + _submit(form_item, field_prefix) + "</p>")

def dropdown(form_item, field_prefix):
	return  "\n<p>" + _label(form_item, field_prefix) + _dropdown(form_item, field_prefix)+ "</p>"
	
def hidden(form_item, field_prefix):
	return ("\n<input name='%s%s' type='hidden' value=''/>" % (field_prefix, str(form_item.name)) )

	
	




def codelist(form_item, field_prefix):
	
	options = pairs = None
	columns = 5
	session = dbconfig.Session()
	out = session.execute("SELECT c.id, c.name FROM code2 c JOIN code2_group g ON c.code2_group_id = g.id where  g.id=1") #FIXME this is hardcoded
	pairs = []
	for row in out.fetchall():
		pairs.append( ( str(row[0]), str(row[1]) ) )
	session.close()
	
	tmp = "\n<p>%s \n<table>"  % str(form_item.label) 
	count = 0
	if len(pairs)>0:
		for (value, option) in pairs:	
			if count % columns == 0:
				if count != 0:	
					tmp += "\n</tr>"
				tmp += "\n<tr>"
			count += 1
			tmp += "\n<td><input name='%s:%s' type='checkbox'  value='True'/> %s</td>" % (field_prefix + str(form_item.name), value, option)
		
		if count % columns != 0:
			for i in range(columns - (count % columns)):
				tmp += "\n<td>&nbsp;</td>"
			tmp += "\n</tr>"
		

	tmp += "\n</table>\n</p>"
	return (tmp)
	
	
	
# grid

def textbox_grid(form_item, field_prefix):
	return "\n<td>" + _textbox(field_prefix + str(form_item.name)) + "</td>"

def password_grid(form_item, field_prefix): 
	return "\n<td>" + _password(field_prefix + str(form_item.name)) + "</td>"

def checkbox_grid(form_item, field_prefix):
	return "\n<td>" + _checkbox(field_prefix + str(form_item.name)) + "</td>"

def submit_grid(form_item, field_prefix):
	return ("\n<td>" + _submit(form_item, field_prefix) + "</td>")		


def save_delete_grid(form_item, field_prefix): # form_items included for common calling params
	return ("\n<p> <input name='%s_::_save_selected' type='submit' value='save selected'/> <input name='%s_::_delete_selected' type='submit' value='delete selected'/></p>" % (field_prefix, field_prefix ))


def dropdown_grid(form_item, field_prefix):
	return  "\n<td>" + _dropdown(form_item, field_prefix)+ "</td>"

#def dropdown_grid(form_item, field_prefix):
#	
#	options = pairs = None
#	p = get_params(form_item)
#	if p.has_key('type'):
#		if p['type'] == 'list':
#			if p.has_key('values'):
#				options = p['values'].split('|')
#			else:
#				options = ('',)
#		elif p['type'] == 'sql':
#			session = dbconfig.Session()
#	#		try:
#			out = session.execute(p['sql']) # FIXME we trust anything what madness you could put a DROP DATABASE here
#			pairs = []
#			for row in out.fetchall():
#				pairs.append( ( str(row[0]), str(row[1]) ) )
#	#		except:
#	#			print "that was scarey here in the dropdowns!!"
#			session.close()
#
#
#	session = dbconfig.Session()
#	out = session.execute("SELECT name, name FROM code JOIN code_group_code ON code.id =  code_group_code.code_id WHERE code_group_id = 3") # FIXME we trust anything what madness you could put a DROP DATABASE here
#	pairs = []
#	for row in out.fetchall():
#		pairs.append( ( str(row[0]), str(row[1]) ) )
#	session.close()
#
#	tmp = "\n<td><select name='%s%s'>"  % (field_prefix, str(form_item.name) ) 
#	if options:
#		for option in options:
#			tmp += "\n<option value='%s'>%s</option>" % (option, option)
#	elif len(pairs)>0:
#		for (value, option) in pairs:
#			tmp += "\n<option value='%s'>%s</option>" % (value, option)	
#	else:
#		pass # FIXME aledgedly an empty dropdown will kill IE should at least have a 'fucked' option
#	tmp += "\n</select></td>"
#	return (tmp)





# utils
def get_params(form_item):
	print "GETTING PARAMS - %s" % form_item
	params = {}
	for p in form_item.form_item_param:
		if p.key:
			print "%s = '%s'" % (p.key, p.value)
			params[str(p.key)] = str(p.value)
	return params


