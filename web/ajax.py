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


import urllib2
import time
import copy
from random import shuffle
import pprint

import simplejson as json
import sqlalchemy as sa


class Sample(object):

    """ A sample from the application database.
    a sample of data for the table and field specified.
    if auto_refresh then new data will be gathered when the current
    sample has been exhausted, otherwise the existing sample is
    shuffled and reused. """

    def __init__(self, table, field, application, size = 100, auto_refresh = False):
        self.table = table
        self.field = field
        self.application = application
        self.size = size
        self.auto_refresh = auto_refresh

        self.sample_set = None
        self.sample_save = None

        self.get_sample()

    def get_sample(self):
        """ Gather a fresh sample from the database if needed
        or reuse the existing sample."""
        if not self.auto_refresh and self.sample_save:
            self.sample_set = copy.copy(self.sample_save)
            shuffle(self.sample_set)
        else:
            session = self.application.database.Session()
            obj = self.application.database.get_class(self.table)
            field = getattr(obj, self.field)
            result = session.query(field).order_by(sa.func.random()).limit(self.size).all()
            self.sample_set = [x[0] for x in result]
            session.close()

            if not self.auto_refresh:
                self.sample_save = copy.copy(self.sample_set)

    def __call__(self):
        """ Return the next sample"""
        if not self.sample_set:
            self.get_sample()
        return self.sample_set.pop()


class GeneratorResult(object):

    """ A generator result behaving like a list / dict hybrid.
    can be access via item[key], item[index] or item.get(key)"""

    def __init__(self, data_dict, data_list):
        self.data_dict = data_dict
        self.data_list = data_list

    def __getitem__(self, key):
        if type(key) == int:
            return self.data_list[key]
        return self.data_dict[key]

    def get(self, key):
        return self.data_dict.get(key)

    def __repr__(self):
        return '<GeneratorResult>\n%s\n%s' % (self.data_dict, self.data_list)


class Generator(object):

    """ A Generator that uses the data creator.
    if auto_refresh then new data will be gathered when the current
    sample has been exhausted, otherwise the existing sample is
    shuffled and reused. """

    def __init__(self, data_generator, generators, kw = [], size = 100, auto_refresh = False):
        self.data_generator = data_generator
        self.size = size
        self.auto_refresh = auto_refresh
        # make sure generators and keywords are lists
        if type(generators) == str:
            generators = [generators]
        if type(kw) == dict:
            kw = [kw]
        # build the generators
        self.num_generators = len(generators)
        self.generators = []
        for i in range(len(generators)):
            generator = generators[i]
            if len(kw) > i:
                gen_kw = kw[i]
            else:
                gen_kw = {}
            self.generators.append((generator, self.data_generator.generators[generator], gen_kw))

        self.sample_set = None
        self.sample_save = None

        self.get_sample()

    def get_sample(self):
        """ Gather a fresh sample from the data creator if needed
        or reuse the existing sample."""
        if not self.auto_refresh and self.sample_save:
            self.sample_set = copy.copy(self.sample_save)
            shuffle(self.sample_set)
        else:
            self.sample_set = []
            for i in xrange(self.size):
                data_dict = {}
                data_list = []
                # set generator for new record
                self.data_generator.new_record()
                for name, generator, kw in self.generators:
                    gen = generator(**kw)
                    data_dict[name] = gen
                    data_list.append(gen)
                # if only one generator just keep the data
                # else store in a GeneratorResult
                if self.num_generators == 1:
                    self.sample_set.append(data_dict[name])
                else:
                    self.sample_set.append(GeneratorResult(data_dict, data_list))

            if not self.auto_refresh:
                self.sample_save = copy.copy(self.sample_set)

    def __call__(self):
        """ Return the next sample"""
        if not self.sample_set:
            self.get_sample()

        return self.sample_set.pop()


