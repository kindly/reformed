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
import reformed.database
from global_session import global_session
import reformed.job_scheduler as job_scheduler

class Application(object):

    def __init__(self, dir, runtime_options = None):

        self.metadata = MetaData()
        self.dir = dir
        this_dir = os.path.dirname(os.path.abspath(__file__))
        application_folder = os.path.join(this_dir, dir)

        sys.path.append(application_folder)

        self.engine = create_engine('sqlite:///%s/%s.sqlite' % (application_folder,dir))
       # self.engine = create_engine('postgres://kindly:ytrewq@localhost:5432/bug')
        self.metadata.bind = self.engine
        Session = sessionmaker(bind=self.engine, autoflush = False)

        if runtime_options and runtime_options.quiet:
            quiet = True
        else:
            quiet = False

        self.database = reformed.database.Database("reformed",
                                                    entity = True,
                                                    metadata = self.metadata,
                                                    engine = self.engine,
                                                    session = Session,
                                                    logging_tables = False,
                                                    quiet = quiet,
                                                    application_dir = application_folder,
                                                    zodb_store = os.path.join(application_folder, 'zodb.fs')
                                                    )

        self.job_scheduler = job_scheduler.JobScheduler(self)
        self.scheduler_thread = job_scheduler.JobSchedulerThread(self, threading.currentThread())

        self.manager_thread = ManagerThread(self, threading.currentThread())
        self.manager_thread.start()

        # system wide settings
        global_session.application = self
        global_session.database = self.database


    def get_bookmark_data(self):
        # FIXME this is hard coded for bugs
        # FIXME can this be removed
        register = self.database.register_info
        register("bookmarks>user>title", "Users")
        register("bookmarks>user>node", "bug.User")
        register("bookmarks>ticket>title", "Ticket")
        register("bookmarks>ticket>node", "bug.Ticket")
        register("bookmarks>user_group>title", "User Group")
        register("bookmarks>user_group>node", "bug.UserGroup")
        register("bookmarks>permission>title", "Permission")
        register("bookmarks>permission>node", "bug.Permission")
        register("bookmarks>_system_info>title", "System Settings")
        register("bookmarks>_system_info>node", "bug.SysInfo")


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
