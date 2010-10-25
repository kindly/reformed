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
##   Copyright (c) 2008-2010 Toby Dacre & David Raznick
##



from node.node import JobNode, Node
from node.form import form
from node.page_item import *
from web.global_session import global_session

def make_menu(node_manager):
    node_manager.add_menu(dict(name = 'Data', menu = 'Admin', title = 'Data', node = None))

class DataGenerate(JobNode):

    main = form(
        text("##Data Generator##"),
        dropdown('table', 'DATA', data_field = 'tables', default = 'people'),
        intbox('number_records', default = 100),
        button('f@$:_generate', label = 'Generate'),
        form_type = "action",
    )

    job_type = 'generate'
    job_function = 'generate'
    params = []

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'Data', title = 'Generate Data', node = '$:select'))

    def setup_extra_commands(self):
        commands = self.__class__.commands
        commands['select'] = dict(command = 'select')
        commands['_generate'] = dict(command = 'generate')

    def select(self, node_token):
        tables = []
        for table in r.tables:
            if r[table].table_type == 'user':
                tables.append(r[table].name)

        data = dict(tables = tables)
        self['main'].show(node_token, data)

    def generate(self, node_token):
        data = node_token['main']
        table = data.get('table')
        number = data.get_data_int('number_records', 0)
        if r[table].table_type == 'user' and number:
            self.base_params = dict(table = table, number_requested = number)
            self.load(node_token, form_name = 'main')


class Truncate(Node):

    # FIXME This is horrific and needs to be replaced
    # Issues of security, user feedback,
    # lack of cancelation, things done in the wrong place etc.

    main = form(
        text("Truncate table :)"),
        dropdown('table', 'DATA', data_field = 'tables'),
        button('fc@$:truncate', label = 'Truncate'),
        form_type = "action",
    )
    completed = form(
        text("Table {table} has been truncated.  {records} record(s)."),
        extra_data('table'),
        extra_data('records'),
        form_type = "action",
    )

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'Data', title = 'Truncate Table', node = '$:list'))

    def call(self, node_token):
        if node_token.command == 'list':
            self.list_tables(node_token)
        elif node_token.command == 'truncate':
            table_name = node_token['main'].get('table')
            if table_name:
                self.truncate_table(node_token, table_name)

    def truncate_table(self, node_token, table_name):
        # FIXME this needs a proper method in database.py
        table = r[table_name]
        if table.table_type == 'user':
            records = r.search(table_name).results
            session = r.Session()
            count = 0
            for record in records:
                session.delete(record)
                count += 1
                print count
            session.commit()
            session.close()
            data = dict(table = table_name,
                        records = count)
            self['completed'].show(node_token, data)
            # As this is not a node level request
            # we need to set the layout by hand.
            # FIXME Can we do this more automated as this is likely
            # a common use case.
            node_token.set_layout('listing', [['completed']])


    def list_tables(self, node_token):
        tables = []
        for table in r.tables:
            if r[table].table_type == 'user':
                tables.append(r[table].name)

        data = dict(tables = tables)
        self['main'].show(node_token, data)

