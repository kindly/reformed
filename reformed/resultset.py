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
        self.result_row = None
        self.current_result = None

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
            if self.search.select_path_list:
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

        for key in self.search.select_path_list:
            self.query = self.query.add_entity(self.search.aliases[key])

        if self.limit:
            self.results = self.query[self.offset: self.offset + self.limit]
        else:
            self.results = self.query.all()
        self.results_length = len(self.results)

        if self.count:
            self.row_count = self.query.count()

    def get(self, name):

        if self.current_row == self.result_row:
            result = self.current_result
        else:
            self.result_row = self.current_row
            self.current_result = Result(self.search,
                                         self.results[self.current_row])
            result = self.current_result

        return result.get(name)


    def __iter__(self):

        self.current_row = -1
        return self

    def next(self):

        if self.current_row + 1 >= self.results_length:
            raise StopIteration

        self.current_row = self.current_row + 1
        return Result(self.search, self.results[self.current_row])

class Result(object):

    def __init__(self, search, row = None):

        self.search = search
        self.data = None

        if row:
            self.data = row
            self.new = False
        else:
            self.new = True

    def get(self, name):

        node = self.search.rtable.get_edge_from_field(name)
        if node:
            table = node.table
        else:
            table = self.search.table

        field = name.split(".")[-1]

        if self.search.select_path_list:
            if table == self.search.table:
                obj = self.data[0]
            else:
                node_path = tuple(node.path)
                index = self.search.select_path_list.index(node_path) + 1
                obj = self.data[index]
        else:
            obj = self.data

        """ when a left join in not there none is returned"""
        if obj is None:
            return

        if field in obj._table.columns.keys() + ["id"]:
            return util.convert_value(getattr(obj, field))

        if field in obj._table.relation_attributes:
            return getattr(obj, field)

