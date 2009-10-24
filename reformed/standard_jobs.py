from search import Search
from datetime import datetime, timedelta
import time
from data_loader import FlatFile

def data_load_from_file(database, job_id, input = None):

    table, file = [attrib.strip() for attrib in input.strip().split(",")]

    flatfile = FlatFile(database,
                        table,
                        file)

    flatfile.load()
    



def delete_lock_tables(database, job_id, wait = "60"):


    session = database.Session()
    search = Search(database, 
                    "_core_lock",
                    session, 
                    "date < now - 30 mins")

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

def wait(database, job_id, number):
    time.sleep(int(number))
    return "%s is done!" % number

def error(database, job_id, number):
    assert 1 <> 1
