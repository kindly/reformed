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

def node(data, caller):
    node = data.get('node')
    out = run(node, data)
    caller.output.append({'type' : 'node',
                          'data' : out})

def run(node_name, data, last_node = None):
    node_base = node_name.rsplit('.')[0]
    found = False
    if not hasattr(nodes, node_base):
        print "importing " + 'nodes.' + node_base
        try:
            globals()['nodes.' + node_base] = __import__('nodes.' + node_base)
        except:
            print "import failed"
            print traceback.print_exc()

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
        x = search_node(data, last_node)
        x.initialise()
        if node_name == last_node:
            x.call2()
        else:
            x.call1()
        x.finalise()
        if x.next_node:
            run(x.next_node, 'moo', node_name)
        else:
            info = {'action': x.action,
                    'node': node_name,
                    'data' : x.out}
            return info
    else:
        print "Node <%s> not found" % node_name


