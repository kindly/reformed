import model


# FIXME I want to combine the controls but have some way to suppress ones used in the wrong context



# normal

def unknown(form_item, field_prefix):  # FIXME do we need one for datasheets?
	return ("\n<p>unknown &lt;type='%s' label='%s' name='%s%s'&gt</p>" % (str(form_item.item), str(form_item.label), field_prefix, str(form_item.name)) )


def textbox(form_item, field_prefix):
	return ("\n<p>%s <input name='%s%s' type='text'  value='fill'/></p>" % (str(form_item.label), field_prefix, str(form_item.name)) )

def password(form_item, field_prefix): # doesn't get filled
	return ("\n<p>%s <input name='%s%s' type='password'  value=''/></p>" % (str(form_item.label), field_prefix, str(form_item.name)) )

def checkbox(form_item, field_prefix):
	return ("\n<p>%s <input name='%s%s' type='checkbox'  value='True'/></p>" % (str(form_item.label), field_prefix, str(form_item.name)) )


def submit(form_item, field_prefix):
	return ("\n<p> <input name='%s%s' type='submit' value='%s'/></p>" % (field_prefix, str(form_item.name), str(form_item.label)) )


def hidden(form_item, field_prefix):
	return ("\n<input name='%s%s' type='hidden' value=''/>" % (field_prefix, str(form_item.name)) )


def dropdown(form_item, field_prefix):
	
	options = pairs = None
	p = get_params(form_item)
	if p.has_key('type'):
		if p['type'] == 'list':
			if p.has_key('values'):
				options = p['values'].split('|')
			else:
				options = ('',)
		elif p['type'] == 'sql':
			session = model.Session()
	#		try:
			out = session.execute(p['sql']) # FIXME we trust anything what madness you could put a DROP DATABASE here
			pairs = []
			for row in out.fetchall():
				pairs.append( ( str(row[0]), str(row[1]) ) )
	#		except:
	#			print "that was scarey here in the dropdowns!!"
			session.close()
	
	tmp = "\n<p>%s <select name='%s%s'>"  % (str(form_item.label), field_prefix, str(form_item.name) ) 
	if options:
		for option in options:
			tmp += "\n<option value='%s'>%s</option>" % (option, option)
	elif len(pairs)>0:
		for (value, option) in pairs:
			tmp += "\n<option value='%s'>%s</option>" % (value, option)	
	else:
		pass # FIXME aledgedly an empty dropdown will kill IE should at least have a 'fucked' option
	tmp += "\n</select></p>"
	return (tmp)

# datasheet

def textbox_datasheet(form_item, field_prefix):
	return ("\n<td><input name='%s%s' type='text'  value='fill'/></td>" % (field_prefix, str(form_item.name)) )

def submit_datasheet(form_item, field_prefix):
	return ("\n<td><input name='%s%s' type='submit' value='%s'/></td>" % (field_prefix, str(form_item.name), str(form_item.label)) )



# utils
def get_params(form_item):
	print "GETTING PARAMS - %s" % form_item
	params = {}
	for p in form_item.form_item_param:
		if p.key:
			print "%s = '%s'" % (p.key, p.value)
			params[str(p.key)] = str(p.value)
	return params


