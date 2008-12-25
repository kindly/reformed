class ResultSet(object):

    def __init__(self, database, session, queryset, *arg, **kw):

        self.database = database
        self.session = session
        self.queryset = queryset
        self.queryclass = self.database.tables[self.queryset].sa_class
        self.order_by = kw.pop("order_by", 'id')
        self.result_num = kw.pop("result_num", 5)
        self.ordered = getattr(self.queryclass,self.order_by)
        self.selection_set = self.session.query(self.queryclass).\
                order_by(self.ordered)
        

    def first(self):        

        self.range = [0,1]
        return self.selection_set[0]
    
    def last(self):

        last = self.selection_set.count()
        self.range = [last -1, last]
        return self.selection_set[last - 1]
    
    def first_set(self):

        self.range = [0, self.result_num]
        return self.selection_set[0:self.result_num]

    def last_set(self):
        
        last = self.selection_set.count()
        self.range = [last - self.result_num, last]
        return self.selection_set[last  - self.result_num: last]

    def next(self):

        try:
            range = [self.range[1], self.range[1] +1] 
            return self.selection_set[range[0]]
        except IndexError:
            range = self.range[:]
            return self.selection_set[range[0]]
        finally:
            self.range = range[:]
        
    def prev(self):

        try:
            range = [self.range[0] - 1 , self.range[0]] 
            return self.selection_set[range[0]]
        except IndexError:
            range = self.range[:]
            return self.selection_set[range[0]]
        finally:
            self.range = range[:]

    def next_set(self):

        try:
            range = [self.range[1], self.range[1] + self.result_num]
            return self.selection_set[range[0]:range[1]]
        except IndexError:
            range = self.range[:]
            return self.selection_set[range[0]:range[1]]
        except Exception:
            range = self.range[:]
            raise
        finally:
            self.range = range[:]

    def prev_set(self):

        try:
            range = [self.range[1], self.range[1] + 1 + self.result_num()]
            return self.selection_set[range[0],range[1]]
        except IndexError:
            range = self.range[:]
            return self.selection_set[range[0], range[1]]
        finally:
            self.range = range[:]





        


        
        


