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
##   Copyright (c) 2008-2010 Toby Dacre & David Raznick
##  


from reformed.database import table
from reformed.fields import *

from global_session import global_session

r = global_session.database

def sysinfo(name, value, description = ''):
    r.register_info(name, value, description)


permissions_defined = None

def permission(code, name, description = u''):
    data = dict(description = name,
                long_description = description)
    add_data("permission", "permission", code, data)


cached_data = {}

def add_data(table, key_field, key_data, data):
    """check code_type exists in the database, add it if not there"""
    global cached_data

    # cache data if we don't have it already
    if table not in cached_data:
        cached_data[table] = []
        values = r.search(table, fields = [key_field]).data
        for record in values:
            cached_data[table].append(record[key_field])

    # add data if not in database
    if key_data not in cached_data[table]:
        new_row = r.get_instance(table)
        setattr(new_row, key_field, key_data)

        for key, value in data.iteritems():
            setattr(new_row, key, value)

        session = r.Session()
        session.add(new_row)
        session.commit()
        session.close()

        cached_data[table].append(key_data)
