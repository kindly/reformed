import threadpool
import threading
from util import load_local_data, get_all_local_data
import tables
from fields import Text, DateTime
import time
import datetime
import traceback
import standard_jobs
import logging
from sqlalchemy import and_

logger = logging.getLogger('reformed.main')

POOL_SIZE = 10
POLL_INTERVAL = 10

class JobScheduler(object):

    def __init__(self, rdatabase, table_name = "_core_job_scheduler"):

        if not table_name in rdatabase.tables:
            rdatabase.add_table(tables.Table(table_name, 
                                            Text("job_type"), 
                                            Text("function"), 
                                            Text("arg"), 
                                            DateTime("job_start_time"),
                                            DateTime("job_started"),
                                            DateTime("job_ended"),
                                            Text("error", length = 2000),
                                            Text("message", length = 2000)))
            rdatabase.persist()

        self.table_name = table_name
        self.database = rdatabase

        self.threadpool = threadpool.ThreadPool(POOL_SIZE)

    def add_job(self, job_type, func, arg = None, **kw):

        session = self.database.Session()

        run_time = kw.get("time", datetime.datetime.now())

        job = self.database.get_instance(self.table_name)
        job.job_type = job_type.decode("utf8")
        if arg:
            job.arg = u"%s" % arg
        job.job_start_time = run_time
        job.function = u"%s" % func
        session.save(job)
        session.commit()
        job_id = job.id
        session.close()
        return job_id


    def shut_down_all_threads(self):

        threadpool = self.database.job_scheduler.threadpool

        threadpool.dismissWorkers(POOL_SIZE)
        threadpool.joinAllDismissedWorkers()

        if self.database.schedular_thread:
            self.database.schedular_thread.alive = False
            self.database.schedular_thread.join()

        



class JobSchedulerThread(threading.Thread):

    def __init__(self, database, maker_thread):
        super(JobSchedulerThread, self).__init__()
        self.database = database
        self.maker_thread = maker_thread
        self.job_scheduler = JobScheduler(self.database)

    alive = False
    def run(self):

        if self.alive:
            return

        self.threadpool = self.job_scheduler.threadpool

        self.alive = True
        while self.alive:

            to_run = self.database.search("_core_job_scheduler",
                                          "job_start_time <= now and job_started is null") 

            for result in to_run:
                result["_core_job_scheduler.job_started"] = datetime.datetime.now()
                result["_core_job_scheduler.message"] = "started"
                result["__table"] = "_core_job_scheduler"
                func = getattr(standard_jobs, result["_core_job_scheduler.function"].encode("ascii"))
                arg = result["_core_job_scheduler.arg"]
                if arg:
                    arg = arg.encode("ascii")
                self.make_request(func, arg, result["_core_job_scheduler.id"])
                load_local_data(self.database, result)



            try:
                self.database.job_scheduler.threadpool.poll()
            except threadpool.NoResultsPending:
                pass

            time_counter = 0


            while time_counter <= POLL_INTERVAL:
                if not self.maker_thread.isAlive():
                    print "commmencing shutdown procedures"
                    self.shut_down_all_threads()
                    self.alive = False
                    break
                time_counter = time_counter + 1
                time.sleep(1)

    def stop(self):

        self.alive = False

    def make_request(self, func, arg, job_id):

        def callback(request, result):
            session = self.database.Session()
            job_class = self.database.get_class("_core_job_scheduler")
            job = session.query(job_class).get(job_id)
            job.message = u"%s" % (result)
            job.job_ended = datetime.datetime.now()
            session.save(job)
            session.commit()
            session.close()

        def exc_callback(request, result):
            session = self.database.Session()
            job_class = self.database.get_class("_core_job_scheduler")
            job = session.query(job_class).get(job_id)
            job.error = u"%s\n %s" % (request, "".join(traceback.format_exception(*result)))
            job.job_ended = datetime.datetime.now()
            session.save(job)
            session.commit()
            session.close()

        if arg:
            request = threadpool.makeRequests(func, [((self.database, arg), {})], callback, exc_callback)
        else:
            request = threadpool.makeRequests(func, [((self.database, ), {})], callback, exc_callback)

        self.threadpool.putRequest(request[0])

    def shut_down_all_threads(self):

        threadpool = self.threadpool

        threadpool.dismissWorkers(POOL_SIZE)
        threadpool.joinAllDismissedWorkers()

