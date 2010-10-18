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


class FakeSession(object):
    """ Fake version of beaker.Session used for performance testing. """
    
    def __init__(self):
        self.data = {}

    def __contains__(self, key):
        return key in self.data

    def __setitem__(self, key, item):
        self.data[key] = item

    def __getitem__(self, key):
        return self.data.get(key)

    def get(self, key):
        return self.data.get(key)

    def persist(self):
        pass


class Request(object):
    """ Fake version of webob.Request used for performance testing. """

    def __init__(self, environ):
        self.environ = environ

    def __getattr__(self, key):
        if key == 'params':
            return self.environ['params']
        elif key == 'cookies':
            return {}
        return 'FAKE'


class Response(object):
    """ Fake version of webob.Response used for performance testing. """
    
    response = {}
    headers = {'Set-Cookie' : None}

    def __init__(self, environ):
        self.environ = environ

    def __setattr__(self, key, value):
        self.response[key] = value

    def __call__(self, environ, start_request):
        return self.response['body']

    def delete_cookie(*args):
        pass
