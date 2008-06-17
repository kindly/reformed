from wsgistate.memory import session
import wsgiref.util
import form
import string
import time, datetime
import cgi
import reformed

# for static
import os, os.path, sys
import posixpath
import mimetypes
from wsgiref.util import FileWrapper

import dataexport

# get our data up
reformed.data = reformed.Database()
reformed.data.create_tables()

uptime = datetime.datetime.now()


@session()
def app(environ, start_response):

	start_time = time.clock()
	session = environ['com.saddi.service.session'].session

	# parse url path
	path = environ['PATH_INFO']
	path_info = string.split(path, '/')
	cmd = path_info[1]

	body = redirect = None # our outcomes
	
	if cmd == 'view':
		environ['selector.vars']= {'form_id' : path_info[2], #FIXME check if these exist durr
					   'table_id' : path_info[3] }
		body = form.view(environ)
	elif cmd == 'save':
		environ['selector.vars']= {'form_id' : path_info[2], #FIXME check if these exist durr
					   'table_id' : path_info[3] }
		redirect = form.save(environ)

	elif cmd == 'list':
		body = form.list()
	elif cmd == 'login':
		body = check_login(environ, session)
	elif cmd == 'reset_cache':
		# reset form cache
		form.form_cache = {}
		body = "cache reset"
	elif cmd == 'logout':
		clear_authentication(session)
		body = "logged out"
	elif cmd == 'content':
		# static content
		path = path[8:]
		return(static(environ, start_response, path))
	elif cmd == 'export':
		# static content
		path = path[8:]
		body = dataexport.export(path)

	else:
		body = 'lost'

	
	if body: # we have a html resonse

		# HTTP header
		start_response('200 OK', [('Content-Type', 'text/html')])
		return [html_header() + body + html_footer(session, start_time)]
		
	elif redirect:
		# HTTP header
		start_response('200 OK', [('Content-Type', 'text/html')])
		return ["<a href='%s'>%s</a>" % (redirect, redirect)]
	else:
		print "nothing to do" # FIXME we want to throw an error here

def check_login(environ, http_session):
	import hashlib

	formdata = cgi.FieldStorage(fp=environ['wsgi.input'],
                    	environ=environ,
                    	keep_blank_values=1)
	username = str(formdata.getvalue('username'))
	password = str(formdata.getvalue('password'))	
	session = model.Session()
	try:
		user = session.query(model.User).options().filter_by(username=username).filter_by(password=password).one()  #eagerload('user_group_permission')
		http_session['username'] = str(user.username)
		http_session['user_id'] = int(user.id)
		return "OK" 
	except:
		# you no good
		clear_authentication(http_session)
		return "BAD " + hashlib.sha256(password).hexdigest()

def clear_authentication(http_session):
	# clear all authentication stuff
	http_session['username'] = None
	http_session['user_id'] = None





def static(environ, start_response, path):
	path = '%s/content%s' % (sys.path[0], path) # does this work in windows?
	print path
	if os.path.isfile(path):
		stat = os.stat(path)
		mimetype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
		max_age = None # FIXME: not done
		last_modified = stat.st_mtime
		not_modified = False
		if 'HTTP_IF_MODIFIED_SINCE' in environ:
			value = parse_date_timestamp(environ['HTTP_IF_MODIFIED_SINCE'])
			if value >= last_modified:
				not_modified = True
		etag = '%s-%s' % (last_modified, hash(path))
		if 'HTTP_IF_NONE_MATCH' in environ:
			value = environ['HTTP_IF_NONE_MATCH'].strip('"')
			if value == etag:
				not_modified = True
		headers = [
			('Content-Type', mimetype),
			('Content-Length', str(stat.st_size)),
			('ETag', etag),
	## FIXME           ('Last-Modified', serialize_date(last_modified))
	]
		if max_age: 
			headers.append(('Cache-control', 'max-age=%s' % max_age))
		if not_modified:
			start_response('304 Not Modified', headers)
			return []
		else:
			print path
			start_response('200 OK', headers)
			f = open(path, 'rb')
			return FileWrapper(f)
	else:
		start_response('404 Not Found', [])
		return []

# dirty old hack
def html_header():

	return """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>
	<html xmlns='http://www.w3.org/1999/xhtml'>
	<head>
	<title>Reformed - what a horrid name</title>
	<meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1' />
	<link href='/content/default.css' rel='stylesheet' type='text/css' />
	</head>
	<body>
	<h1><img src="/content/reformed.png" title="cool" alt="reformed" /></h1>\n"""

def html_footer(http_session, start_time): 
	# footers
	if http_session.get('user_id'):
		body = "\n\n<p><small>user: %s <a href='/logout'>log out</a></small></p>" % (http_session.get('username') )
	else:
		body = "\n\n<p><small><a href='/view/5/0'>log in</a></small></p>" #FIXME bad url
	body += "\n\n<p><small>page created in %s seconds - uptime %s</small></p>" % (time.clock() - start_time, datetime.datetime.now() - uptime)
	body += "\n</body>\n</html>"
	return body
