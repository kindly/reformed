#!/usr/bin/python
import dbconfig
import model

def export(table):
	session = dbconfig.Session()

	obj = model.__dict__[table]
	data = session.query(obj).all()

	print "\n# %s\n" % table
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
			out = "dataloader.put('%s', %s)" % (table.lower(), out[2:])
			print out
	session.close()
	
export('Form')
export('Form_param')
export('Form_item')
export('Form_item_param')



