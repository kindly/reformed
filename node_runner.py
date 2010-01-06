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

import nodes
import traceback
import imp
import sys
import paste


def node(data, caller):
    node = data.get('node')
    out = run(node, data)
    caller.output.append({'type' : 'node',
                          'data' : out})
def reload_nodes():
    global nodes
    nodes = reload(nodes)

    for node in globals():
        if node[:6] == 'nodes.':
            print 'reloading %s' % node
            imp.reload(sys.modules[node])


def run(node_name, data, last_node = None):
    print 'RUNNING NODE %s' % node_name
    node_base = node_name.split('.')[0]
    found = False
    if not hasattr(nodes, node_base):
        print "importing " + 'nodes.' + node_base
        try:
            globals()['nodes.' + node_base] = __import__('nodes.' + node_base)
        except:
            print "import failed"
            print traceback.print_exc()
            error_msg = 'IMPORT FAIL (%s)\n\n%s' % (node_name, traceback.format_exc())
            info = {'action': 'general_error',
                    'node': node_name,
                    'data' : error_msg}
            return info

    search_node = nodes
    node_path = node_name.split('.')
    for node in node_path:
        if hasattr(search_node, node):
            search_node = getattr(search_node, node)
            found = True
        else:
            found = False
            break

    if found:
        print "Node: %s, last: %s" % (node_name, last_node)
        x = search_node(data, node_name, last_node)
        if x.allowed:
            x.initialise()
            x.call()
            x.finalise()
            if x.next_node:
                return run(x.next_node, x.next_data, node_name)
            else:
                info = {'action': x.action,
                        'node': node_name,
                        'title' : x.title,
                        'link' : x.link,
                        'bookmark' : x.bookmark,
                        'data' : x.out}
                return info
        else:
            # the user cannot perform this action
            return {'action': 'general_error',
                    'data' : 'no permission'}
    else:
        print "Node <%s> not found" % node_name



