import os
import os.path
import sys
import mimetypes
import cgi

import wsgiref.util
from paste.session import SessionMiddleware
import json

import interface



# I'd like to put this in the WebApplication class but it
# doesn't like the decorator if I do :(
@SessionMiddleware
def process_ajax(environ, start_response):
    """ this gets the request data and starts any processing jobs
    needs to be expanded to do multiple requests """

    http_session = environ['paste.session.factory']()

    formdata = cgi.FieldStorage(fp=environ['wsgi.input'],
                        environ=environ,
                        keep_blank_values=1)
    head = str(formdata.getvalue('head'))

    try:
        body = json.loads(str(formdata.getvalue('body')))
    except:
        print "WHOOA that data you sent looks corrupt!"
        print "*" * 40
        print repr(formdata.getvalue('body'))
        print "*" * 40
        body = {};
    moo = interface.Interface(http_session)

    print repr(body)

    moo.add_command(head, body)
    moo.process()
    data = moo.output

    start_response('200 OK', [('Content-Type', 'text/html')])
    print json.dumps(data, sort_keys=False, indent=4)
    print 'length %s bytes' % len(json.dumps(data, sort_keys=True, indent=4))
    print 'condenced length %s bytes' % len(json.dumps(data, separators=(',',':')))
    print 'SESSION\n%s' % json.dumps(http_session, sort_keys=False, indent=4)

    return json.dumps(data, separators=(',',':'))



class WebApplication(object):
    """New leaner webapplication server."""

    def static(self, environ, start_response, path):
        """Serve static content"""

        print "STATIC %s" % path
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



    def __call__(self, environ, start_response):
        """Request handler"""

        request_url = environ['PATH_INFO']
        if request_url.startswith('/ajax'):
            # ajax request
            return(process_ajax(environ, start_response))
        else:
            # content request
            return(self.static(environ, start_response, request_url))


