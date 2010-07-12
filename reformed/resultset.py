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
##	This file is produces a result set.

import reformed.util as util

class ResultSet(object):

    def __init__(self, search, *arg, **kw):


        self.search = search

        self.session = search.session

        self.limit = int(kw.get("limit", 0))
        self.offset = int(kw.get("offset", 0))
        self.internal = kw.get("internal", False)
        self.count = kw.get("count", False)
        self.keep_all = kw.get("keep_all", True)

        self.database = search.database

        self.order_by = kw.pop("order_by", None)
        self.result_num = kw.pop("result_num", 5)

        self.tables = kw.get("tables", [search.table])
        self.fields = kw.get("fields", None)

        self.row_count = None
        self.results = None
        self._data = None

        self.current_row = 0

    @property
    def data(self):
        if self._data is None:
            self.create_data()

        return self._data

    def create_data(self):

        if self.results is None:
            self.collect()

        results = self.results

        self._data = []
        for res in results:
            if self.select_path_list:
                ##FIXME need to get out all data somehow
                obj = res[0]
            else:
                obj = res
            extra_obj = None

            self._data.append(util.get_all_local_data(obj,
                                   tables = self.tables,
                                   fields = self.fields,
                                   internal = self.internal,
                                   keep_all = self.keep_all,
                                   allow_system = True,
                                   extra_obj = extra_obj))

    def collect(self):

        if self.results is not None:
            return

        self.query = self.search.search()

        distict_select_paths = set()
        for table in self.search.all_extra:
            distict_select_paths.add(self.search.name_to_path[table])

        self.select_path_list = list(distict_select_paths)

        for key in self.select_path_list:
            self.query = self.query.add_entity(self.search.aliases[key])

        if self.limit:
            self.results = self.query[self.offset: self.offset + self.limit]
        else:
            self.results = self.query.all()

        if self.count:
            self.row_count = self.query.count()

    def get(self, name):

        if name.count(">"):
            table, field = name.split(".")
        else:
            name_list = name.split(".") 
            field = name_list[-1]
            if len(name_list) > 1:
                table = ".".join(name_list[:-1])
            else:
                table = self.search.table

        if self.select_path_list:
            if table == self.search.table:
                obj = self.results[self.current_row][0]
            else:
                path = self.search.name_to_path[table]
                index = self.select_path_list.index(path) + 1
                obj = self.results[self.current_row][index]
        else:
            obj = self.results[self.current_row]

        """ when a left join in not there none is returned"""
        if obj is None:
            return

        if field in obj._table.columns.keys() + ["id"]:
            return util.convert_value(getattr(obj, field))

        if field in obj._table.relation_attributes:
            return getattr(obj, field)



    def get_start_range(self, current_row):
        return current_row - current_row % self.result_num

    def all(self):

        return self.selection_set.all()

    def first(self):

        self.current_row = 0
        return self.selection_set[0]
    
    def last(self):

        last = self.selection_set.count()
        self.current_row = last -1
        return self.selection_set[last - 1]
    
    def first_set(self):

        self.current_row = 0
        return self.selection_set[self.offset : self.offset + self.result_num]

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
