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
##	boot_tables.py
##	======
##	
##	This file contains the system tables that contain the metadate for
##  a Reformed database

from tables import Table
import fields


class boot_tables(object):

    def __init__(self):

        self.boot_tables = [Table("__table", fields.Text("table_name"),
                                fields.OneToMany("table_params","__table_params"),
                                fields.OneToMany("field","__field"),
                                primary_key = "table_name"
                               ),
                   Table("__table_params", fields.Text("item"),
                                fields.Text("value")),
                   Table("__field", fields.Text("name"),
                                fields.Text("type"),
                                fields.Text("other"))
                  ]
