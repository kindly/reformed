import donkey_test
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
        session.commit()
        obj.name = u"davidagain"
        obj2.amount = 100
        session.add(obj)
        session.commit()

        poo = self.Donkey.get_instance("__table_params")
        poo.key = u'plop'
        session.add(poo)
        session.commit()
        allpeople = session.query(self.Donkey.get_class("_log_people")).all()
        allspon = session.query(self.Donkey.get_class("_log_donkey_sponsership")).all()

        for a in allpeople:
            print a.name
        
        for a in allspon:
            print a.amount

        assert u"david%s" % p in [people.name for people in allpeople]
        assert u"david"  in [people.name for people in allpeople]

        
        assert p in [spon.amount for spon in allspon]
        assert 50 in [spon.amount for spon in allspon]
        
