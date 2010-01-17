import donkey_test
import sqlalchemy as sa
import reformed.custom_exceptions
from nose.tools import assert_raises
import random

class test_session_wrapper(donkey_test.test_donkey):

    def test_add_logged_instances(self):

        p = random.randrange(1,10000)
        session = self.Donkey.Session()
        obj = session.query(self.Donkey.get_class("people")).first()
        obj.name = u"david%s" % p
        obj2 =  obj.donkey_sponsership[0]
        obj2.amount = p
        session.add(obj)
        session.add(obj2)
        session.commit()
        obj.name = u"davidagain"
        obj2.amount = 100
        session.add(obj)
        session.add(obj2)
        session.commit()

        allpeople = session.query(self.Donkey.get_class("_log_people")).all()
        allspon = session.query(self.Donkey.get_class("_log_donkey_sponsership")).all()

        assert u"david%s" % p in [people.name for people in allpeople]
        assert u"david"  in [people.name for people in allpeople]
        
        assert p in [spon.amount for spon in allspon]
        assert 50 in [spon.amount for spon in allspon]

    def test_zz_locking(self):

        session1 = self.Donkey.Session()
        person = session1.query(self.Donkey.aliases["people"]).first()
        person.name = u"poo"
        session1.save(person)
        
        session2 = self.Donkey.Session()
        person = session2.query(self.Donkey.aliases["people"]).first()
        person.name = u"poo"
        session2.save(person)

        session1.commit()
        assert_raises(sa.orm.exc.ConcurrentModificationError, session2.commit)



