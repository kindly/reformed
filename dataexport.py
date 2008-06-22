#!/usr/bin/python
import dbconfig
import reformed as r

def export(table, parent = None, parent_id = None):

	"""export data from table and subtables
	does not export the id for the table
	basically create a huge messy __dict__"""
	
	# check if we know the object.  Remember that 'tables' is a restricted name.
	if not hasattr(r.data, table) or table == "tables":
		return "no such object"

	obj = getattr(r.data, table)
	session = dbconfig.Session()
	if parent and parent_id:
		print parent + '_id', parent_id
		data = session.query(obj).filter_by(**{str(parent + '_id'):parent_id}).all()
	else:
		data = session.query(obj).all()

	# FIXME would be nice to use sqlalchemy for this if I could get to those objects
	sql = """SELECT DISTINCT p.field_param_value
			 FROM field f 
			 JOIN field_param p ON f.id=p.field_id 
			 JOIN tables t ON t.id = f.table_id 
			 WHERE field_type='OneToMany'
			 and t.name='%s'""" % table

	out = session.execute(sql)
	sub_tables = []
	for (row,) in out.fetchall():
		sub_tables.append(row)
	print "\n# %s\n" % table
	out_total = ''
	for record in data:
		out = ""
		for col in record.__dict__.keys():
		
			if col[:1]!='_' and col != 'id' and (not parent or col != parent + '_id'):
				value = record.__dict__[col]
				if not value:
					out += ", '%s':None" % col
				else:
					try:
						int(value) # FIXME dirty old hack if only I knew the column type!
						out += ", '%s':%s" % (col, int(value))
					except ValueError:
						out += ", '%s':'%s'" % (col, value.replace("'", "\\'") )

		# look for a sub table
		out_sub = ''
		if sub_tables:
			for sub in sub_tables:
				print sub,int(record.__dict__['id'])
				out_sub_tmp =  export(sub, table, int(record.__dict__['id'])).replace('\n', '\n\t')
				if out_sub_tmp:
					out_sub += out_sub_tmp + ','
		if out:
			if out_sub:
				out_total += ",\n{'%s':{ %s }, \n'_data_': [%s]}" % (table.lower(), out[2:], out_sub[:-1])	
			else:
				out_total += ",\n{'%s':{ %s } }" % (table.lower(), out[2:])	
				
	session.close()	
	if out_total:
		return str("%s\n" % (out_total[1:]) )
	else:
		return ''


