import traceback

import node_runner


class Interface(object):

    def __init__(self, http_session):
        self.http_session = http_session
        self.command_queue = [] 
        self.output = [] # this will be returned

    def add_command(self, command, data):
        self.command_queue.append((command, data))
        
    def reload_nodes(self):
        print "Reloading"
        global node_runner
        node_runner = reload(node_runner)
        node_runner.reload()
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
