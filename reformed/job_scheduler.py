import threadpool
import threading
from util import load_local_data
import tables
from fields import Text, DateTime, Integer
import time
import datetime
import traceback
import standard_jobs
import sys
import logging
import json
from custom_exceptions import ThreadPoolNotInitialised

logger = logging.getLogger('reformed.main')

POOL_SIZE = 5
POLL_INTERVAL = 10

class JobScheduler(object):

    def __init__(self, application, table_name = "_core_job_scheduler"):

        self.table_name = table_name
        self.database = application.database
        self._threadpool = None

        ## FIXME why does this need the user table?
        if not table_name in self.database.tables and 'user' in self.database.tables:
            self.database.add_table(tables.Table(table_name,
                                            Text("job_type"), 
                                            Text("function"), 
                                            Text("arg"), 
                                            DateTime("job_start_time"),
                                            DateTime("job_started"),
                                            DateTime("job_ended"),
                                            Text("error", length = 5000),
                                            Text("message", length = 5000),
                                            Integer("percent"),
                                            quiet = self.database.quiet,
                                            table_type = "internal")
                               )

            self.database.persist()

    def get_threadpool(self):
        # we only want the threadpool to be created if it is actually going to be used
        # FIXME do we want some form of locking to ensure that this can only be
        # called once?
        if not self._threadpool:
            self._threadpool = threadpool.ThreadPool(POOL_SIZE)
        return self._threadpool

    def poll(self):
        self._threadpool.poll()

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

        threadpool = self._threadpool
        if threadpool:
            print 'Stopping job scheduler'
            threadpool.dismissWorkers(POOL_SIZE, do_join = True)

class JobSchedulerThread(threading.Thread):

    def __init__(self, application, maker_thread):
        super(JobSchedulerThread, self).__init__()
        self.application = application
        self.database = application.database
        self.maker_thread = maker_thread
        self.job_scheduler = application.job_scheduler
        self.alive = False
        self.threadpool = None

    def run(self):
        # get the threadpool (start if needed)
        self.threadpool = self.job_scheduler.get_threadpool()
        self.alive = True
        tick_interval = 0.1
        time_counter = 0.0

        while self.alive:


            time.sleep(tick_interval)
            if not self.maker_thread.isAlive() or self.database.status == "terminated":
                print "commencing shutdown procedures"
                self.stop()
                break

            time_counter = time_counter + tick_interval
            if time_counter > POLL_INTERVAL:
                time_counter = 0.0

            ## added as last resort 
            if time_counter == 0:
                try:
                    to_run = self.database.search("_core_job_scheduler",
                                                  "job_start_time <= now and job_started is null",
                                                  internal = True).data
    
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
                    self.job_scheduler.poll()
                except threadpool.NoResultsPending:
                    pass
    

    def stop(self):

        if self.alive:
            print 'Stopping job scheduler thread'
            self.alive = False

    def make_request(self, func, arg, job_id):

        def callback(request, result):
            session = self.database.Session()
            job_class = self.database.get_class("_core_job_scheduler")
            job = session.query(job_class).get(job_id)
            message = u"%s" % (result)
            message = message[:5000] # truncate the message if needed
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
            error = error[:5000] # truncate error if needed
            job.message = error # for now output the error as a message
            job.error = error
            job.job_ended = datetime.datetime.now()
            session.save(job)
            session.commit()
            session.close()

        if not arg:
            arg = {}

        request = threadpool.makeRequests(func, [((self.application, job_id), arg)], callback, exc_callback)

        if self.threadpool:
            self.threadpool.putRequest(request[0])
        else:
            raise ThreadPoolNotInitialised()
