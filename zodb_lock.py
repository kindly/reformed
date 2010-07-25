import os
from ZODB import FileStorage, DB
from zc.lockfile import LockError

def aquire_zodb_lock(zodb_location):

    return FileStorage.FileStorage(zodb_location)


def store_zodb(func):

    def inner_function(self, *args, **kw):

        app = kw.pop("application")
        zodb_location = os.path.join(app.application_folder, 'zodb.fs')

        counter = 0
        while 1:
            if counter % 10 == 1:
                print "zodb lock at %s tries" % counter
            try:
                storage = aquire_zodb_lock(zodb_location)
                break
            except LockError:
                continue

        zodb = DB(storage)
        func(self, zodb, *args, **kw)

        app.get_zodb(True)

        zodb.close()

    return inner_function
