import reformed
import dbconfig


def put(data, parent_field = None, parent_id = 0):
	
	"""load data into database"""
	session = dbconfig.Session()
	for row in data:
		saved_id = 0
		for key in row.keys():
			if key != '_data_':
				if reformed.data.tables[key]: 
					obj = getattr(reformed.data, key)
					# check if already loaded
					if parent_field and parent_id:
						row[key][parent_field] = parent_id
					data = session.query(obj).filter_by(**row[key]).all()
					if data:
						print "already there"
						saved_id = data[0].id
					else:
						#print "adding", key
						data = obj()
						for key2 in row[key].keys():
							#print '%s = %s' % (key2, row[key][key2])
							setattr(data, key2, row[key][key2])
						if parent_field and parent_id:
							setattr(data, parent_field, parent_id)

						session.save_or_update(data)
						session.commit()
						saved_id = data.id

		if row.has_key('_data_') and saved_id:	
			put(row['_data_'], key + '_id', saved_id)
	session.close()
