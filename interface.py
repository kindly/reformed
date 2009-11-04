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

import node_runner


class Interface(object):

    def __init__(self):
        self.command_queue = []
        self.output = [] # this will be returned

    def add_command(self, command, data):
        self.command_queue.append((command, data))

    def reload_nodes(self):
        print "Reloading"
        global node_runner
        node_runner = reload(node_runner)
        node_runner.reload_nodes()
        out ={'action': 'null',
              'node': '',
              'data' : 'Nodes reimported'}
        self.output.append({'type' : 'node',
                            'data' : out})


    def process(self):
        print "PROCESS"
        try:

            while self.command_queue:
                (command, data) = self.command_queue.pop()
                print command, repr(data)

                if command == 'node':
                    node_runner.node(data, self)
                elif command == 'reload':
                    self.reload_nodes()
        except:
            error_msg = 'ERROR\n\n%s' % (traceback.format_exc())
            out = {'action': 'general_error',
                    'node': 'moo',
                    'data' : error_msg}

            self.output.append({'type' : 'node',
                                'data' : out})
