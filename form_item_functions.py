import dbconfig
from string import Template
import form #FIXME want to remove this dependancy on forms should be in cache_util or something


def dropdown(form_item, data):
	
	options = pairs = None
	p = form.get_form_item_params(form_item) #FIXME want to remove this dependancy on forms
	print p
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
	tmp = Template("<select onchange='select_box(this)' $class name='$name' id='$name'>").safe_substitute(data)
	if options:
		for option in options:
			tmp += "\n<option value='%s'>%s</option>" % (option, option)
	elif len(pairs)>0:
		for (value, option) in pairs:
			tmp += "\n<option value='%s'>%s</option>" % (value, option)	
	else:
		pass # FIXME allegedly an empty dropdown will kill IE should at least have a 'fucked' option
	tmp += "\n</select>"
	return (tmp)


def codelist(form_item, data):
	# FIXME This is half done
	options = pairs = None
	columns = 5
	session = dbconfig.Session()
	out = session.execute("SELECT c.id, c.name FROM code2 c JOIN code2_group g ON c.code2_group_id = g.id where  g.id=1") #FIXME this is hardcoded
	pairs = []
	for row in out.fetchall():
		pairs.append( ( str(row[0]), str(row[1]) ) )
	session.close()
	
	tmp = "\n<table>"  % str(form_item.label) 
	count = 0
	if len(pairs)>0:
		for (value, option) in pairs:	
			if count % columns == 0:
				if count != 0:	
					tmp += "\n</tr>"
				tmp += "\n<tr>"
			count += 1
			data['value'] = value
			data['option'] = option
			tmp += Template("\n<td><input name='$name:$value' type='checkbox' $class value='True' onchange='select_box(this)' /> $option</td>").safe_substitute(data)
		
		if count % columns != 0:
			for i in range(columns - (count % columns)):
				tmp += "\n<td>&nbsp;</td>"
			tmp += "\n</tr>"
	tmp += "\n</table>\n"
	return (tmp)
