import threadpool
import threading
import tables
from fields import Text, DateTime
import time
import datetime
import traceback

POOL_SIZE = 10

class JobScheduler(object):

    def __init__(self, rdatabase, table_name = "_core_job_scheduler"):

        if not table_name in rdatabase.tables:
            rdatabase.add_table(tables.Table(table_name, 
                                            Text("job_type"), 
                                            DateTime("job_started",
                                                     default = datetime.datetime.now),
                                            DateTime("job_ended"),
                                            Text("error", length = 2000),
                                            Text("message", length = 2000)))
            rdatabase.persist()

        self.table_name = table_name
        self.database = rdatabase

        self.threadpool = threadpool.ThreadPool(POOL_SIZE)

    def add_job(self, job_type, func, args, init_message, compl_message):

        session = self.database.Session()

        job = self.database.get_instance(self.table_name)
        job.job_type = job_type.decode("utf8")
        job.message = init_message.decode("utf8")
        job.job_started = datetime.datetime.now()

        session.save(job)
        session.commit()

        job_id = job.id

        session.close()

        def callback(request, result):
            session = self.database.Session()
            job_class = self.database.get_class(self.table_name)
            job = session.query(job_class).get(job_id)
            job.message = "%s, %s" % (compl_message, result)
            job.job_ended = datetime.datetime.now()
            session.save(job)
            session.commit()

        def exc_callback(request, result):
            session = self.database.Session()
            job_class = self.database.get_class(self.table_name)
            job = session.query(job_class).get(job_id)
            job.error = "%s\n %s" % (request, "".join(traceback.format_exception(*result)))
            job.job_ended = datetime.datetime.now()
            session.save(job)
            session.commit()

        request = threadpool.makeRequests(func, [args], callback, exc_callback)
        self.threadpool.putRequest(request[0])


class JobScedulerThread(threading.Thread):


    def __init__(self, database):
        super(JobScedulerThread, self).__init__()
        self.database = database

    
    alive = False
    def run(self):

        if self.alive:
            return
        self.alive = True
        while True:
            time.sleep(2)
            try:
                self.database.job_scheduler.threadpool.poll()
            except KeyboardInterrupt:
                print "**** Interrupted!"
                break
            except threadpool.NoResultsPending:
                continue

            









    
