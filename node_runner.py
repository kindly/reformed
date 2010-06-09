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

    def __init__(self, data):

        self.last_node = None
        self.first_call = False
        self.command = data.pop('command', None)

        self.data = data.pop('data', None)
        if type(self.data).__name__ != 'dict':
            self.data = {}

        self.request_application_data = data.pop('request_application_data', False)
        self.output = None
        # output stuff
        self.out = []
        self.title = None
        self.link = None

        self.action = None
        self.bookmark = None
        self.user = None
        self.next_node = None
        self.next_data = None
        self.next_data_out = None
        self.auto_loggin_cookie = None

    def get_data_int(self, key, default = 0):
        """ Get integer value out of self.data[key] or default """
        try:
            value = int(self.data.get(key, default))
        except:
            value = default
        return value

    def set_form_message(self, message):
        """Sets the button info to be displayed by a form."""
        self.out['data']['__message'] = message

    def set_form_buttons(self, button_list):
        """Sets the button info to be displayed by a form."""
        if not self.out.get('data'):
            self.out["data"] = {}

        self.out['data']['__buttons'] = button_list



        
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
            print 'reuse node %s' % node_name
            return self.node_instances[node_name]
        else:
            print 'create node %s' % node_name
            instance = self.nodes[node_name](node_name)
            if not instance.volatile and instance.static:
                self.node_instances[node_name] = instance
        return instance

    def get_nodes(self):
        # get details of previously known nodes
        connection = self.application.zodb.open()
        root = connection.root()
        if "nodes" not in root:
            root["nodes"] = PersistentMapping()
            transaction.commit()
        else:
            # get cached info
            for key, value in root["nodes"].iteritems():
                self.processed_nodes[key] = value

        self.import_nodes()

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
                connection = self.application.zodb.open()
                zodb_root = connection.root()
                zodb_root["nodes"][root] = True
                transaction.commit()
                connection.close()



class NodeRunner(object):

    def __init__(self, node_manager):
        self.node_manager = node_manager
        self.command_queue = []
        self.output = [] # this will be returned
        self.auto_loggin_cookie = None
        
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


    def run(self, node_name, node_token, last_node = None):
        log.info('running node: %s, user id: %s' % (node_name, global_session.session['user_id']))
        log.debug('sent data: \n%s' %  pprint.pformat(node_token.data))

        sys_info = global_session.sys_info
        # check if application is private
        if not sys_info.get('public') and not global_session.session['user_id']:
            node_name = sys_info.get('default_node')
            node_token.data['command'] = sys_info.get('default_command')
            log.info('User not logged in.  Switching to node %s, command %s' % (node_name, node_token.data['command']))

        # get node from node_manager
        try:
            # this should really get an existing node
            # node_class = self.node_manager[node_name]
            node = self.node_manager.get_node_instance(node_name)
        except KeyError:
            raise NodeNotFound(node_name)

        node_token.node = node
    #    x = node_class(node_name, last_node)

        # the user cannot perform this action
        if not node.allowed:
            log.warn('forbidden node or command')
            return {'action': 'forbidden'}

        node.initialise(node_token)
        node.call(node_token)
        node.finalise(node_token)
        node.finish_node_processing(node_token)
## todo
## todo        # auto loggin cookie info
## todo        if xnode_token.auto_loggin_cookie:
## todo            self.auto_loggin_cookie = node.auto_loggin_cookie
## todo
## todo        if node.prev_node and node.prev_node.next_data_out:
## todo            node.out["data"].update(node.prev_node.next_data_out)
## todo
## todo        if node.next_node:
## todo            log.info('redirect to next node %s' % node.next_node)
## todo            return self.run(node.next_node, node.next_data, node)
## todo        else:
## todo            refresh_frontend = False

        # FIXME hack
        refresh_frontend = True
        info = {'action': node_token.action,
                'node': node_name,
                'title' : node_token.title,
                'link' : node_token.link,
                'user' : node_token.user,
                'bookmark' : node_token.bookmark,
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
                                      fields = ['title', 'bookmark', 'entity_table', 'entity_id', 'accessed_date'],
                                      values = [user_id],
                                      order_by = "accessed_date",
                                      keep_all = False,
                                      limit = limit).data
        return bookmarks
