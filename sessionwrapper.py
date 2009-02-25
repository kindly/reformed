from sqlalchemy.orm import attributes 
class SessionWrapper(object):
            
    def __init__(self, Session):
        self.session = Session()

    def __getattr__(self, item):
        return getattr(self.session, item)

    def close(self):
        self.session.close()

    def add(self, obj):
            
        obj._table.validate(obj)
        self.session.add(obj)
    
    def query(self, mapper):
        return self.session.query(mapper)

    def flush(self):
        self.add_logged_instances()
        self.session.flush()

    def commit(self):
        self.add_logged_instances()
        self.session.flush()
        self.session.commit()

    def add_logged_instances(self):

        for obj in self.session.dirty:
            database = obj._table.database
            table = obj._table
            if not table.logged:
                continue
            logged_instance = database.get_instance("_log_%s"%table.name)
            changed = False
            for column in table.columns.keys():
                a,b,c = attributes.get_history(attributes.instance_state(obj), column,
                                              passive = False)
                print a,b,c
                if c:
                    setattr(logged_instance, column, c[0])
                    changed = True
                else:
                    setattr(logged_instance, column, getattr(obj,column))
            if changed:
                self.session.add(logged_instance)

#       print "finished first"

class SessionClass(object):

    def __init__(self, Session):
        self.Session = Session

    def __call__(self):
        return SessionWrapper(self.Session)
       
