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

from global_session import global_session
import logging
import pprint
import glob
import os.path
import inspect
from ZODB.PersistentMapping import PersistentMapping
import transaction

log = logging.getLogger('rebase.node')

class NodeNotFound(Exception):
    pass

class NodeToken(object):

    """This holds state information for the current transaction"""


    class FormToken(object):

        """Helper class to hold data for each form and add some functionality"""

        def __init__(self, data, simple = True):
            """simple: True if shared data for all forms,
            False if separate data for each form"""
            if simple:
                self.data = data
                self.form = None
            else:
                self.data = data['data']
                self.form = data['form']

        def get(self, name, default = None):
            """get method"""
            return self.data.get(name, default)

        def get_data_int(self, key, default = 0):
            """ Get integer value out of self.data[key] or default """
            try:
                value = int(self.data.get(key, default))
            except ValueError:
                value = default
            return value


    def __init__(self, data):

        self.last_node = None
        self.first_call = False
        # The command type will be set to 'layout' or 'node' in process_data()
        self.command_type = None

        self.command = data.pop('command', None)
        self.data = data.pop('data', None)

        # self.node will be set each time a new node is called with this token
        # it is currently set in NodeRunner.run()
        self.node = None
        self.node_name = None


        # when data is sent in multiple form mode (this should be the default)
        # we want to split it for each form to make processing easier.
        self.data_split = {}
        self.process_data()


        # form cache is used to cache forms when possible
        # it is a hash of the name and client version of all client
        # side cached forms.
        self.form_cache = data.pop('form_cache', None)

        # the browser can request application data via this method
        # this is usually requested at start-up
        self.request_application_data = data.pop('request_application_data', False)

        self.output = None
        # output stuff
        self.out = {}

        # the layout_type sets the section layout
        # the form_layout will be an array
        # that has the grouping and ordering of the forms
        # for each section
        # eg. [ ['form1', 'form2'], ['form3'] ]
        self.layout_type = None
        # the form_layout sets the layout
        # eg. 'entity', 'listing'
        self.form_layout = None
        # this is the list of forms provided to the frontend
        # it may be redundant
        self.layout_forms = []

        # title sets the title of the page
        self.title = None
        self.link = None

        self.action = None
        self.bookmark = None
        self.user = None
        self.next_node = None
        self.next_data = None
        self.next_data_out = None
        self.auto_login_cookie = None

    def __getitem__(self, form_name):
        """A shortcut method to get the sent data associated with the named form.
        If it is a 'layout' level command then there will be individual data for each form,
        else there is common data for a 'node' level command"""
        if self.command_type == 'layout':
            try:
                return self.data_split[form_name]
            except:
                raise Exception('Node Token tried to access none existant sent data for form `%s`' % form_name)
        elif self.command_type == 'node':
            return self.data_split

    def process_data(self):
        """Process the data to make it easier to work with and
        determine if we are running a 'node' or 'layout' level command."""
        # If the data is a list (multiple forms)
        # then we need to split it into parts
        # as it is a 'layout' level command
        # If not then it is a 'node' level command
        # and we want only have a single source of data
        if type(self.data).__name__ == 'list':
            self.command_type = 'layout'
            self.split_data()
        else:
            self.command_type = 'node'
            self.data_split = self.FormToken(self.data)

    def split_data(self):
        """We get an array of data for each form,
        split this out into a hash to make it easier to access"""
        for row in self.data:
            self.data_split[row['form']] = self.FormToken(row, simple = False)

    def get_data_int(self, key, default = 0):
        """ Get integer value out of self.data[key] or default """
        # FIXME I don't like this here but we'll see TD
        try:
            value = int(self.data.get(key, default))
        except ValueError:
            value = default
        return value

    def output_form_data(self, form_name, output):
        """Helper function to add form data to the node token for a form"""

        # paranoia check TODO should this be an assertion?
        if form_name in self.layout_forms:
            raise Exception("Attempt to overwrite form data in node token")

        self.layout_forms.append(form_name)
        self.out[form_name] = output


    def set_form_message(self, message):
        """Sets the button info to be displayed by a form."""
        self.out['data']['__message'] = message

    def set_form_buttons(self, button_list):
        """Sets the button info to be displayed by a form."""
        if not self.out.get('data'):
            self.out["data"] = {}

        self.out['data']['__buttons'] = button_list

    def get_layout(self):
        """ Returns the layout hash to be sent to the front end. """

        if not self.layout_type and self.layout_forms and self.command_type == 'node':
            # No layout has been specified but one is needed
            # because this was a 'node' level command.
            self.layout_type = 'listing'
            self.form_layout = [self.layout_forms]

        layout = dict(layout_type = self.layout_type,
                      form_layout = self.form_layout,
                      layout_forms = self.layout_forms)
        return layout


        
