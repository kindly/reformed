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
POLL_INTERVAL = 5

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

    def add_job(self, job_type, func, arg):

        session = self.database.Session()

        job = self.database.get_instance(self.table_name)
        job.job_type = job_type.decode("utf8")
        if arg:
            job.arg = arg
        job.job_start_time = datetime.datetime.now()
        job.function = func
        session.save(job)
        session.commit()
        job_id = job.id
        session.close()
        return job_id


class JobScedulerThread(threading.Thread):

    def __init__(self, database):
        super(JobScedulerThread, self).__init__()
        self.database = database
        self.threadpool = self.database.job_scheduler.threadpool
        self.deamon = True

    alive = False
    def run(self):

        if self.alive:
            return
        self.alive = True
        while True:

            #to_run = self.database.search("_core_job_scheduler",
            #                              "job_start_time <= now and job_started is null") 

            time.sleep(POLL_INTERVAL)

            session = self.database.Session()
            table = self.database.t._core_job_scheduler
            res = session.query(table).filter(and_(table.job_start_time <= datetime.datetime.now(), table.job_started == None)).all()
            to_run = [get_all_local_data(obj, keep_all = True, allow_system = True) for obj in res]    

            logger.info(to_run)
        

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
            except KeyboardInterrupt:
                print "**** Interrupted!"
                break
            except threadpool.NoResultsPending:
                continue

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

        request = threadpool.makeRequests(func, [((self.database, arg), {})], callback, exc_callback)
        self.threadpool.putRequest(request[0])

