from search import Search
from datetime import datetime, timedelta
import time

def delete_lock_tables(database, wait = 60 * 5):


    session = database.Session()
    search = Search(database, 
                    "_core_lock",
                    session, 
                    database.t._core_lock.date <\
                    datetime.now() - timedelta(minutes = 1))

    count = 0
    for obj in search.search().all():
        count = count + 1
        session.delete(obj)


    session.commit()
    session.expunge_all()

    time.sleep(wait)

    database.job_scheduler.add_job("delete_lock", 
                                   delete_lock_tables,
                                   database,
                                   "running",
                                   "stopped")

    return "number deleted = %s" % count

