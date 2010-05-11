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
import shutil
from reformed.export import json_dump_all_from_table
from reformed.data_loader import load_json_from_file
from reformed.util import get_dir
from optparse import OptionParser
import application as app

application = None
dir = None

def make_application():

    global application
    if not application:
        application = app.Application(dir, quiet = options.quiet)
    return application

def create(application):
    print 'creating database structure'
    import schema

def extract(application):
    import extract
    extract.extract(application.database,
                 application.dir)

def load_data(application, file):
    print 'loading data'
    from reformed.data_loader import FlatFile
    flatfile = FlatFile(application.database,
                        "people",
                        file)

    flatfile.load()

def load(application):
    print "loading data"
    import load
    load.load(application.database,
                 application.dir)

def generate_data(application):
    print 'generating data'
    import data_creator
    data_creator.create_csv()

def confirm_request(msg, default = 'n'):

    if options.yes_to_all:
        return True
    if default == 'y' or default == 'yes':
        opts = '[Yes, no, quit]'
    elif default == 'n' or default == 'no':
        opts = '[Yes, No, quit]'
    else:
        opts = '[yes, no, Quit]'
        default = 'q'
    while True:
        response = raw_input('%s %s ' % (msg, opts)).lower()
        if response == '':
            response = default
        if response == 'y' or response == 'yes':
            response = True
            break
        if response == 'n' or response == 'no':
            response = False
            break
        if response == 'q' or response == 'quit':
            sys.exit()

        print 'Answer Yes or No'

    return response

def purge_attachments(application):

    attachments_path = os.path.join(application.database.application_dir, application.sys_info['file_uploads>root_directory'])
    if not os.path.exists(attachments_path):
        print "directory '%s' does not exist cannot purge attachments" % attachments_path
        return
    if not confirm_request("Purge attachments from '%s'?" % attachments_path, 'y'):
        return
    print 'purging attachments'
    shutil.rmtree(attachments_path)

def delete(args):

    if args:
        dir = args[0]
    else:
        dir = "sample"

    from sqlalchemy import MetaData, create_engine

    this_dir = os.path.dirname(os.path.abspath(__file__))
    application_folder = os.path.join(this_dir, dir)
    sys.path.append(application_folder)
    engine = create_engine('sqlite:///%s/%s.sqlite' % (application_folder,dir))
    meta = MetaData()
    meta.reflect(bind=engine)

    if not (meta.sorted_tables and os.path.exists("%s/%s.fs" % (application_folder, dir))):
        print 'no database to delete'
        return

    if not confirm_request('Delete database?', 'y'):
        return

    print 'deleting database'
    try:
        os.remove("%s/%s.fs" % (application_folder, dir))
        os.remove("%s/%s.fs.lock" % (application_folder, dir))
        os.remove("%s/%s.fs.index" % (application_folder, dir))
        os.remove("%s/%s.fs.tmp" % (application_folder, dir))
    except OSError:
        print "zodb store not there to remove"
        pass

    for table in reversed(meta.sorted_tables):
        if not options.quiet:
            print 'deleting %s...' % table.name
        table.drop(bind=engine)

def dump(application):
    print 'dumping data'
    session = application.database.Session()
    json_dump_all_from_table(session, 'user', application.database, 'data/users.json', style = "clear")
    session.close()

def undump(application):
    print 'undumping data'
    load_json_from_file('data/users.json', application.database, 'user')


def output_sys_info(application):

    # import web so that all the system variariables get registered
    # FIXME this maybe an issue with ones added by modules
    # are the modules loaded?
    import web
    print '\n----- Application Data -----\n'
    sys_info = application.database.sys_info_full

    for key in sys_info.keys():
        print '(%s)\t%s = %s\n - %s' % (type(sys_info[key]['value']).__name__,
                                     key,
                                     sys_info[key]['value'],
                                     sys_info[key]['description'])
    print

def reload(host, options):
    import paste.reloader
    print "reloading"

    application = make_application()
    paste.reloader.install()
    run(options.host, options.port, application, options.ssl, options.ssl_cert)

def reloader(args, options):

    import subprocess

    while 1:
        try:
            command = ["python",
                       "manage.py",
                       "--reloader",
                       "--port=%s" % options.port,
                       "--host=%s" % options.host,
                      ]
            if options.ssl:
                command.append('--ssl')
            if options.ssl_cert:
                command.append('--ssl_cert=%s' % options.ssl_cert)
            if args:
                command.append(args[0])
            proc = subprocess.Popen(command)
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            break

