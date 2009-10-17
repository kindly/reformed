import traceback

import ajax
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

                if command == 'form':
                    ajax.ajax.get_form(data, self)
                elif command == 'data':
                    ajax.ajax.get_data(data, self)
                elif command == 'edit':
                    ajax.ajax.process_edit(data, self)
                elif command == 'action':
                    ajax.ajax.process_action(data, self)
                elif command == 'page':
                    ajax.ajax.process_page(data, self)
                elif command == 'html':
                    ajax.ajax.process_html(data, self)
                elif command == 'node':
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
