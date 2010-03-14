import threadpool
import threading
from util import load_local_data, get_all_local_data
import tables
from fields import Text, DateTime, Integer
import time
import datetime
import traceback
import standard_jobs
import sys
import logging
import json
from sqlalchemy import and_

logger = logging.getLogger('reformed.main')

POOL_SIZE = 5
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
                                            Text("message", length = 2000),
                                            Integer("percent"),
                                            table_type = "internal")
                               )

            rdatabase.persist()

        self.table_name = table_name
        self.database = rdatabase

        self.threadpool = threadpool.ThreadPool(POOL_SIZE)

    def add_job(self, job_type, func, run_time = datetime.datetime.now(), **kw):

        try:
            session = self.database.Session()
            job = self.database.get_instance(self.table_name)
            job.job_type = job_type.decode("utf8")
            if kw:
                job.arg = u"%s" % json.dumps(kw)
            job.job_start_time = run_time
            job.function = u"%s" % func
            job.message = u'waiting'
            session.save(job)
            # FIXME this does not look safe against exceptions
            session.commit()
            job_id = job.id
            return job_id
        except Exception:
            print >> sys.stderr, "%s %s" % ("error in adding job",
                                            traceback.format_exc())
        finally:
            session.close()

    def stop(self):

        self.shut_down_all_threads()

    def shut_down_all_threads(self):

        threadpool = self.threadpool

        threadpool.dismissWorkers(POOL_SIZE)
        threadpool.joinAllDismissedWorkers()

class JobSchedulerThread(threading.Thread):

    def __init__(self, database, maker_thread):
        super(JobSchedulerThread, self).__init__()
        self.database = database
        self.maker_thread = maker_thread
        self.job_scheduler = database.job_scheduler
        self.threadpool = self.job_scheduler.threadpool
        self.alive = False

    def run(self):

        self.alive = True

        while self.alive:

            ## added to make sure query does not run and clean up
            if not self.maker_thread.isAlive() or self.database.status == "terminated":
                print "commmencing shutdown procedures"
                self.stop()
                break


            ## added as last resort 
            try:
                to_run = self.database.search("_core_job_scheduler",
                                              "job_start_time <= now and job_started is null",
                                              internal = True)["data"]

                for result in to_run:
                    result["job_started"] = datetime.datetime.now()
                    result["message"] = "starting"
                    result["__table"] = "_core_job_scheduler"
                    func = getattr(standard_jobs, result["function"].encode("ascii"))
                    arg = result["arg"]
                    if arg:
                        arg = json.loads(arg, encoding = "ascii")
                        arg = dict((item[0].encode("ascii"), item[1])
                                   for item in arg.items())
                    self.make_request(func, arg, result["id"])
                    load_local_data(self.database, result)
            except Exception:
                print >> sys.stderr, "%s %s" % ("error in schedular thread shutting down",
                                                traceback.format_exc())
                self.stop()
                break


            try:
                self.database.job_scheduler.threadpool.poll()
            except threadpool.NoResultsPending:
                pass

            time_counter = 0

            while time_counter <= POLL_INTERVAL:
                if not self.maker_thread.isAlive() or self.database.status == "terminated":
                    print "commencing shutdown procedures"
                    self.stop()
                    break
                time_counter = time_counter + 1
                time.sleep(1)

    def stop(self):

        if self.alive:
            self.alive = False

    def make_request(self, func, arg, job_id):

        def callback(request, result):
            session = self.database.Session()
            job_class = self.database.get_class("_core_job_scheduler")
            job = session.query(job_class).get(job_id)
            message = u"%s" % (result)
            message = message[:2000] # truncate the message if needed
            job.message = message
            job.job_ended = datetime.datetime.now()
            session.save(job)
            session.commit()
            session.close()

        def exc_callback(request, result):
            ## FIXME sqlalchemy calls need some crash protection for
            ## out of our control stuff ie network failures
            session = self.database.Session()
            job_class = self.database.get_class("_core_job_scheduler")
            job = session.query(job_class).get(job_id)
            #FIXME this may not be the correct error trace
            error = u"%s\n %s" % (request, "".join(traceback.format_exception(*result)))
            logger.error(error)
            error = error[:2000] # truncate error if needed
            job.message = error # for now output the error as a message
            job.error = error
            job.job_ended = datetime.datetime.now()
            session.save(job)
            session.commit()
            session.close()

        if arg:
            request = threadpool.makeRequests(func, [((self.database, job_id), arg)], callback, exc_callback)
        else:
            request = threadpool.makeRequests(func, [((self.database, job_id), {})], callback, exc_callback)

        self.threadpool.putRequest(request[0])


