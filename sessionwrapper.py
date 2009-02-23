class SessionWrapper(object):
    
    def __init__(self, Session):
        self.session = Session()

    def __getattr__(self, item):
        return getattr(self.session, item)

    def close(self):
        self.session.close()

    def add(self, obj):
        self.session.add(obj)
    
    def query(self, mapper):
        return self.session.query(mapper)

class SessionClass(object):

    def __init__(self, Session):
        self.Session = Session

    def __call__(self):
        return SessionWrapper(self.Session)
       
