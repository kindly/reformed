#!/usr/bin/env python

def attributesfromdict(d):
    self = d.pop('self')
    for n,v in d.iteritems():
        setattr(self,n,v)

class Table(object):
    def __init__(self,name):
        attributesfromdict(locals())
    def __repr__(self):
        return repr(self.__class__) +  repr(self.__dict__)

orm.mapper(self.Terma, self.terma_table, properties={
        'termb':orm.relation(self.Termb)
          })





bb = Table("bb")