def attributesfromdict(d):
    self = d.pop('self')
    for n,v in d.iteritems():
        setattr(self,n,v)
        
def attributesfromkw(d):
    self = d.pop('self')
    kw = d.pop('kw')
    for p,q in kw.iteritems():
        setattr(self,p,q)        


