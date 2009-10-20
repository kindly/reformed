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


import os, sys
from reformed.export import json_dump_all_from_table
from reformed.data_loader import load_json_from_file



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
    print 'deleting database'
    import reformed.dbconfig as config
    engine = config.engine.name
    if engine == 'sqlite':
        file = config.engine.url.database
        os.system("rm %s" % file)
    elif engine == 'mysql':
        session = config.Session()
        tables = session.execute('SHOW TABLES')
        for (table, ) in tables:
            print 'deleting %s...' % table
            session.execute('DROP TABLE `%s`' % table)
        session.commit()
        session.close()
    else:
        print 'Database engine "%s" cannot be deleted' % engine
        sys.exit(1)


def dump():
    print 'dumping data'
    from reformed.reformed import reformed 
    session = reformed.Session()
    session.close()

def run():
    print 'starting webserver'
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
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
   if 'dump' in sys.argv:
       dump()
   if 'delete' in sys.argv:
       delete()
   if 'create' in sys.argv:
        create()
   if 'generate' in sys.argv:
        generate_data()
   if 'load' in sys.argv:
        load_data()
   if 'run' in sys.argv:
        run()
   if 'test' in sys.argv:
        delete()
        create()
        load_data()
        run()

