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


import os
import sys
from optparse import OptionParser

from reformed.export import json_dump_all_from_table
from reformed.data_loader import load_json_from_file
import application as app

application = None
dir = None



def create():
    application.create_database()

def extract():
    import extract
    extract.extract(application.database,
                 application.dir)

def load_data(file):
    print 'loading data'
    from reformed.data_loader import FlatFile
    flatfile = FlatFile(application.database,
                        "people",
                        file)

    flatfile.load()

def load():
    print "loading data"
    import load
    load.load(application.database,
                 application.dir)

def generate_data():
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

        print 'Answer Yes, No or Quit'

    return response

def purge_attachments():
    application.purge_attachments()

def delete():
    application.delete_database()

def dump():
    print 'dumping data'
    session = application.database.Session()
    json_dump_all_from_table(session, 'user', application.database, 'data/users.json', style = "clear")
    session.close()

def undump():
    print 'undumping data'
    load_json_from_file('data/users.json', application.database, 'user')


def output_sys_info():

    # import web so that all the system variariables get registered
    # FIXME this maybe an issue with ones added by modules
    # are the modules loaded?
    import web

    application.initialise_sys_info()
    print '\n----- Application Data -----\n'
    sys_info = application.sys_info

    for key in sys_info.keys():
        print '(%s)\t%s = %s\n - %s' % (type(sys_info[key]['value']).__name__,
                                     key,
                                     sys_info[key]['value'],
                                     sys_info[key]['description'])
    print

def reload(host, options):
    import paste.reloader
    print "reloading"
    paste.reloader.install()
    run(options.host, options.port, options.ssl, options.ssl_cert, options.no_job_scheduler)

def reloader(args, options):

    import subprocess

    application.release_all()
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
            if options.no_job_scheduler:
                command.append('-J')
            if args:
                command.append(args[0])
            proc = subprocess.Popen(command)
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            break

def run(host, port, ssl, ssl_cert, no_job_scheduler):
    print 'starting webserver'
    import beaker.middleware
    import web


    web_application = web.WebApplication(application)

    if not no_job_scheduler:
        application.start_scheduler()

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
                      help="equivilent to delete purge create load")

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
    parser.add_option("-J", "--nojobs", dest="no_job_scheduler", action="store_true",
                      help="disable job scheduler")
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

    # make application
    application = app.Application(dir, options)

    if options.extract:
        extract()
    if options.delete:
        delete()

    if options.purge_attachments and not options.delete:
        purge_attachments()

    if options.console:
        import code
        database = make_application().database
        code.interact(local=locals())
    if options.generate:
        generate_data()
    if options.create:
        create()
    if options.sysinfo:
        output_sys_info()
    if options.load:
        load_data(options.load_file)
    if options.table_load:
        load()
    if options.run:
        run(options.host, options.port, options.ssl, options.ssl_cert, options.no_job_scheduler)
    if options.reload:
        reloader(args, options)
    if options.reloader:
        reload(args, options)
    if options.all:
        delete()
        create()
        load()

