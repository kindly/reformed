from search import Search
from datetime import datetime, timedelta
import time

def delete_lock_tables(database, wait = "60" ):


    session = database.Session()
    search = Search(database, 
                    "_core_lock",
                    session, 
                    "date < now")

    count = 0
    for obj in search.search().all():
        count = count + 1
        session.delete(obj)


    session.commit()
    session.close()

    database.job_scheduler.add_job("delete_lock", 
                                   "delete_lock_tables",
                                    wait,
                                    time = datetime.now() + timedelta(seconds = int(wait))
                                  )



    return "number deleted = %s" % count

def wait(database, number):
    time.sleep(int(number))
    return "%s is done!" % number

def error(database, number):
    assert 1 <> 1
