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
    """check permission exists in the database, add it if not there"""
    global permissions_defined
    # cache permissions list if we don't have it already
    if permissions_defined == None:
        permissions_defined = []
        permissions = r.search('permission', fields = ['permission']).data
        for record in permissions:
            permissions_defined.append(record['permission'])

    # add permission if not in database
    if code not in permissions_defined:
        print 'add permision: %s' % code
        new_permission = r.get_instance('permission')
        new_permission.permission = code
        new_permission.description = name
        new_permission.long_description = description
        session = r.Session()
        session.add(new_permission)
        session.commit()
        session.close()
