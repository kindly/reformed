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

import traceback

from global_session import global_session

class Interface(object):

    def __init__(self):
        self.command_queue = []
        self.output = [] # this will be returned

    def add_command(self, data):
        self.command_queue.append(data)

    def process(self):
        print "PROCESS"
        try:

            while self.command_queue:
                data = self.command_queue.pop()
                print repr(data)

                self.node(data)
        except:
            error_msg = 'ERROR\n\n%s' % (traceback.format_exc())
            out = {'action': 'general_error',
                    'node': 'moo',
                    'data' : error_msg}

            self.output.append({'type' : 'node',
                                'data' : out})

    def node(self, data):
        node = data.get('node')
        out = self.run(node, data)
        self.output.append({'type' : 'node',
                              'data' : out})


    def run(self, node_name, data, last_node = None):
        print 'RUNNING NODE %s' % node_name
        sys_info = global_session.sys_info
        # check if application is private
        if not sys_info.get('public') and not global_session.session['user_id']:
            node_name = sys_info.get('default_node')
            data['command'] = sys_info.get('default_command')


        node_path = node_name.split('.')
        node_base = node_path[0]

        try:
            module = __import__('custom_nodes.' + node_base)
            print "importing " + 'custom_nodes.' + node_base
        except ImportError:
            try:
                module = __import__('nodes.' + node_base)
                print "importing " + 'nodes.' + node_base
            except ImportError:
                module = None

        if not module:
            print "import failed"
            print traceback.print_exc()
            error_msg = 'IMPORT FAIL (%s)\n\n%s' % (node_name, traceback.format_exc())
            info = {'action': 'general_error',
                    'node': node_name,
                    'data' : error_msg}
            return info

        search_node = module
        for node in node_path:
            if hasattr(search_node, node):
                search_node = getattr(search_node, node)
                found = True
            else:
                found = False
                break

        print "Node: %s, last: %s" % (node_name, last_node)
        x = search_node(data, node_name, last_node)

        # the user cannot perform this action
        if not x.allowed:
            return {'action': 'forbidden'}

        x.initialise()
        x.call()
        x.finalise()
        x.finish_node_processing()

        if x.prev_node and x.prev_node.next_data_out:
            x.out["data"].update(x.prev_node.next_data_out)

        if x.next_node:
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