class Worker(object):

    """ The Worker makes requests to the web application.  It can
    run the web application itself which is needed for performance testing
    or use an actual running instance.' """

    def __init__(self, **kw):

        self.host = kw.get('host', '127.0.0.1')
        self.port = kw.get('port', '8000')

        self.application_name = kw.get('application')

        self.username = kw.get('username')
        self.password = kw.get('password')

        self.profile = kw.get('profile', False)
        self.process = kw.get('process', False)
        self.quiet = kw.get('quiet', False)
        self.verbose = kw.get('verbose', False)

        self.fake_server = kw.get('fake_server', False)

        self._test_function = None
        self._setup_function = None

        self.application = None
        self.data_generator = None

        if self.fake_server:
            # use internal fake webserver
            import web
            from fake_webob import FakeSession
            self.init_application()
            self.server = web.WebApplication(self.application)
            self.server.fake_requests()
            # fake environ
            self.environ = {}
            self.environ['PATH_INFO'] = '/ajax'
            self.environ['params'] = {}
            self.environ['beaker.session'] = FakeSession()
        else:
            # use real webserver
            # cookie handler
            cookie_proc = urllib2.HTTPCookieProcessor()
            self.opener = urllib2.build_opener(cookie_proc)
            self.url = 'http://%s:%s/ajax' % (self.host, self.port)

        # log in if we have user details
        if self.username and self.password:
            self.login(self.username, self.password)

    def init_application(self):
        """ Initialise the application if needed. """
        if self.application:
            return
        if self.application_name:
            import application
            self.application = application.Application(self.application_name)
        else:
            raise Exception('No Application Name')

    def get_data_generator(self):
        """ Returns a data generator. """
        if not self.data_generator:
            from database.data_creator import DataGenerator
            self.data_generator = DataGenerator()
            self.init_application()
            self.data_generator.initialise(self.application)
        return self.data_generator

    def start_response(*junk):
        """ Null function for fake webserver """
        pass

    def request(self, data):
        """ Make a request to the application. """
        if self.verbose:
            print '== Sent Data', '=' * 47
            pprint.pprint(data)
            print '-' * 60
        if self.fake_server:
            self.environ['params']['body'] = data
            return self.server(self.environ, self.start_response)
        else:
            return self.opener.open(self.url, 'body=%s' % data).read()

    def get_form_data(self, form_name):
        """ Get the data for the named form. """
        form_data = self.decode.get('form').get(form_name)
        if form_data:
            return form_data.get('data')
        else:
            return {}

    def decode_response_part(self, data):
        """ Decode a part response and store form and node data. """
        if self.verbose:
            print '== Returned Data', '=' * 43
            pprint.pprint(data)
            print '-' * 60
#        data = data['data']
        action = data.get('action')
        if action == 'function':
            info = 'function: %s' % data['function']
        elif action == 'form' or action == 'dialog':
            info = 'form: %s' % data.get('title')
            self.decode['form'] = {}
            for form_name in data.get('data'):
                form_data = data.get('data').get(form_name).get('data')
                if '__array' in form_data:
                    form_data = form_data.get('__array')[0]
                version = data.get('data').get(form_name).get('form').get('version')
                self.decode['form'][form_name] = dict(version = version, data = form_data)
            self.decode['node_data'] = data.get('node_data')
        elif action == 'general_error':
            info = 'general_error:\n%s' % data.get('data')
        else:
            info = action
        if not self.quiet:
            print info

    def decode_response(self, response):
        """ Decode the response - data is stored in self.decode. """
        self.decode = {}
        data = json.loads(response)
        for row in data: 
            self.decode_response_part(row)

    def request_node(self, node_name, command = '', **kw):
        """ Make a node request to the web application. """
        req = dict(node = node_name, command = command)
        req.update(kw)
        data = json.dumps(req, separators=(',',':'))
        start = time.time()
        response = self.request(data)
        duration = '%sms' % int((time.time() - start) * 1000)
        if not self.quiet:
            print node_name, command, duration
            print '(%s bytes)' % len(response)
        if self.process:
            self.decode_response(response)

    def login(self, username, password):
        """ log in to the system """
        data = dict(login_name = username, password = password)
        form_data = [dict(form = 'login_form', data = data)]
        self.request_node("user.User", "login", form_data = form_data)

    def logout(self):
        """ log in to the system """
        self.request_node("user.User", "logout")

    def setup_function(self, function):
        """ Set the test function. """
        self._setup_function = function

    def test_function(self, function, count = 10):
        """ Set the test function. """
        self._test_function = function
        self.count = count

    def run(self):
        """ Run the test function. """
        if not self._test_function:
            print "No test function supplied"
            return
        cumlative_time = 0.0
        for i in xrange(self.count):
            start = time.time()
            self._test_function(self, self.test_environ)
            duration = time.time() - start
            cumlative_time += duration
            print '--- run %s --- %sms' % (i, int(duration * 1000))
        print 'total time %ss' % cumlative_time
        print 'average %sms' % int(cumlative_time / self.count * 1000)


    def start(self):
        """ Start the test. """
        self.test_environ = {}
        if self._setup_function:
            self._setup_function(self, self.test_environ)

        if self.profile:
            import cProfile
            cProfile.run('a.run()', 'ajax.profile')
        else:
            self.run()




