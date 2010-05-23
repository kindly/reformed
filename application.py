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


import threading
import os
import time
import os.path
import sys
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from ZODB import FileStorage, DB
from ZODB.PersistentMapping import PersistentMapping
import transaction
import reformed.database
from global_session import global_session
import reformed.job_scheduler as job_scheduler
import predefine
import logging
import node_runner

log = logging.getLogger('rebase.application')

class Application(object):

    def __init__(self, dir, runtime_options = None, engine = None):


        self.dir = dir
        self.root_folder = os.path.dirname(os.path.abspath(__file__))
        self.application_folder = os.path.join(self.root_folder, dir)

        self.logging_setup()

        sys.path.append(self.application_folder)


        if engine:
            self.engine = create_engine(engine)
        else:
            self.engine = create_engine('sqlite:///%s/%s.sqlite' % (self.application_folder,dir))
            #self.engine = create_engine('postgres://kindly:ytrewq@localhost:5432/bug')

        self.metadata = MetaData()
        self.metadata.bind = self.engine
        Session = sessionmaker(bind=self.engine, autoflush = False)

        if runtime_options and runtime_options.quiet:
            quiet = True
        else:
            quiet = False

        ##FIXME need proper options
        logging_tables = False if runtime_options else True

        # zodb data store
        zodb_store = os.path.join(self.application_folder, 'zodb.fs')
        storage = FileStorage.FileStorage(zodb_store)
        self.zodb = DB(storage)

        # sys info
        self.sys_info = {}  # used for quick access to the system variables
        self.sys_info_full = {} # store of the full system info

        connection = self.zodb.open()
        root = connection.root()
        if "sys_info" not in root:
            root["sys_info"] = PersistentMapping()
            transaction.commit()
        else:
            self.cache_sys_info(root["sys_info"])
        connection.close()


        self.database = reformed.database.Database("reformed",
                                                    application = self,
                                                    entity = True,
                                                    metadata = self.metadata,
                                                    engine = self.engine,
                                                    session = Session,
                                                    logging_tables = logging_tables,
                                                    quiet = quiet
                                                    )

        self.job_scheduler = job_scheduler.JobScheduler(self)
        self.scheduler_thread = job_scheduler.JobSchedulerThread(self, threading.currentThread())

        self.manager_thread = ManagerThread(self, threading.currentThread())
        self.manager_thread.start()

        self.predefine = predefine.Predefine(self)

        self.get_bookmark_data()
        # system wide settings
        global_session.application = self
        global_session.database = self.database
        self.load_nodes()


    def load_nodes(self):
        self.node_manager = node_runner.NodeManager(self)
        # FIXME this is a dirty hack
        # we need to store state about the application
        # at least empty/tables created
        # but really this is part of application.py restructuring and being able to handle
        # delete create etc
        if len(self.database.tables) > 1:
            self.node_manager.get_nodes()

    def logging_setup(self):

        self.log_dir = os.path.join(self.application_folder, "log")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        self.create_logger("database", "rebase.application.database")
        self.create_logger("application")
        self.create_logger("node")
        self.create_logger("web")
        self.create_logger("rebase", "rebase", log_name = True)
        self.create_logger("rebase", "rebase", log_name = True, error_logger = True)

        self.create_logger("zodb", "ZODB.FileStorage")
        self.create_logger("sql", "sqlalchemy.engine")

    def create_logger(self, name, logger_name = None, log_name = False, error_logger = False):

        if not logger_name:
            logger_name = 'rebase.%s' % name

        if log_name:
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        else:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        if error_logger:
            log_file = os.path.join(self.log_dir, "%s.error" % name)
        else:
            log_file = os.path.join(self.log_dir, "%s.log" % name)

        handler = logging.FileHandler(log_file)
        handler.setFormatter(formatter)
        if error_logger:
            handler.setLevel(logging.ERROR)
        else:
            handler.setLevel(logging.DEBUG)

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        logger.addHandler(handler)


    def get_bookmark_data(self):
        # FIXME this is hard coded for bugs
        # need a better solution
        # maybe get the nodes to register themselves?

        bookmarks = {}
        bookmarks['user'] = dict(title = "Users", node = "bug.User")
        bookmarks['ticket'] = dict(title = "Ticket", node = "bug.Ticket")
        bookmarks['user_group'] = dict(title = "User Group", node = "bug.UserGroup")
        bookmarks['permission'] = dict(title = "Permission", node = "bug.Permission")
        bookmarks['permission'] = dict(title = "Permission", node = "bug.Permission")
        self.register_info('bookmarks', bookmarks)

        #register("bookmarks>_system_info>title", "System Settings")
        #register("bookmarks>_system_info>node", "bug.SysInfo")





    def register_info(self, key, value, description = '', force = False):
        """register system info adds the info if it is not already there"""

        connection = self.zodb.open()
        root = connection.root()

        if force or key not in root["sys_info"]:
            # add/update the value
            data = dict(value = value, description = description, read_only = force)
            root["sys_info"][key] = data
            self.sys_info_full[key] = data
            self.sys_info[key] = value

            #TODO make sure on concurrent changes recache data?
            try:
                transaction.commit()
            except:
                raise

        else:
            value = self.sys_info[key]

        connection.close()

        return value


    def cache_sys_info(self, sys_info_db):
        """get system info out of the database"""
        for key, value in sys_info_db.iteritems():
            self.sys_info_full[key] = value
            self.sys_info[key] = value['value']



class ManagerThread(threading.Thread):

    def __init__(self, application, initiator_thread):

        super(ManagerThread, self).__init__()
        self.initiator_thread = initiator_thread
        self.application = application

    def run(self):

        while True:
            if not self.initiator_thread.isAlive():
                self.application.database.status = "terminated"
                if self.application.job_scheduler:
                    self.application.job_scheduler.stop()
                break
            time.sleep(0.1)
