#!/usr/bin/python
import dbconfig
import reformed as r

def export(table):
	print "export", table
	if not hasattr(r.data, table):
		return "no such object"
		
	obj = getattr(r.data, table)
	session = dbconfig.Session()
	data = session.query(obj).all()

	print "\n# %s\n" % table
	out_total = ''
	for record in data:
		out = ""
		for col in record.__dict__.keys():
			if col[:1]!='_':
				value = record.__dict__[col]
				if not value:
					out += ", %s=None" % col
				else:
					try:
						int(value) # FIXME dirty old hack if only I knew the column type!
						out += ", %s=%s" % (col, int(value))
					except ValueError:
						out += ", %s='%s'" % (col, value)
			
		if out:
			out_total += "dataloader.put('%s', %s)\n" % (table.lower(), out[2:])
			
	session.close()	
	print out_total
	return str("<pre># %s\n\n%s</pre>" % (table, out_total) )


