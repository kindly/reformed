import donkey_persist_test
from sqlalchemy import MetaData, create_engine
from reformed.standard_jobs import wait
import reformed.job_scheduler
import time


class test_single_request(donkey_persist_test.test_donkey_persist_mysql):

    @classmethod
    def setUpClass(cls):
        super(test_single_request, cls).setUpClass()
        reformed.job_scheduler.POLL_INTERVAL = 1
        cls.job_scheduler = cls.Donkey.job_scheduler
        cls.scheduler_thread = cls.Donkey.scheduler_thread

        cls.scheduler_thread.start()
        cls.wait3 = cls.job_scheduler.add_job("test_type", "wait", "3")
        cls.wait1 = cls.job_scheduler.add_job("test_type", "wait", "1")
        cls.waiterror = cls.job_scheduler.add_job("test_type", "error", "3")

        cls.length_before = len(cls.Donkey.search("people"))

        cls.loader = cls.job_scheduler.add_job("loader", "data_load_from_file", "people, tests/new_people_with_header.csv")

        time.sleep(7)

        cls.length_after = len(cls.Donkey.search("people"))

    @classmethod
    def tearDownClass(cls):
        cls.scheduler_thread.stop()

    def test_add_basic_job(self):

        assert self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait3).message.count("3 is done") > 0
        assert self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait1).message.count("1 is done") > 0

        print self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait3).job_ended
        print self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait1).job_ended  

        assert self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait3).job_ended  >= \
               self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.wait1).job_ended  

    def test_z_add_basic_error(self):

        def func(number):
            assert 1 <> 1


        self.job_scheduler.threadpool.wait()
        
        assert self.session.query(self.Donkey.get_class("_core_job_scheduler")).get(self.waiterror).error.count("AssertionError") >0

    def test_data_loader(self):
        assert self.length_before == self.length_after - 28

