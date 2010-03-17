from sqlalchemy import create_engine
import sqlalchemy as sa
from reformed.database import Database
import reformed.job_scheduler
import time
import os


class test_single_request(object):

    @classmethod
    def setUpClass(cls):

        if not hasattr(cls, "engine"):
            cls.engine = create_engine('mysql://localhost/test_donkey' )

        try:
            os.remove("tests/zodb.fs")
            os.remove("tests/zodb.fs.lock")
            os.remove("tests/zodb.fs.index")
            os.remove("tests/zodb.fs.tmp")
        except OSError:
            pass

        meta_to_drop = sa.MetaData()
        meta_to_drop.reflect(bind=cls.engine)
        for table in reversed(meta_to_drop.sorted_tables):
            table.drop(bind=cls.engine)

        cls.meta = sa.MetaData()
        cls.Sess = sa.orm.sessionmaker(bind =cls.engine, autoflush = False)
        cls.Donkey = Database("Donkey", 
                        metadata = cls.meta,
                        engine = cls.engine,
                        session = cls.Sess,
                        entity = True,
                        zodb_store = "tests/zodb.fs"
                        )

        cls.session = cls.Donkey.Session()

        reformed.job_scheduler.POLL_INTERVAL = 1
        cls.job_scheduler = cls.Donkey.job_scheduler
        cls.scheduler_thread = cls.Donkey.scheduler_thread

        cls.scheduler_thread.start()
        cls.wait3 = cls.job_scheduler.add_job("test_type", "wait", time = 4)
        cls.wait1 = cls.job_scheduler.add_job("test_type", "wait", time = 1)

        cls.waiterror = cls.job_scheduler.add_job("test_type", "error", time = 3)

        time.sleep(7)


        #cls.length_before = len(cls.Donkey.search("people")["data"])

        #cls.loader = cls.job_scheduler.add_job("loader", "data_load_from_file", "people, tests/new_people_with_header.csv")


        #cls.length_after = len(cls.Donkey.search("people")["data"])

    @classmethod
    def tearDownClass(cls):

        cls.scheduler_thread.stop()
        cls.session.close()
        sa.orm.clear_mappers()
        cls.Donkey.status = "terminated"

    def test_add_basic_job(self):

        print self.Donkey.tables
        print self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait3).message

        assert self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait3).message.count("4 is done") > 0
        assert self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait1).message.count("1 is done") > 0

        print self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait3).job_ended
        print self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait1).job_ended  

        assert self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait3).job_ended  >= \
               self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait1).job_ended  

    def test_z_add_basic_error(self):

        print self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.waiterror)

        assert self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.waiterror).error.count("AssertionError") >0

#    def test_data_loader(self):
#        assert self.length_before == self.length_after - 28


class test_job_post(test_single_request):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('postgres://david:@:5432/test_donkey')
        super(test_job_post, cls).setUpClass()

