import os
import os.path
import sys
import mimetypes
import beaker
import cgi
import traceback
import wsgiref.util
import json
from global_session import global_session
import interface
import lookup

import logging
logger = logging.getLogger('reformed.main')

def session(environ):
    global_session.session = environ['beaker.session']
    if global_session.session.get('user_id') == None:
        global_session.session['user_id'] = 0
        global_session.session['permissions'] = []


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

    return lookup.table_lookup(q, limit, request, http_session)

def process_node(environ, start_response):


    session(environ)

    formdata = cgi.FieldStorage(fp=environ['wsgi.input'],
                        environ=environ,
                        keep_blank_values=1)

    head = str(formdata.getvalue('head'))

    try:
        body = json.loads(str(formdata.getvalue('body')))
    except:
        body = {}

    node_interface = interface.Interface()

    node_interface.add_command(head, body)
    node_interface.process()
    data = node_interface.output

    start_response('200 OK', [('Content-Type', 'text/html')])
    try:
        return [json.dumps(data, separators=(',',':'))]
    except TypeError:
        # we had a problem with the JSON conversion
        # let's send the error to the front-end
        error_msg = 'JSON OUTPUT FAIL\n\n%s' % traceback.format_exc()
        info = {'action': 'general_error',
                'node' : 'JSON error',
                'data' : error_msg}
        data = [{'data' : info, 'type' : 'node'}]
        return [json.dumps(data,  separators=(',',':'))]


class WebApplication(object):
    """New leaner webapplication server."""

    def static(self, environ, start_response, path):
        """Serve static content"""

        root = os.path.dirname(os.path.abspath(__file__))
        path = '%s/content/%s' % (root, path) # does this work in windows?

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
                start_response('200 OK', headers)
                f = open(path, 'rb')
                return wsgiref.util.FileWrapper(f)
        else:
            start_response('404 Not Found', [])
            return []



    def __call__(self, environ, start_response):
        """Request handler"""

        request_url = environ['PATH_INFO']
        if request_url == '/ajax':
            return (process_node(environ, start_response))
        elif request_url.startswith('/ajax'):
            # ajax request
            return (process_autocomplete(environ, start_response))
        else:
            # content request
            return (self.static(environ, start_response, request_url))


