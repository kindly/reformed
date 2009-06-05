import time, datetime
from string import Template

uptime = datetime.datetime.now()



def html_wrapper(fn):

	
	def new(*args):
	
		environ = args[0]
		start_response = args[1]
		
		start_time = time.clock()
		environ['reformed'] = {'start_time' : start_time}

		fn(*args)
		
		body = environ['reformed']['body']
		# HTTP header
		start_response('200 OK', [('Content-Type', 'text/html')])

		data['main'] = body
		data['footer'] = html_footer(environ)
		return Template(page_template).safe_substitute(data) 
	return new
		
		

def html_footer(environ): 
	# footers
	http_session = environ['com.saddi.service.session'].session
	start_time = environ['reformed']['start_time']
	
	if http_session.get('user_id'):
		body = "\n\n<p><small>user: %s <a href='/logout'>log out</a>" % (http_session.get('username') )
	else:
		body = "\n\n<p><small><a href='/form/5/1'>log in</a>"
	
	body += " <a href='/reset_cache'>refresh cache</a> <a href='/list'>form list</a></small></p>" #FIXME bad url
	body += "\n\n<p><small>page created in %s seconds - uptime %s</small></p>" % (time.clock() - start_time, datetime.datetime.now() - uptime)
	return body		
		
data = {}
page_template = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>
<html xmlns='http://www.w3.org/1999/xhtml'>
<head>
<title>Reformed - what a horrid name</title>
<meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1' />
<link href='/content/default.css' rel='stylesheet' type='text/css' />
<script type='text/javascript' src='/content/default.js'></script>
</head>
<body>
<h1><img src="/content/reformed.png" title="cool" alt="reformed" /></h1>
$main
$footer
</body>\n</html>
"""

