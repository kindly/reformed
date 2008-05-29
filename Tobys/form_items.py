import model

# normal

def textbox(form_item, field_prefix):
	return ("\n<p>%s <input name='%s%s' type='text'  value='fill'/></p>" % (str(form_item.label), field_prefix, str(form_item.name)) )


def checkbox(form_item, field_prefix):
	return ("\n<p>%s <input name='%s%s' type='checkbox'  value='fill'/></p>" % (str(form_item.label), field_prefix, str(form_item.name)) )


def submit(form_item, field_prefix):
	return ("\n<p> <input name='%s%s' type='submit' value='%s'/></p>" % (field_prefix, str(form_item.name), str(form_item.label)) )


def hidden(form_item, field_prefix):
	return ("\n<input name='%s%s' type='hidden' value=''/>" % (field_prefix, str(form_item.name)) )


def dropdown(form_item, field_prefix):
	print "DROPDOWN\n"
	p = get_params(form_item)
	if p['type'] == 'list':
		option = p['values'].split('|')
	elif p['type'] == 'sql':
		session = model.Session()
		out = session.execute("SELECT id, name FROM form")
		print "OUT"
		print repr(out)
		options = []
		values = []
		for row in out.fetchall():
			values.append( str(row[0]) )
			options.append( str(row[1]) )	
	else:
		options = [ 1,2,3,4]
	tmp = "\n<p>%s <select name='%s%s'>"  % (str(form_item.label), field_prefix, str(form_item.name) ) 
	for option in options:
		tmp += "\n<option value='%s'>%s</option>" % (option, option)
	tmp += "\n</select></p>"
	return (tmp)

# datasheet

def textbox_datasheet(form_item, field_prefix):
	return ("\n<td><input name='%s%s' type='text'  value='fill'/></td>" % (field_prefix, str(form_item.name)) )


def submit_datasheet(form_item, field_prefix):
	return ("\n<td><input name='%s%s' type='submit' value='%s'/></td>" % (field_prefix, str(form_item.name), str(form_item.label)) )



# utils
def get_params(form_item):
	params = {}
	for p in form_item.form_item_param:
		if p.key:
			params[str(p.key)] = str(p.value)
	return params


