#!/usr/bin/python


import dbconfig
import reformed as r

r.data = r.Database()
r.data.create_tables()
#r.data.create_classes()
d=r.data


#print repr(r.data.tables['form']),r.data.tables['form'].name,r.data.tables['form'].form

session = dbconfig.Session()
#if d.tables['form']:
#	print "found"
#else:
#	print "not found"
#obj = r.data.tables['form'].form
body=''
obj = getattr(d, 'form')
data = session.query(obj).all()
for form in data:
	body += "<a href='/view/1/%s'>%s</a><br />" % (str(form.id), str(form.name) )
body += "<a href='/view/1/0'>new</a><br />"
session.close()
print '<b>Forms</b><br />' + body 
