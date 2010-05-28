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

import logging
import random
import hashlib
import base64

from reformed.custom_exceptions import SingleResultError
from global_session import global_session


log = logging.getLogger('rebase.authentication')

def loggin(data, auto = False):
    """Set user http session details
    data: sa user object"""

    user_id = data.get('id')
    username = data.get('login_name')
    global_session.session['user_id'] = user_id
    global_session.session['username'] = username
    global_session.session['permissions'] = get_permissions(user_id)
    global_session.session.persist()

    if auto:
        log.info('Login %s (%s)' % (user_id, username))
    else:
        log.info('Login %s (%s) automatic' % (user_id, username))


def get_permissions(user_id):
    """return an array of permissions for the user_id provided"""

    r = global_session.database
    result = r.search('permission', 'user_group_user.user_id = %s' % user_id, fields=['permission']).data
    permissions = ['LoggedIn']
    for row in result:
        permissions.append(row.get('permission'))
    return permissions


def clear_user_session():
    """clear authorisation data from the http session"""

    if 'user_id' in global_session.session:
        log.info('Log out %s (%s)' % (global_session.session['user_id'],
                                      global_session.session['username']))

    global_session.session['user_id'] = 0
    global_session.session['username'] = ''
    global_session.session['permissions'] = []
    global_session.session.persist()


def auto_loggin(auto_cookie):
    """attempt an auto login using the info in the auto_cookie string
    format <user_id>:<token>
    returns True if successful"""

    try:
        (user_id, token) = auto_cookie.split(':',1)
    except ValueError:
        return False
    r = global_session.database
    where = "id = %s and auto_loggin= '%s'" % (user_id, token)
    try:
        data = r.search_single_data('user', where)
    except SingleResultError:
        # not allowed
        return False
    loggin(data, auto = True)

    return True


def create_auto_loggin_id():
    """generate hard to guess random string for auto loggin"""

    random_string = ''
    for i in range(1024):
        random_string += chr(random.randint(0, 255))

    h = hashlib.new('sha512')
    h.update(random_string)
    digest = h.digest()
    return base64.encodestring(digest).replace('\n','')
    

