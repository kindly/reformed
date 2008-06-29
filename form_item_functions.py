import dbconfig
from string import Template
from form_cache import FormCache

#FIXME want to remove this dependancy on forms should be in cache_util or something

form_cache = FormCache()

def dropdown(form_item, data):
	
	options = pairs = None

	if form_item.params("type") == 'list':
		if form_item.params("values"):
			options = form_item.params("values").split('|')
		else:
			options = ('',)
	elif form_item.params("type") == 'sql':
		session = dbconfig.Session()
		sql = form_item.params("sql")
		out = session.execute(sql) # FIXME we trust anything what madness you could put a DROP DATABASE here
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
