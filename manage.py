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
##   Copyright (c) 2008-2009 Toby Dacre & David Raznick
##


import os, os.path, sys
from reformed.export import json_dump_all_from_table
from reformed.data_loader import load_json_from_file
from reformed.util import get_dir




def create():
    print 'creating database structure'
    import td

def load_data():
    print 'loading data'
    import reformed.reformed as r
    from reformed.data_loader import FlatFile
    flatfile = FlatFile(r.reformed,
                        "people",
                        "data.csv")
    flatfile.load()

def generate_data():
    print 'generating data'
    import data_creator
    data_creator.create_csv()

def delete():

    import reformed.dbconfig as config
    from sqlalchemy import MetaData
    print 'deleting database'

    engine = config.engine.name

    meta = MetaData()
    meta.reflect(bind=config.engine)

    for table in reversed(meta.sorted_tables):
        print 'deleting %s...' % table.name
        table.drop(bind=config.engine)

def dump():
    print 'dumping data'
    from reformed.reformed import reformed
    session = reformed.Session()
    json_dump_all_from_table(session, 'user', reformed, 'data/users.json', style = "clear")
    session.close()

def undump():
    print 'undumping data'
    from reformed.reformed import reformed
    load_json_from_file('data/users.json', reformed, 'user')

def reloader():
    import paste.reloader
    paste.reloader.install()

def run():
    print 'starting webserver'
    import beaker.middleware
    from reformed.reformed import reformed 
    reformed.scheduler_thread.start()
    import web
    if os.environ.get("REQUEST_METHOD", ""):
        from wsgiref.handlers import BaseCGIHandler
        BaseCGIHandler(sys.stdin, sys.stdout, sys.stderr, os.environ).run(http.app)
    else:

        from paste import httpserver
        #from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
        #httpd = WSGIServer(('', 8000), WSGIRequestHandler)
        application = web.WebApplication()
        
        application = beaker.middleware.SessionMiddleware(application, {"session.type": "memory",
                                                                        "session.auto": True})

        #httpd.set_app(application)
        #print "Serving HTTP on %s port %s ..." % httpd.socket.getsockname()

        try:
            httpserver.serve(application, port = 8000, host = "10.0.0.5")
            #httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
   load = False 
   if 'dump' in sys.argv:
       dump()
   if 'delete' in sys.argv:
       delete()
   if 'create' in sys.argv:
        create()
   if 'undump' in sys.argv:
       undump()
   if 'generate' in sys.argv:
        generate_data()
   if 'load' in sys.argv:
        if "run" not in sys.argv:
            load_data()
        load = True
   if 'reload' in sys.argv:
        reloader()
        run()
   if 'run' in sys.argv:
        run()
   if 'test' in sys.argv:
        load = True
        delete()
        create()
        run()

