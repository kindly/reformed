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


class NodeManager(object):

    """NodeManager imports and stores nodes form
    <app_root>/<app>/custom_nodes and <app_root>/nodes.
    If a node with the same name has already been imported any new node
    with the same name will be ignored.

    New node modules have their initialise() called but only once"""

    def __init__(self, application):
        self.application = application
        self.nodes = {}
        self.modules = {}
        self.processed_nodes = {}

    def __getitem__(self, value):
        return self.nodes[value]

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
                self.modules[root] = module
                for name in dir(module):
                    item = getattr(module, name)
                    if inspect.isclass(item):
                        if item.__module__ == node_root + '.' + root:
                            node_title = '%s.%s' % (root, name)
                    #        print 'importing %s' % node_title
                            self.nodes[node_title] = item
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

            except ImportError:
                log.critical('cannot import %s' % file)
                raise


class NodeRunner(object):

    def __init__(self, node_manager):
        self.node_manager = node_manager
        self.command_queue = []
        self.output = [] # this will be returned

    def add_command(self, data):
        self.command_queue.append(data)

    def process(self):
        while self.command_queue:
            data = self.command_queue.pop()
            self.node(data)

    def node(self, data):
        node = data.get('node')
        out = self.run(node, data)
        self.output.append({'type' : 'node',
                              'data' : out})


    def run(self, node_name, data, last_node = None):
        log.info('running node: %s, user id: %s' % (node_name, global_session.session['user_id']))
        log.debug('sent data: \n%s' %  pprint.pformat(data))

        sys_info = global_session.sys_info
        # check if application is private
        if not sys_info.get('public') and not global_session.session['user_id']:
            node_name = sys_info.get('default_node')
            data['command'] = sys_info.get('default_command')
            log.info('User not logged in.  Switching to node %s, command %s' % (node_name, data['command']))

        # get node from node_manager
        try:
            node_class = self.node_manager[node_name]
        except KeyError:
            raise NodeNotFound(node_name)

        x = node_class(data, node_name, last_node)

        # the user cannot perform this action
        if not x.allowed:
            log.warn('forbidden node or command')
            return {'action': 'forbidden'}

        x.initialise()
        x.call()
        x.finalise()
        x.finish_node_processing()

        if x.prev_node and x.prev_node.next_data_out:
            x.out["data"].update(x.prev_node.next_data_out)

        if x.next_node:
            log.info('redirect to next node %s' % x.next_node)
            return self.run(x.next_node, x.next_data, x)
        else:
            refresh_frontend = False

            info = {'action': x.action,
                    'node': node_name,
                    'title' : x.title,
                    'link' : x.link,
                    'user' : x.user,
                    'bookmark' : x.bookmark,
                    'data' : x.out}

            user_id = global_session.session['user_id']
            # application data
            if data.get('request_application_data'):
                    info['application_data'] = sys_info
                    info['application_data']['__user_id'] = user_id
                    info['application_data']['__username'] = global_session.session['username']
                    refresh_frontend = True
            # bookmarks
            if (info['user'] or refresh_frontend) and user_id:
                # we have logged in so we want our bookmarks
                info['bookmark'] = self.bookmark_list(user_id)
            log.debug('returned data\n%s\n----- end of node processing -----' % pprint.pformat(info))
            return info


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
