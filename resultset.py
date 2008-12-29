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
        

    def get_start_range(self, current_row):
        return current_row - current_row % self.result_num

    def first(self):        

        self.current_row = 0
        return self.selection_set[0]
    
    def last(self):

        last = self.selection_set.count()
        self.current_row = last -1
        return self.selection_set[last - 1]
    
    def first_set(self):

        self.current_row = 0
        return self.selection_set[0:self.result_num]

    def last_set(self):
        
        last = self.selection_set.count()
        self.current_row = self.get_start_range(last-1)
        return self.selection_set[self.current_row:
                                  self.current_row + self.result_num]

    def next(self):

        try:
            current_row = self.current_row + 1
            return self.selection_set[current_row]
        except IndexError:
            current_row = self.current_row
            return self.selection_set[current_row]
        except Exception:
            current_row = self.current_row
            raise
        finally:
            self.current_row = current_row
        
    def prev(self):

        try:
            current_row = self.current_row - 1 
            return self.selection_set[current_row]
        except IndexError:
            current_row = self.current_row
            return self.selection_set[current_row]
        except Exception:
            current_row = self.current_row
            raise
        finally:
            self.current_row = current_row

    def next_set(self):

        current_row = self.get_start_range(self.current_row +
                                               self.result_num)
        result = self.selection_set[current_row:
                                      current_row+self.result_num]
        if result:
            self.current_row = current_row
            return result
        return self.selection_set[self.current_row:
                                      self.current_row+self.result_num] 

            
    def prev_set(self):

        try:
            current_row = [self.range[1], self.range[1] + 1 + self.result_num()]
            return self.selection_set[current_row[0],range[1]]
        except IndexError:
            current_row = self.range[:]
            return self.selection_set[current_row[0], range[1]]
        finally:
            self.current_row = range[:]





        


        
        