class NodeManager(object):

    """NodeManager imports and stores nodes form
    <app_root>/<app>/custom_nodes and <app_root>/nodes.
    If a node with the same name has already been imported any new node
    with the same name will be ignored.

    New node modules have their initialise() called but only once"""

    def __init__(self, application):
        self.application = application
        self.nodes = {}
        self.node_instances = {}
        self.modules = {}
        self.processed_nodes = {}
        self.get_nodes()


    def get_node_instance(self, node_name):
        if node_name in self.node_instances:
            return self.node_instances[node_name]
        else:
            try:
                node_class = self.nodes[node_name]
            except KeyError:
                raise NodeNotFound(node_name)
            instance = node_class(node_name)
            if not instance.volatile and instance.static:
                self.node_instances[node_name] = instance
        return instance

    def get_nodes(self):
        # get details of previously known nodes
        zodb = self.application.aquire_zodb()

        connection = zodb.open()
        root = connection.root()
        if "nodes" not in root:
            root["nodes"] = PersistentMapping()
            transaction.commit()
        else:
            # get cached info
            for key, value in root["nodes"].iteritems():
                self.processed_nodes[key] = value
        self.import_nodes()

        zodb.close()

    def import_node(self, name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    def import_nodes(self):

        log.info('IMPORTING NODES')
        # custom nodes
        directory = os.path.join(self.application.application_folder, 'custom_nodes')
        self.import_node_directory(directory, 'custom_nodes')
        # standard nodes
        directory = os.path.join(self.application.root_folder, 'nodes')
        self.import_node_directory(directory, 'nodes')
        log.info('FINISHED')

    def import_node_directory(self, directory, node_root):
        """Find all *.py files in directory.
        Import if no module of this name is currently imported.
        Find and store all classes and call initialise if needed"""

        log.info('directory %s' % directory)
        module_dir = os.path.join(directory, '*.py')
        files = glob.glob(module_dir)
        for file in files:
            (head, tail) = os.path.split(file)
            (root, ext) = os.path.splitext(tail)
            if root == '__init__':
                # skip __init__.py
                continue
            if root in self.modules:
                log.info('Module `%s` already imported, ignoring' % root)
                continue
            try:
                # import node
                module = self.import_node('%s.%s' % (node_root, root))
                self.modules[root] = (module, node_root, root)
            except ImportError:
                log.critical('cannot import %s' % file)
                raise


    def process_nodes(self):
        for module, node_root, root in self.modules.itervalues():
            for name in dir(module):
                item = getattr(module, name)
                if inspect.isclass(item):
                    if item.__module__ == node_root + '.' + root:
                        node_title = '%s.%s' % (root, name)
                        self.nodes[node_title] = item


    def initialise_nodes(self):
        for module, node_root, root in self.modules.itervalues():

            if root not in self.processed_nodes:
                # new node, call initialize() if needed
                if 'initialise' in dir(module) and inspect.isfunction(module.initialise):
                    log.info('initialising')
                    module.initialise()
                # store node processed in zodb
                self.store_node(root)

    def store_node(self, root):

        zodb = self.application.aquire_zodb()

        connection = zodb.open()
        zodb_root = connection.root()
        zodb_root["nodes"][root] = True
        transaction.commit()
        connection.close()

        zodb.close()
        self.application.get_zodb(True)




class NodeRunner(object):

    def __init__(self, node_manager):
        self.node_manager = node_manager
        self.command_queue = []
        self.output = [] # this will be returned
        self.auto_login_cookie = None
        
    def add_command(self, data):
        self.command_queue.append(data)

    def process(self):
        while self.command_queue:
            data = self.command_queue.pop()
            self.node(data)

    def node(self, data):

        # create our node token to hold state
        node_token = NodeToken(data)

        node = data.get('node')
        self.run(node, node_token)
        self.output.append({'type' : 'node',
                              'data' : node_token.output})
        # auto login cookie info
        if node_token.auto_login_cookie:
            self.auto_login_cookie = node_token.auto_login_cookie


    def run(self, node_name, node_token, last_node = None):
        log.info('running node: %s, user id: %s' % (node_name, global_session.session['user_id']))
        log.debug('sent data: \n%s' %  pprint.pformat(node_token.data))

        sys_info = global_session.sys_info
        # check if application is private
        if not sys_info.get('public') and not global_session.session['user_id']:
            node_name = sys_info.get('default_node', node_name)
            node_token.data['command'] = sys_info.get('default_command')
            log.info('User not logged in.  Switching to node %s, command %s' % (node_name, node_token.data['command']))

        # get node from node_manager
        # this should really get an existing node
        # node_class = self.node_manager[node_name]
        node = self.node_manager.get_node_instance(node_name)
        # pass the current node to the node token
        node_token.node = node
        node_token.node_name = node.name

        # the user cannot perform this action
        if not node.check_permissions():
            log.warn('forbidden node or command')
            # FIXME this should be appended
            node_token.output = {'action': 'forbidden'}
            return

        node.initialise(node_token)
        node.call(node_token)
        node.finalise(node_token)
        node.finish_node_processing(node_token)



## todo        if node.prev_node and node.prev_node.next_data_out:
## todo            node.out["data"].update(node.prev_node.next_data_out)
## todo
        if node_token.next_node:
            log.info('redirect to next node %s' % node_token.next_node)
            node_token.data = node_token.next_data['data']
            node_token.command = node_token.next_data['command']
            next_node = node_token.next_node
            node_token.next_node = None
            node_token.next_data = None
            # clear the form cache so we don't get confussed
            self.form_cache = None
            print node_token.next_node, node_token, node_name
            return self.run(next_node, node_token, node_name)
        else:
            refresh_frontend = False



        info = {'action': node_token.action,
                'node': node_name,
                'title' : node_token.title,
                'link' : node_token.link,
                'user' : node_token.user,
                'bookmark' : node_token.bookmark,
                'layout' : node_token.get_layout(),
                'data' : node_token.out}

        user_id = global_session.session['user_id']
        # application data
        if node_token.request_application_data:
            info['application_data'] = sys_info
            info['application_data']['__user_id'] = user_id
            info['application_data']['__username'] = global_session.session['username']
            refresh_frontend = True
        # bookmarks
        if (info['user'] or refresh_frontend) and user_id:
            # we have logged in so we want our bookmarks
            info['bookmark'] = self.bookmark_list(user_id)
        log.debug('returned data\n%s\n----- end of node processing -----' % pprint.pformat(info))

        ## FIXME botch
        node_token.output = info


    def bookmark_list(self, user_id, limit = 100):

        r = global_session.database
        bookmarks = r.search("bookmarks",
                                      "user_id = ?",
                                      fields = ['title', 'entity_table', 'entity_id', 'accessed_date'],
                                      values = [user_id],
                                      order_by = "accessed_date",
                                      keep_all = False,
                                      limit = limit).data
        return bookmarks
