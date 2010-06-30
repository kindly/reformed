from search import Search
from datetime import datetime, timedelta
import time
import util
from data_loader import FlatFile
from sqlalchemy.exceptions import ConcurrentModificationError
import data_creator

class Messager(object):

    def __init__(self, application, job_id):
        self.application = application
        self.database = application.database
        self.job_id = job_id

    def message(self, message, percent = None):

        row = self.database.search_single_data("_core_job_scheduler", "id = %s" % self.job_id, internal = True)

        row["message"] = u"%s" % message

        if percent:
            row["percent"] = percent

        # FIXME don't like this here
        try:
            util.load_local_data(self.database, row)
        except ConcurrentModificationError:
            pass



def data_load_from_file(application, job_id, **kw):

    table = kw.get("table")
    file = kw.get("file")

    flatfile = FlatFile(application.database,
                        table,
                        util.get_dir(file))

    messager = Messager(application, job_id)

    return flatfile.load(messager = messager)


def wait(application, job_id, **kw):

    number = kw.get("time")

    time.sleep(int(number))
    return "%s is done!" % number

def error(application, job_id, **kw):
    number = kw.get("time")
    assert 1 <> 1


def generate(application, job_id, **kw):

    generator = data_creator.Generator(application, **kw)

    messager = Messager(application, job_id)

    return generator.run(messager = messager)








