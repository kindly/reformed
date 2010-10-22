##   This file is part of Reformed.
##
##   Reformed is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License version 2 as
##   published by the Free Software Foundation.
##
##   Reformed is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with Reformed.  If not, see <http://www.gnu.org/licenses/>.
##
##   -----------------------------------------------------------------
##
##   Reformed
##   Copyright (c) 2008-2010 Toby Dacre & David Raznick
##


import os
import os.path
import mimetypes
import cgi
import traceback
import wsgiref.util
import pprint
import logging

import webob
import simplejson as json

from global_session import global_session
import node.node_runner as node_runner
import fileupload
import database.util
import node.authenticate as authenticate
import lookup
log = logging.getLogger('rebase.web')

Request = webob.Request
Response = webob.Response


def session(environ):
    global_session.session = environ['beaker.session']
    # if this is a new session set up the defaults
    if global_session.session.get('user_id') == None:
        # auto login
        request = Request(environ)
        global_session.session['IP_address'] = request.remote_addr
        auto_cookie = request.cookies.get('auto')
        if auto_cookie:
            if authenticate.auto_login(auto_cookie):
                return
        # normal session start
        authenticate.clear_user_session()

        log.info('%s creating new http session\n%s' % (request.remote_addr, pprint.pformat(global_session.session)))


# I'd like to put this in the WebApplication class but it
# doesn't like the decorator if I do :(
def process_autocomplete(environ, start_response):
    """ this gets the request data and starts any processing jobs
    needs to be expanded to do multiple requests """

    # FIXME this has no security

    session(environ)

    formdata = cgi.FieldStorage(fp=environ['wsgi.input'],
                        environ=environ,
                        keep_blank_values=1)
    request = environ['PATH_INFO'].split("/")[2:]
    q = str(formdata.getvalue('q'))
    limit = int(formdata.getvalue('limit'))

    start_response('200 OK', [('Content-Type', 'text/html')])

    return lookup.table_lookup(q, limit, request)


def process_fileupload(environ, start_response, request_url):

    session(environ)
    if request_url.startswith("/uploadstatus"):
        # get status for this upload
        return fileupload.fileupload_status(environ, start_response)
    else:
        # start upload
        return fileupload.fileupload(environ, start_response, global_session.application)


def process_attachment(environ, start_response):

    session(environ)
    reference = environ['QUERY_STRING']
    # FIXME need to check can view this file
    try:
        if '.' in reference:
            (id, type) = reference.split('.', 1)
            type = '.%s' % type
        else:
            id = reference
            type = ''
        reference = int(id)
        r =  global_session.database
        data = r.search('upload', 'id=%s' % reference, fields = ['path', 'filename']).data
    except ValueError:
        data = None
    if data:
        full_path = fileupload.get_dir(data[0]['path'], global_session.application) + type
        return get_file(environ, start_response, full_path)
    else:
        start_response('404 Not Found', [])
        return []



def process_node(environ, start_response):

    session(environ)

    request = Request(environ)

    ##FIXME make sure we have a head and a body
    try:
        body = json.loads(request.params["body"])
    except Exception, e:
        return throw_error(environ, start_response, 'sent_data', 'Sent JSON Error', request.params["body"])

    node_interface = node_runner.NodeRunner(global_session.application)

    node_interface.add_command(body)
    try:
        node_interface.process()
    except node_runner.NodeNotFound:
        error = 'The requested node `%s` does not exist.' % node_interface.node_name
        return throw_error(environ, start_response, 'Node Error', 'Node not found', error)
    except:
        error = '<pre>%s</pre>' % traceback.format_exc()
        return throw_error(environ, start_response, 'Application Error', 'Application error', error)

    data = node_interface.output

    try:
        # fast output
        output = [json.dumps(data, separators=(',',':'))]
        # slow pretty output
        #output = [json.dumps(data, sort_keys=False, indent=4)]
    except TypeError:
        return throw_error(environ, start_response, 'Application Error', 'Output JSON Error', 'Generated data cannot be convered to JSON.' )

    response = Response(environ)
    response.content_type = 'text/plain'

    # Cookie stuff
    if node_interface.auto_login_cookie:
        cookie = node_interface.auto_login_cookie
        if cookie == 'CLEAR':
            response.delete_cookie('auto')

        else:
            # are we are using https?
            host_secure = (request.scheme == 'https')

            response.set_cookie('auto',  cookie,
                                secure = host_secure, # can be sent over plain http (risky)
                                max_age = 31536000, # cookie lifetime in seconds (1 year)
                                path = '/')
        response.headers['Set-Cookie']

    response.body = ''.join(output)

    return response(environ, start_response)




def throw_error(environ, start_response, error_type, error_title, details):

    """an exception was thrown generate the traceback info and send to the frontend"""

    info = {'action': 'error',
            'error_type' : error_type,
            'error_title' : error_title,
            'data' : details}
    data = [info]

    response = Response(environ)
    response.content_type = 'text/plain'

    response.body = json.dumps(data, separators=(',',':'))
    return response(environ, start_response)

class WebApplication(object):
    """New leaner webapplication server."""

    def __init__(self, application):

        print "-----web app started------"
        log.info("----- web app started ------")

        self.application = application
        self.application.initialise_database()
        self.application.process_nodes()
        self.database = application.database
        self.directory = application.directory
        global_session.database = self.database

    def static(self, environ, start_response, path):
        """Serve static content"""
        if path == '/':
            path = '/reformed.html'
        print path
        # FIXME security limit path directory traversal etc
        root = database.util.get_dir()
        if path.startswith('/local/'):
            path = os.path.join(root, self.directory, 'content', path[7:])
        else:
            path = os.path.join(root, 'content', path[1:])
        return get_file(environ, start_response, path)



    def __call__(self, environ, start_response):
        """Request handler"""

        global_session.application = self.application
        global_session.database = self.database
        global_session.sys_info = self.application.sys_info

        request_url = environ['PATH_INFO']
        log.info("url: %s" % request_url)

        if request_url == '/ajax':
            return (process_node(environ, start_response))
        elif request_url.startswith('/ajax'):
            # ajax request
            return (process_autocomplete(environ, start_response))
        elif request_url.startswith('/upload'):
            # file upload
            return (process_fileupload(environ, start_response, request_url))
        elif request_url.startswith('/attach'):
            # file upload
            return (process_attachment(environ, start_response))
        else:
            # content request
            return (self.static(environ, start_response, request_url))


    def fake_requests(self):
        """ For performance testing we can run the web application
        outside of a webserver but we need to fake the servers
        request and response objects this swaps in our fakes."""
        import fake_webob
        global Request
        Request = fake_webob.Request
        global Response
        Response = fake_webob.Response


def get_file(environ, start_response, path):

    """returns the file in path to the browser
    NOTE: there is no security at this point all
    authorisation must be checked before this is called"""

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
            log.info('file not modified %s' % path)
            start_response('304 Not Modified', headers)
            return []
        else:
            log.info('serving file %s' % path)
            start_response('200 OK', headers)
            f = open(path, 'rb')
            return wsgiref.util.FileWrapper(f)
    else:
        log.warn('file %s not found' % path)
        start_response('404 Not Found', [])
        return []
