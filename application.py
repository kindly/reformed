import os
import sys
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
import reformed.database
from global_session import global_session

class Application(object):

    def __init__(self, dir):

        print "-----app started------"

        ##FIXME may not be the correct place for this

        self.metadata = MetaData()
        self.dir = dir
        this_dir = os.path.dirname(os.path.abspath(__file__))
        application_folder = os.path.join(this_dir, dir)

        sys.path.append(application_folder)

        self.engine = create_engine('sqlite:///%s/%s.sqlite' % (application_folder,dir))
        self.metadata.bind = self.engine
        Session = sessionmaker(bind=self.engine, autoflush = False)

        self.database = reformed.database.Database("reformed",
                                                    entity = True,
                                                    metadata = self.metadata,
                                                    engine = self.engine,
                                                    session = Session,
                                                    logging_tables = False,
                                                    zodb_store = "%s/%s.fs" % (application_folder,dir)
                                                    )


        self.load_application_data()
        # system wide settings
        self.application = self.database.sys_info

        global_session.database = self.database


    def load_application_data(self):

        # list of default data if none provided
        register = self.database.register_info

        register("public", True, "Allow unregistered users to use the application")
        register("name", 'Reformed Application', "Name of the application")

        self.get_bookmark_data()


    def get_bookmark_data(self):
        # FIXME this is hard coded for bugs

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
