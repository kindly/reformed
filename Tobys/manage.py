#!/usr/bin/python
import os, sys



def create():

    import model
    import dbconfig
    dbconfig.metadata.create_all() 

def run():
    import http
    if os.environ.get("REQUEST_METHOD", ""):
        from wsgiref.handlers import BaseCGIHandler
        BaseCGIHandler(sys.stdin, sys.stdout, sys.stderr, os.environ).run(http.app)
    else:
        from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
        httpd = WSGIServer(('', 8000), WSGIRequestHandler)
        httpd.set_app(http.app)
        print "Serving HTTP on %s port %s ..." % httpd.socket.getsockname()
        httpd.serve_forever()


if __name__ == "__main__":
   if 'create' in sys.argv:
        create()
   if 'run' in sys.argv:
        run()

