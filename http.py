import wsgiref.util
import string
import time, datetime
import cgi
import dbconfig


# for static
import os, os.path, sys
import mimetypes
import dataexport
from form_cache import FormCache

form_cache = FormCache()

from html import html_wrapper
from wsgistate.memory import session


@session()
@html_wrapper
def reset_cache(environ, start_response):
	# FIXME this needs to be done better as a general purpose function"""

	form_cache.reset()
	environ['reformed']['body'] = 'cache reset'	
	return (environ, start_response)

@session()
@html_wrapper
def check_login(environ, start_response):
	import hashlib

	http_session = environ['com.saddi.service.session'].session
	
	formdata = cgi.FieldStorage(fp=environ['wsgi.input'],
                    	environ=environ,
                    	keep_blank_values=1)
	username = str(formdata.getvalue('username'))
	password = str(formdata.getvalue('password'))	
	session = dbconfig.Session()
	try:
		user = session.query(model.User).options().filter_by(username=username).filter_by(password=password).one()  #eagerload('user_group_permission')
		http_session['username'] = str(user.username)
		http_session['user_id'] = int(user.id)
		environ['reformed']['body'] = 'logged in'
	except:
		# you no good
		clear_authentication_call(environ, start_response)
		environ['reformed']['body'] = 'login fails'
	return (environ, start_response)
	
	
def clear_authentication_call(environ, start_response):

	http_session = environ['com.saddi.service.session'].session
	# clear all authentication stuff
	http_session['username'] = None
	http_session['user_id'] = None
	#return (environ, start_response)

@session()
@html_wrapper
def clear_authentication(environ, start_response):

	clear_authentication_call(environ, start_response)
	environ['reformed']['body'] = 'logged out'
	return (environ, start_response)


def static(environ, start_response):

	path = environ['selector.vars']['path']
	path = '%s/content/%s' % (sys.path[0], path) # does this work in windows?
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
			return wsgiref.util.FileWrapper(f)
	else:
		start_response('404 Not Found', [])
		return []





