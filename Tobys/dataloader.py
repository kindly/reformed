import reformed
import dbconfig

def put(table, **kw):
	
	session = dbconfig.Session()
	
	if reformed.data.tables[table]:
		print ".",
		obj = getattr(reformed.data, table)
		data = obj()
		for field, value in kw.iteritems():
			setattr(data, field, value)
			
		try: # another dirty hack to stop duplicate data
			# it does let us hack ids
			session.save_or_update(data)
			session.commit()
		except:
			print " data loading failed!", kw
		
	else:
		print "object not found"
		
	
	session.close()

