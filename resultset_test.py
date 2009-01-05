from fields import *
from tables import *
from database import *
from nose.tools import assert_raises,raises
import sqlalchemy as sa
from sqlalchemy import create_engine
import logging
from donkey_test import test_donkey

logging.basicConfig(filename = "sql.txt")
logging.getLogger('sqlalchemy.engine').setLevel(logging.info)

class test_result_set_basic(test_donkey):

    def test_get_first_last_row(self):

        results = self.Donkey.query(self.session, "donkey")
        first = results.first()
        assert first.name == "jim"

        results = self.Donkey.query(self.session, "donkey")
        last = results.last()
        assert last.name == "jim0"

    def test_get_first_last_set(self):

        results = self.Donkey.query(self.session, "donkey")
        first_set = results.first_set()
        assert [donkey.name for donkey in first_set] == [u'jim',
                                                         u'jim1',
                                                         u'jim2',
                                                         u'jim3',
                                                         u'jim4']
        
        results = self.Donkey.query(self.session, "donkey")
        last_set = results.last_set()
        assert [donkey.name for donkey in last_set] == [u'jim0']

    def test_get_next_prev_item(self):

        results = self.Donkey.query(self.session, "donkey")
        first = results.first()
        next = results.next()
        assert next.name== u"jim1"
        next2 = results.next()
        assert next2.name== u"jim2"
        prev = results.prev()
        assert prev.name== u"jim1"
        prev2 = results.prev()
        assert prev2.name== u"jim"
        prev3 = results.prev()
        assert prev3.name== u"jim"

        last = results.last()
        assert last.name== u"jim0"
        lastprev = results.prev()
        assert lastprev.name == u"jim9"
        last2 = results.next()
        assert last2.name == u"jim0"
        last3 = results.next()
        assert last3.name == u"jim0"



    def test_get_next_prev_set(self):

        results = self.Donkey.query(self.session, "donkey")
        firstset = results.first_set()
        nextset = results.next_set()

        assert [donkey.name for donkey in nextset] == [u'jim5',
                                                        u'jim6',
                                                        u'jim7',
                                                        u'jim8',
                                                        u'jim9']
        nextset2 = results.next_set()
        assert [donkey.name for donkey in nextset2] == [u'jim0']

        nextset3 = results.next_set()
        assert [donkey.name for donkey in nextset3] == [u'jim0']

        prevset = results.prev_set()
        assert [donkey.name for donkey in prevset] == [u'jim5',
                                                        u'jim6',
                                                        u'jim7',
                                                        u'jim8',
                                                        u'jim9']
        prevset2 = results.prev_set()
        prevset3 = results.prev_set()
        
        assert [donkey.name for donkey in prevset3] == [u'jim',
                                                         u'jim1',
                                                         u'jim2',
                                                         u'jim3',
                                                         u'jim4']
