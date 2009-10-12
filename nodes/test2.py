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

from node import Node
from .reformed import reformed as r
from .reformed import util

class ResultSet(Node):

    def call(self):

        search_table = "donkey"

        results = r.search(search_table)

        out = []

        for result in results:
            row = {"table": result["__table"],
                   "id": result["_core_entity.id"],
                   "title": "donkey %s" % result["_core_entity.id"]}
            out.append(row)

        self.out = out