def run(host, port, application, ssl, ssl_cert):
    print 'starting webserver'
    import beaker.middleware
    import web

    web_application = web.WebApplication(application)

    database = application.database
    database.scheduler_thread.start()

    if os.environ.get("REQUEST_METHOD", ""):
        from wsgiref.handlers import BaseCGIHandler
        BaseCGIHandler(sys.stdin, sys.stdout, sys.stderr, os.environ).run(http.app)
    else:

        import cherrypy.wsgiserver as httpserver

        web_application = beaker.middleware.SessionMiddleware(web_application, {"session.type": "memory",
                                                                        "session.auto": True})
        try:
            server = httpserver.CherryPyWSGIServer(
                    (host, int(port)), web_application,
                    server_name='rebase')
            if ssl:
                try:
                    server.ssl_certificate = '%s.cert' % ssl_cert
                    server.ssl_private_key = '%s.key' % ssl_cert
                except:
                    print 'failed to add ssl certificate or private key'
                    return
                print "serving on https://%s:%s" % (host, port)
            else:
                print "serving on http://%s:%s" % (host, port)
            server.start()
        except KeyboardInterrupt:
            server.stop()

if __name__ == "__main__":
    usage = "usage: %prog [options] package"

    parser = OptionParser(usage=usage)

    parser.add_option("-a", "--all",
                      action="store_true", dest="all",
                      help="equivilent to delete create load")

    parser.add_option("-c", "--create",
                      action="store_true", dest="create",
                      help="create the database")
    parser.add_option("-e", "--extract",
                      action="store_true", dest="extract",
                      help="extract all tables")
    parser.add_option("-l", "--load",
                      action="store_true", dest="table_load",
                      help="load all tables")
    parser.add_option("--loadfile",
                      action="store_true", dest="load",
                      help="load the data, use -f to change the file (default data.csv)")
    parser.add_option("-f", "--file",
                      action="store", dest="load_file", default = "data.csv",
                      help="specify load file (default data.csv)")
    parser.add_option("-g", "--generate", action="store_true",
                      help="generate sample file")
    parser.add_option("-d", "--delete", dest = "delete", action="store_true",
                      help="delete current database")
    parser.add_option("-r", "--run", dest = "run", action="store_true",
                      help="run the web server")
    parser.add_option("-q", "--quiet", dest = "quiet", action="store_true",
                      help="make the application less noisy")
    parser.add_option("-y", "--yes", dest = "yes_to_all", action="store_true",
                      help="automatically choose yes")
    parser.add_option("-p", "--purge", dest = "purge_attachments", action="store_true",
                      help="remove all attachment files from the file system")
    parser.add_option("--console", dest = "console", action="store_true",
                      help="start application and drop to interactive python console")
    parser.add_option("--reload", dest = "reload", action="store_true",
                      help="run with reloader")
    parser.add_option("--reloader", dest = "reloader", action="store_true",
                      help="INTERNAL, used for reload")
    parser.add_option("--host", dest = "host", action="store",
                      default = "127.0.0.1",
                      help="web server host")
    parser.add_option("--port", dest = "port", action="store",
                      default = "8000",
                      help="web server port")
    parser.add_option("-s", "--ssl",
                      action="store_true", dest="ssl",
                      help="serve using ssl")
    parser.add_option("--ssl_cert", dest = "ssl_cert", action="store",
                      default = 'host',
                      help="web server ssl certificate/private key prefix")
    parser.add_option("--sysinfo", dest = "sysinfo", action="store_true",
                      help="output system information")
    (options, args) = parser.parse_args()

    application = None

    # default application directory
    if args:
        dir = args[0]
    else:
        dir = "sample"

    if options.extract:
        extract(make_application())
    if options.delete:
        delete(args)
        # kill application as it is no longer valid
        application = None
    if options.purge_attachments:
        purge_attachments(make_application())

    if options.console:
        import code
        database = make_application().database
        code.interact(local=locals())
    if options.generate:
        generate_data(make_application())
    if options.create:
        create(make_application())
    if options.sysinfo:
        output_sys_info(make_application())
    if options.load:
        load_data(make_application(), options.load_file)
    if options.table_load:
        load(make_application())
    if options.run:
        run(options.host, options.port, make_application(), options.ssl, options.ssl_cert)
    if options.reload:
        reloader(args, options)
    if options.reloader:
        reload(args, options)
    if options.all:
        delete(args)
        application = None
        create(make_application())
        load(make_application())

