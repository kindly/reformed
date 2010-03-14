from search import Search
from datetime import datetime, timedelta
import time
import util
from data_loader import FlatFile

class Messager(object):

    def __init__(self, database, job_id):
        self.database = database
        self.job_id = job_id

    def message(self, message, percent = None):

        row = self.database.search_single("_core_job_scheduler", "id = %s" % self.job_id, internal = True)

        row["message"] = u"%s" % message

        if percent:
            row["percent"] = percent

        util.load_local_data(self.database, row)


def data_load_from_file(database, job_id, **kw):

    table = kw.get("table")
    file = kw.get("file")

    flatfile = FlatFile(database,
                        table,
                        util.get_dir(file))

    messager = Messager(database, job_id)

    return flatfile.load(messager = messager)


def wait(database, job_id, **kw):

    number = kw.get("time")

    time.sleep(int(number))
    return "%s is done!" % number

def error(database, job_id, **kw):
    number = kw.get("time")
    assert 1 <> 1
