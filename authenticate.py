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

import reformed.fshp
from reformed.custom_exceptions import SingleResultError
from global_session import global_session


log = logging.getLogger('rebase.authentication')

def login(data, auto = False):
    """Set user http session details
    data: sa user object"""

    user_id = data.get('id')
    username = data.get('login_name')
    global_session.session['user_id'] = user_id
    global_session.session['username'] = username
    global_session.session['permissions'] = get_permissions(user_id)
    # Reset session at front-end
    global_session.session['reset'] = True
    global_session.session.persist()

    if auto:
        log.info('Login %s (%s)' % (user_id, username))
    else:
        log.info('Login %s (%s) automatic' % (user_id, username))

def forbidden(node_token):
    if global_session.session['user_id']:
        # user logged in but not enough permissions
        node_token.forbidden()
    else:
        # user not logged in so show login form
        data = dict(message = 'you need to login to see this page')
        node_token.next_node('user.User', command = 'login', node_data = data);


def get_permissions(user_id):
    """return a set of permissions for the user_id provided"""

    r = global_session.database
    result = r.search('permission', 'user_group_user.user_id = ?', values = [user_id], fields=['permission']).data
    permissions = ['LoggedIn']
    for row in result:
        permissions.append(row.get('permission'))
    return set(permissions)


def clear_user_session():
    """clear authorisation data from the http session"""

    if 'user_id' in global_session.session:
        log.info('Log out %s (%s)' % (global_session.session['user_id'],
                                      global_session.session['username']))

    global_session.session['user_id'] = 0
    global_session.session['username'] = ''
    global_session.session['permissions'] = set()
    # Reset session at front-end
    global_session.session['reset'] = True
    global_session.session.persist()

def check_login(login_name, password):
    message = None
    data = None
    fail_message = '# Login failed\n\nuser name or password incorrect, try again.'

    r = global_session.database
    if login_name and password:
        where = "login_name = ?"
        try:
            data_out = r.search_single_data('user', where, values = [login_name])
            if not data_out.get("password") or not reformed.fshp.check(password, data_out.get("password")):
                # password incorrect
                message = fail_message
                log.info('Login Fail for `%s` incorrect password' % login_name)
            else:
                if data_out.get('active') != True:
                    # account disabled
                    message = '# Login failed\n\nThis account is disabled.'
                    log.info('Login Fail for `%s` account disabled' % login_name)
                else:
                    where = 'user_group_user.user_id = ? and (permission = ? or permission = ?)'
                    result = r.search('permission', where, values = [data_out.get('id'), 'LogIn', 'SysAdmin']).data
                    if result:
                        # login successful
                        login(data_out)
                        data = data_out
                    else:
                        # no login permissions for this user
                        message = '# Login failed\n\nThis account does not have permission to log in to the system.'
                        log.info('Login Fail for `%s` does not have permission' % login_name)
        except SingleResultError:
            # no such user
            message = fail_message
            log.info('Unknown user `%s`' % login_name)

    return (message, data)

def auto_login(auto_cookie):
    """attempt an auto login using the info in the auto_cookie string
    format <user_id>:<token>
    returns True if successful"""

    try:
        (user_id, token) = auto_cookie.split(':',1)
    except ValueError:
        return False
    r = global_session.database
    where = "id = ? and auto_login = ?"
    try:
        data = r.search_single_data('user', where, values = [user_id, token])
    except SingleResultError:
        # not allowed
        return False
    login(data, auto = True)

    return True

def check_permission(permissions):
    """check if a user has the required permission to perform an action"""
    # no permission so allowed
    if not permissions:
        return True

    user_perms = global_session.session.get('permissions')

    # SysAdmin permission give automatic access
    if 'SysAdmin' in user_perms:
        return True

    # general case does the user have one of the required permissions
    if len(set(permissions).intersection(user_perms)):
        return True

    # action not allowed
    return False

def create_auto_login_id():
    """generate hard to guess random string for auto log in"""

    random_string = ''
    for i in range(1024):
        random_string += chr(random.randint(0, 255))

    h = hashlib.new('sha512')
    h.update(random_string)
    digest = h.digest()
    return base64.encodestring(digest).replace('\n','')
    