##    =======
##    EXAMPLE
##    =======
##
##    def setup(worker, environ):
##        # This will be run once before the test is started.
##        # Use it to set up any generators etc.
##        # environ is a dict and will be passed to the test function.
##        generator = worker.get_data_generator()
##        application = worker.application
##
##        # Sample - get data for a field in a table.
##        environ['people'] = Sample('people', 'id', application)
##
##        # Generator - get random generated data using the data generator.
##        # simple example of single generator.
##        environ['simple_name'] = Generator(generator, 'full_name')
##        # with parameters.
##        environ['simple_int'] = Generator(generator, 'Integer', dict(min=1, max = 5))
##
##        # complex generator with multiple generators as list.
##        environ['person'] = Generator(generator,
##                                     ['full_name', 'Email', 'postcode', 'road', 'town'])
##        # with parameters as list.
##        environ['numbers'] = Generator(generator,
##                                    ['Integer', 'Integer'],
##                                    [dict(min = 1, max = 5), dict(min = 100, max = 500)])
##
##
##    def test(worker, environ):
##        # This will be called for each test cycle.
##
##        # Sample - will return the id of a person.
##        print environ['people']()
##
##        # Generators.
##        # simple - will return the item.
##        print environ['simple_name']()
##        print environ['simple_int']()
##
##        # complex - returns a GeneratorResult.
##        person = environ['person']()
##        print person['full_name']
##        print person.get('full_name')
##        print person[0]
##
##        # Request simple node.
##        worker.request_node("test.Node1")
##
##        # Node with node data.
##        worker.request_node("test.People", "edit", node_data = dict(id = 1))
##
##        # Having requested an edit form we can change some data and save.
##        # Get the latest node data.
##        node_data = worker.decode.get('node_data')
##        # Get the form data for form main.
##        data = worker.get_form_data('main')
##
##        # Update the data using the generator.
##        gen_data = environ['person']()
##        data['name'] = gen_data.get('full_name')
##        data['email'] = gen_data.get('Email')
##        data['street'] = gen_data.get('road')
##        data['town'] = gen_data.get('town')
##        data['postcode'] = gen_data.get('postcode')
##
##        # Set the form data.
##        form_data = [dict(form = 'main', data = data)]
##        # Make the request
##        worker.request_node("test.People",
##                            "_save",
##                            node_data = node_data,
##                            form_data = form_data)
##
##
##    # Create a worker
##    worker = Worker(application = 'testing',
##                    username = 'admin',
##                    password = 'admin',
##                    verbose = False,
##                    fake_server = True,
##                    profile = True,
##                    process = True,
##                    quiet = False)
##    # Add setup function.
##    worker.setup_function(setup)
##    # Add test function.
##    worker.test_function(test, count = 10)
##    # Start the test.
##    worker.start()
