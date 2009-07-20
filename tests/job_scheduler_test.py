import donkey_test
from reformed.job_scheduler import JobScheduler
import time


class test_single_request(donkey_test.test_donkey):

    @classmethod
    def setUpClass(cls):
        super(test_single_request, cls).setUpClass()

        #cls.job_scheduler = JobScheduler(cls.Donkey)
        cls.job_scheduler = cls.Donkey.job_scheduler

    def test_add_basic_job(self):

        def func(number):
            time.sleep(number)
            return "%s is done!" % number

        self.job_scheduler.add_job("test_type", func, 2, u"started", u"finished")
        self.job_scheduler.add_job("test_type", func, 1, u"started", u"finished")

        self.job_scheduler.threadpool.wait()

        assert self.session.query(self.Donkey.get_class("_core_job_scheduler"))[0].message.count("2 is done") > 0
        assert self.session.query(self.Donkey.get_class("_core_job_scheduler"))[1].message.count("1 is done") > 0

        assert self.session.query(self.Donkey.get_class("_core_job_scheduler"))[0].job_ended  > \
               self.session.query(self.Donkey.get_class("_core_job_scheduler"))[1].job_ended  


        
    def test_z_add_basic_error(self):

        def func(number):
            assert 1 <> 1

        self.job_scheduler.add_job("test_type", func, 3, "started", "finished")

        self.job_scheduler.threadpool.wait()
        
        assert self.session.query(self.Donkey.get_class("_core_job_scheduler"))[2].error.count("AssertionError") >0


