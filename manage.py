#!/usr/bin/python
import os, sys
from reformed.export import json_dump_all_from_table
from reformed.data_loader import load_json_from_file



def create():

    from reformed.reformed import reformed
    import td
    load_json_from_file("form_dump.json", reformed, "_core_form") 

def delete():

    os.system("rm reformed/reformed.sqlite")

def dump():

    from reformed.reformed import reformed 
    session = reformed.Session()
    json_dump_all_from_table(session, "_core_form", reformed, "form_dump.json", style='clear')
    session.close()

def run():

    from reformed.reformed import reformed, scheduler_thread 
    scheduler_thread.start()
    import web
    if os.environ.get("REQUEST_METHOD", ""):
        from wsgiref.handlers import BaseCGIHandler
        BaseCGIHandler(sys.stdin, sys.stdout, sys.stderr, os.environ).run(http.app)
    else:
        from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
        httpd = WSGIServer(('', 8000), WSGIRequestHandler)
        httpd.set_app(web.WebApplication())
        print "Serving HTTP on %s port %s ..." % httpd.socket.getsockname()
        httpd.serve_forever()


if __name__ == "__main__":
   if 'dump' in sys.argv:
       dump()
   if 'delete' in sys.argv:
       delete()
   if 'create' in sys.argv:
        create()
   if 'run' in sys.argv:
        run()

