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
import logging
import pprint
import glob
import os.path
import inspect
import urllib
from operator import itemgetter

from ZODB.PersistentMapping import PersistentMapping
import transaction

import authenticate
from web.global_session import global_session

log = logging.getLogger('rebase.node')

class NodeNotFound(Exception):
    pass

class NodeToken(object):

    """This holds state information for the current transaction"""


    class FormToken(object):

        """Helper class to hold data for each form and add some functionality"""

        def __init__(self, data, simple = True, node_data = {}):
            """simple: True if shared data for all forms,
            False if separate data for each form"""
            self.node_data = node_data
            if simple:
                self.data = data
                self.form = None
            else:
                self.data = data['data']
                self.form = data['form']

        def get(self, key, default = None):
            """ Get method
            Will try to get from form the form data first
            then will look in node data and finally return the default."""
            if key in self.data:
                return self.data.get(key)
            elif key in self.node_data:
                return self.node_data.get(key)
            else:
                return default

        def pop(self, key, default = None):
            """ Get method
            Will try to get from form the form data first
            then will look in node data and finally return the default."""
            if key in self.data:
                return self.data.pop(key)
            elif key in self.node_data:
                return self.node_data.pop(key)
            else:
                return default

        def get_data_int(self, key, default = 0):
            """ Get integer value out of self.data[key] or node data or default. """
            try:
                value = int(self.get(key, default))
            except ValueError:
                value = default
            return value

        def url_encode(self):
            return urllib.urlencode(self.data)


    def __init__(self, data, application):

        self.application = application
        self.reset()

        self.command = data.pop('command', None)
        self.form_cache = data.pop('form_cache', None)
        # the browser can request application data via this method
        # this is usually requested at start-up
        self.request_application_data = data.pop('request_application_data', False)
        self._data = data
        self.process_data()
        self.auto_login_cookie = None
        self._added_responses = []


    def reset(self):
        """ Clear all NodeToken data. """

        self.last_node = None
        self.first_call = False
        # The command type will be set to 'layout' or 'node' in process_data()
        self.command_type = None
        self._data = {}


        # self.node will be set each time a new node is called with this token
        # it is currently set in NodeRunner.run()
        self.node = None
        self.node_name = None

        # when data is sent in multiple form mode (this should be the default)
        # we want to split it for each form to make processing easier.
        self._form_data = {}
        self._node_data = None
        self._flags = {}
        self.form_token_list = []

        # form cache is used to cache forms when possible
        # it is a hash of the name and client version of all client
        # side cached forms.
        self.form_cache = None

        # output stuff
        self._out = {}

        # self._layout holds layout information if needed
        # keys are
        # 'layout_type' sets the section layout
        # 'form_layout' will be an array
        # that has the grouping and ordering of the forms
        # for each section
        # eg. [ ['form1', 'form2'], ['form3'] ]
        # 'form_layout' sets the layout
        # eg. 'entity', 'listing'
        # 'form_layout'
        # this is the list of forms provided to the frontend
        # it may be redundant
        # 'layout_forms'
        # any returned form that should be shown as a dialog.
        # 'layout_dialog' any form to use as a dialog.
        self._layout = {}

        # title sets the title of the page
        self._title = None
        self._layout_title = None

        self._action = None
        self._function = None
        self._output_node_data = {}
        self.bookmark = None
        self.user = None

        self._next_node = None
        self._next_data = None
        self._next_command = None

        self._clear_node_data = False
        self.next_data_out = None # TODO do we still need this? what is it doing/

    def __getitem__(self, form_name):
        """A shortcut method to get the sent data associated with the named form.
        If it is a 'layout' level command then there will be individual data for each form.
        If there is no data for the form then the node data will be returned.
        For a 'node' level command node data is returned."""
        if self.command_type == 'layout':
            try:
                # form data
                return self._form_data[form_name]
            except KeyError:
                # node data
                return self._node_data
        elif self.command_type == 'node':
            return self._node_data

    def debug_info(self):
        """Debug information."""
        return  self._data


    def process_data(self):
        """Process the data to make it easier to work with and
        determine if we are running a 'node' or 'layout' level command."""
        # If the data is a list (multiple forms)
        # then we need to split it into parts
        # as it is a 'layout' level command
        # If not then it is a 'node' level command
        # and we want only have a single source of data

        self._flags = self._data.get('flags', {})
        form_data = self._data.get('form_data', [])
        node_data = self._data.get('node_data', {})

        if form_data:
            self.command_type = 'layout'
        else:
            self.command_type = 'node'

        # Build the node data
        self._node_data  = self.FormToken(node_data)

        # Build any form data.
        # We get an array of data for each form,
        # split this out into a hash to make it easier to access
        for row in form_data:
            form_token = self.FormToken(row, simple = False, node_data = node_data)
            self._form_data[row['form']] = form_token
            # Build list of form names too.
            self.form_token_list.append(row['form'])


    def form_tokens(self):
        """returns the form tokens if we have more than one"""
        return self.form_token_list

    def get_node_data(self):
        """returns the FormToken if there is a node level data"""
        return self._node_data

    def set_node_data(self, node_data):
        if self._output_node_data:
            raise Exception('node data set multiple times')

        self._clear_node_data = True
        self._output_node_data = node_data


    def output_form_data(self, form_name, output):
        """Helper function to add form data to the node token for a form"""
        # paranoia check TODO should this be an assertion?
        if form_name in self._out:
            raise Exception("Attempt to overwrite form data in node token")
        if not 'dialog' in self._flags:
            if 'layout_forms' not in self._layout:
                self._layout['layout_forms'] = []
            self._layout['layout_forms'].append(form_name)
        self._out[form_name] = output

    def set_form_message(self, message):
        """Sets the button info to be displayed by a form."""
        self._out['data']['__message'] = message

    def set_form_buttons(self, button_list):
        """Sets the button info to be displayed by a form."""
        if not self._out.get('data'):
            self._out["data"] = {}
        self._out['data']['__buttons'] = button_list

    def set_layout(self, layout_type, form_layout):
        """ Helper function to set layout. """
        if 'layout_type' in self._layout:
            raise Exception('NodeToken layout type already set')
        self._layout['layout_type'] = layout_type
        self._layout['form_layout'] = form_layout
        self._clear_node_data = True

    def _get_layout(self):
        """ Returns the layout hash to be sent to the front end. """
        if not self._layout.get('layout_type') and self._layout.get('layout_forms') and self.command_type == 'node':
            # No layout has been specified but one is needed
            # because this was a 'node' level command.
            self._layout['layout_type'] = 'listing'
            self._layout['form_layout'] = [self._layout['layout_forms']]
            self._clear_node_data = True

        return self._layout


    def next_node(self, node, node_data = None, command = None):
        """ Automatically pass control to a new node. """
        self._next_node = node
        self._next_data = node_data
        self._next_command = command
        self._set_action('next_node')

    def force_dialog(self):
        """ Force the next sent form to be viewed as a dialog. """
        self._flags['dialog'] = True

    def redirect(self, node_string, url_data = None, node_data = None):
        """ Helper function redirect via the front end. """
        # Append any url_data to the node if needed
        if url_data:
            link_data = urllib.urlencode(url_data)
            node_string += '?'
            node_string += link_data
        # if this is not a special command make it an update node
        self._set_action('redirect', data = node_string, node_data = node_data)

    def redirect_back(self):
        """ Helper function direct the front end to go back in the history. """
        self._set_action('redirect', data = 'BACK')

    def status(self, data):
        """ Helper function send status data to front end. """
        self._set_action('status', data = data)

    def function(self, function_name, data = None):
        """ Helper function send status data to front end. """
        self._set_action('function', function_name = function_name, data = data)

    def forbidden(self):
        """ Helper function send forbidden error to front end. """
        self._set_action('forbidden')

    def form(self, form, **kw):
        """ Helper function set action to form. """
        if self._flags.get('dialog'):
            if not 'layout_title' in kw or not kw['layout_title']:
                kw['layout_title'] = form.layout_title
            self._set_action('dialog', dialog = form.name, **kw)
        else:
            self._set_action('form', **kw)

    def general_error(self, error):
        """ Helper function send error to front end. """
        self._set_action('error', data = error)

    def message(self, message):
        """ Helper function send error to front end. """
        self._set_action('message', data = message)

    def _set_action(self, action, **kw):
        """ Set the action for the node token. """
        if self._action and not(action == self._action and action == 'form'):
            raise Exception('Action has already been set for this NodeToken')
        self._action = action
        title = kw.get('title')
        if title:
            self._title = title
        layout_title = kw.get('layout_title')
        if layout_title:
            self._layout['layout_title'] = layout_title
        function_name = kw.get('function_name')
        if function_name:
            self._function = function_name
        dialog = kw.get('dialog')
        if dialog:
            # TODO make sure we only allow one dialog.
            self._layout['layout_dialog'] = dialog
        data = kw.get('data')
        if data:
            self._out = data
        clear_node_data = kw.get('clear_node_data')
        if clear_node_data:
            self._clear_node_data = True
        node_data = kw.get('node_data')
        if node_data:
            self.set_node_data(node_data)

    def add_paging(self, form, count, limit, offset, base_link):
        """Add paging info to form data"""
        # check we have data for this form
        if form.name not in self._out:
            self._out[form.name] = {}
        paging_data = dict(row_count = count,
                           limit = limit,
                           offset = offset,
                           base_link = base_link)

        if form.form_type == 'results':
            self._layout['paging'] = paging_data
        else:
            self._out[form.name]['paging'] = paging_data

    def output(self):
        """Build the output data to be sent to the front end."""

        layout = self._get_layout()
        # By default we will return the same node data
        # unless it is updated elsewhere
        if not self._clear_node_data:
            self._output_node_data  = self._node_data.data

        info = {'action': self._action,
                'node': self.node_name,
                'title' : self._title,
                'function' : self._function,
                'bookmark' : self.bookmark,
                'layout' : layout,
                'node_data' : self._output_node_data,
                'data' : self._out}

        user_id = global_session.session['user_id']
        # application data
        if self.request_application_data:
            data = global_session.sys_info
            self.add_extra_response_function('application_data', data)
            refresh_frontend = True
        else:
            refresh_frontend = False
        # menu and bookmarks
        if (self.user or refresh_frontend):
            data = self._make_menu()
            self.add_extra_response_function('make_menu', data)
            if user_id:
                # we have logged in so we want our bookmarks
                data = self._bookmark_list(user_id)
                self.add_extra_response_function('load_bookmarks', data)
            # user data
            data = self._user_data(user_id)
            self.add_extra_response_function('update_user', data)


        if global_session.session['reset']:
            self.add_extra_response_function('clear_form_cache')
            global_session.session['reset'] = False
            global_session.session.persist()

        self._added_responses.append(info)
      #  log.debug('returned data\n%s\n----- end of node processing -----' %
      #            pprint.pformat(self._added_responses))
        return self._added_responses

    def add_extra_response_function(self, function, data = None):
        #self._added_responses.append(dict(type = 'node', data = dict(action = action, data = data)))
        response = dict(action = 'function', function = function, data = data)
        self._added_responses.append(response)

    def _user_data(self, user_id):
        data = dict(user_id = user_id,
                    user_name = global_session.session['username'])
        if global_session.session['real_username']:
            data['real_user_id'] = global_session.session['real_user_id']
            data['real_user_name'] = global_session.session['real_username']
        return data

    def _bookmark_list(self, user_id, limit = 100):

        r = global_session.database
        session = r.Session()
        bookmarks = r.search("bookmarks",
                             "user_id = ?",
                             fields = ['_core_entity.title', 'entity_table', '_core_id'],
                             values = [user_id],
                             order_by = "accessed_date",
                             keep_all = False,
                             session = session,
                             limit = limit).data
        return bookmarks

    def _make_menu(self):
        """Make the data for the users menu.
        Menu item permissions are checked and only allowed items are returned. """

        def build_items(items):
            # checks the permissions
            output = []
            # TODO we should just sort the menu when it's created.
            # sort by index, alpha
            for item in sorted(sorted(items, key = itemgetter('title')), key = itemgetter('index')):
                if not authenticate.check_permission(item.get('permissions')):
                    continue
                menu_item = {}
                if 'title' in item:
                    menu_item['title'] = item['title']
                if 'node' in item:
                    menu_item['node'] = item['node']
                if 'function' in item:
                    menu_item['function'] = item['function']
                if 'sub' in item:
                    sub_items = build_items(item['sub'])
                    if sub_items:
                        menu_item['sub'] = sub_items
                output.append(menu_item)
            return output

        return build_items(self.application.node_manager.menu)


    def get_title(self):
        return self._title

    def check_next_node(self):
        """ Is there a next node to visit. """
        return (self._action == 'next_node')


    def next_node_update(self):
        """ Set data for next node. """
        node_name = self.node_name
        next_node = self._next_node
        command = self._next_command
        data = self._next_data

        # clear the node token
        self.reset()

        self.command_type = 'node'
        self._node_data  = self.FormToken(data)
        self.command = command
        self.last_node = node_name
        return next_node


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
        # menu stuff
        self.menu = []
        self.menu_pending = {}
        self.menu_lookup = {}
        self.current_node = None

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
        directory = os.path.join(self.application.root_folder, 'default_nodes')
        self.import_node_directory(directory, 'default_nodes')
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
            # add any menu items for the module
            if hasattr(module, 'make_menu'):
                self.current_node = None
                make_menu = getattr(module, 'make_menu')
                make_menu(self)
            # find and store nodes
            for name in dir(module):
                item = getattr(module, name)
                if inspect.isclass(item):
                    if item.__module__ == node_root + '.' + root:
                        node_title = '%s.%s' % (root, name)
                        self.nodes[node_title] = item
                        # add any menu items for the node
                        if hasattr(item, 'make_menu'):
                            self.current_node = node_title
                            item().make_menu(self)
        # Check menu build completed
        if self.menu_pending:
            print 'Warning: Orphaned menu items wanting', self.menu_pending.keys()



    def add_menu(self, data):

        actioned = False
        if 'index' not in data:
            data['index'] = 5
        node = data.get('node')
        if node:
            # process the node data
            # we can use $ as shorthand for the current node.
            if self.current_node:
                node = node.replace('$', self.current_node)
            # make the item an update link or use supplied flags
            # and store updated node
            flags = data.get('flags')
            if flags:
                data['node'] = '%s@%s' % (flags, node)
            else:
                data['node'] = node
        if 'menu' in data:
            # adding this item to a sub menu.
            master_name = data['menu']
            if master_name in self.menu_lookup:
                # we have the menu master so add to it
                master = self.menu_lookup[master_name]
            else:
                # menu master not yet defined so store in pending
                if master_name not in self.menu_pending:
                    self.menu_pending[master_name] = {}
                master = self.menu_pending[master_name]
            if 'sub' not in master:
                master['sub'] = []
            master['sub'].append(data)
            actioned = True
        if 'name' not in data:
            if not actioned:
                print 'MENU: no name given', data
        else:
            if data['name'] not in self.menu_lookup:
                # have we got any pending sub menus?
                if data['name'] in self.menu_pending:
                    data['sub'] = self.menu_pending[data['name']]['sub']
                    del self.menu_pending[data['name']]
                # store our menu item so sub items can
                # easily be added later.
                self.menu_lookup[data['name']] = data
        if not actioned:
            # is in the root of the menu
            self.menu.append(data)

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

    def __init__(self, application):
        self.application = application
        self.node_manager = application.node_manager
        self.command_queue = []
        self.output = [] # this will be returned
        self.auto_login_cookie = None
        self.node_name = None

    def add_command(self, data):
        self.command_queue.append(data)

    def process(self):
        while self.command_queue:
            data = self.command_queue.pop()
            self.node(data)

    def node(self, data):

        # create our node token to hold state
        node_token = NodeToken(data, self.application)

        node = data.get('node')
        self.node_name = node
        self.run(node, node_token)
        self.output.extend(node_token.output())

        # auto login cookie info
        if node_token.auto_login_cookie:
            self.auto_login_cookie = node_token.auto_login_cookie


    def run(self, node_name, node_token, last_node = None):
        log.info('running node: %s, user id: %s' % (node_name, global_session.session['user_id']))
        log.debug('sent data: \n%s' % node_token.debug_info)

        sys_info = global_session.sys_info
        # check if application is private
        if not sys_info.get('public') and not global_session.session['user_id']:
            node_name = sys_info.get('default_node', node_name)
            node_token.command = sys_info.get('default_command')
            log.info('User not logged in.  Switching to node %s, command %s' % (node_name, node_token.command))

        # get node from node_manager
        # this should really get an existing node
        # node_class = self.node_manager[node_name]
        node = self.node_manager.get_node_instance(node_name)
        # pass the current node to the node token
        node_token.node = node
        node_token.node_name = node.name

        # the user cannot perform this action
        if not node.check_permissions():
            authenticate.forbidden(node_token)
        else:
            node.initialise(node_token)
            node.call(node_token)
            node.finalise(node_token)
            node.finish_node_processing(node_token)



## todo        if node.prev_node and node.prev_node.next_data_out:
## todo            node.out["data"].update(node.prev_node.next_data_out)
## todo
        if node_token.check_next_node():
            log.info('redirect to next node %s' % node_token.next_node)
            next_node = node_token.next_node_update()

            # clear the form cache so we don't get confussed
            self.form_cache = None
            return self.run(next_node, node_token)

