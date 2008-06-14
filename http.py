from wsgistate.memory import session
import wsgiref.util
import form
import string
import time, datetime
#import model
import cgi
import reformed


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
	else:
		body = 'lost'

	
	if body: # we have a html resonse
		# footers
		if session.get('user_id'):
			body += "\n\n<p><small>user: %s <a href='/logout'>log out</a></small></p>" % (session.get('username') )
		else:
			body += "\n\n<p><small><a href='/view/5/0'>log in</a></small></p>" #FIXME bad url
		body += "\n\n<p><small>page created in %s seconds - uptime %s</small></p>" % (time.clock() - start_time, datetime.datetime.now() - uptime)
		# HTTP header
		start_response('200 OK', [('Content-Type', 'text/html')])
		return body
		
	elif redirect:
		# HTTP header
		start_response('200 OK', [('Content-Type', 'text/html')])
		return "<a href='%s'>%s</a>" % (redirect, redirect)
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

