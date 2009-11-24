from tests.donkey_test import test_donkey
import sqlalchemy
from sqlalchemy import create_engine
import sys
import os


class sqlite_database(test_donkey):

    @classmethod
    def setUpClass(self):
        os.system("rm tests/test_donkey.sqlite")
        self.engine = create_engine('sqlite:///tests/test_donkey.sqlite')
        super(sqlite_database, self).setUpClass()

class mysql_database(test_donkey):

    @classmethod
    def setUpClass(self):
        os.system("mysqladmin --host=localhost drop test_donkey --force=TRUE")
        os.system("mysqladmin --host=localhost create test_donkey --force=TRUE")
        self.engine = create_engine('mysql://localhost/test_donkey')
        super(mysql_database, self).setUpClass()

class postgres_database(test_donkey):

    @classmethod
    def setUpClass(self):
        os.system("dropdb test_donkey")
        os.system("createdb test_donkey")
        self.engine = create_engine('postgres://david:@:5432/test_donkey')
        super(postgres_database, self).setUpClass()

if __name__== "__main__":

    sqlite_database.setUpClass()
    mysql_database.setUpClass()
    postgres_database.setUpClass()



