##   This file is part of Reformed.
##
##   Reformed is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License version 2 as 
##   published by the Free Software Foundation.
##
##   Reformed is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with Reformed.  If not, see <http://www.gnu.org/licenses/>.
##
##   -----------------------------------------------------------------
##	
##   Reformed
##   Copyright (c) 2008-2009 Toby Dacre & David Raznick
##	
##	resultset.py
##	======
##	
##	This file is experimental

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
        except:
            current_row = 1 
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
        except:
            current_row = 1
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

        current_row = self.get_start_range(self.current_row -
                                               self.result_num)
        result = self.selection_set[current_row:
                                      current_row+self.result_num]
        if result and current_row >= 0:
            self.current_row = current_row
            return result
        return self.selection_set[self.current_row:
                                      self.current_row+self.result_num] 
