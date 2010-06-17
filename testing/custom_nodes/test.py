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

from node import Node, TableNode, AutoForm
from form import form
from page_item import *

from global_session import global_session
r = global_session.database
application = global_session.application

class Node1(Node):
    main = form(
        text('Test Form.\n====\nThis demonstrates the page items available.'),
        layout('spacer'),
        text('Layouts\n----'),
        text('**Text**'),
        layout('text', text = '`text(text)` or  `layout(\'text\', text = text)`'),
        text('Text accepts [Markdown](http://en.wikipedia.org/wiki/Markdown#Syntax_examples) (wikipedia.org)'),
        
        text('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque posuere, purus quis ornare congue, leo metus dignissim elit, eu hendrerit enim orci at elit. Nulla lacus felis, feugiat id aliquam et, viverra eget enim. Mauris fringilla fermentum odio eget fermentum. Curabitur scelerisque quam vitae nibh volutpat ac vehicula nisi tempus. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec cursus turpis vitae enim sollicitudin mollis. Proin scelerisque felis in justo porttitor vestibulum. Integer placerat ultricies ligula non gravida. Morbi elementum metus quis erat dapibus eleifend. Proin non ultrices elit. Nulla ut felis nisl, eget aliquet nisi. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Morbi feugiat eleifend tristique. Aliquam nec tellus neque. Aliquam nec tellus eu sem fringilla tempor sed id metus.'),


        layout('spacer'),
        text('**Horizontal Rule**'),
        text('`layout(\'hr\')`'),
        layout('hr'),

        layout('spacer'),
        text('**Box**'),
        text('`layout(\'box_start\')`\n\n. . .\n\n`layout(\'box_end\')`'),
        layout('box_start'),
        text('Donec sit amet metus sem, at consectetur arcu. Curabitur condimentum, justo at euismod vehicula, nisl nibh scelerisque magna, aliquam laoreet nisl urna ut justo. Maecenas quis arcu in felis pulvinar egestas in ut lectus. Vestibulum varius fringilla massa, vel posuere risus ultricies ac. Vestibulum molestie facilisis purus, ut tincidunt sem fringilla eget. Cras in ligula hendrerit eros mattis porttitor. Cras eget quam arcu. Fusce non eros ligula, porta gravida velit. Donec erat orci, accumsan vitae varius ac, pulvinar in lectus. Curabitur risus ligula, vestibulum non viverra sed, condimentum sed mi.'),
        layout('box_end'),

        layout('spacer'),
        text('**Area**'),
        text('`layout(\'area\_start\', css=\'color\_background\')`\n\n. . .\n\n`layout(\'area_end\')`'),
        layout('area_start', css='color_background'),
        text('Donec sit amet metus sem, at consectetur arcu. Curabitur condimentum, justo at euismod vehicula, nisl nibh scelerisque magna, aliquam laoreet nisl urna ut justo. Maecenas quis arcu in felis pulvinar egestas in ut lectus. Vestibulum varius fringilla massa, vel posuere risus ultricies ac. Vestibulum molestie facilisis purus, ut tincidunt sem fringilla eget. Cras in ligula hendrerit eros mattis porttitor. Cras eget quam arcu. Fusce non eros ligula, porta gravida velit. Donec erat orci, accumsan vitae varius ac, pulvinar in lectus. Curabitur risus ligula, vestibulum non viverra sed, condimentum sed mi.'),
        layout('area_end'),


        layout('spacer'),
        text('**Columns**'),
        text('`layout(\'column_start\')`\n\n. . .\n\n`layout(\'column_next\')`\n\n. . .\n\n`layout(\'column_end\')`'),
        layout('column_start'),
        text('Column 1'),
        text('Nullam imperdiet ligula vel arcu mollis ac euismod odio sagittis. Nam fringilla enim quam. Duis vitae sem id justo consectetur adipiscing viverra nec dolor. Praesent aliquam mollis auctor. Donec nibh justo, laoreet ut tincidunt quis, bibendum ut libero. Nulla facilisi. Donec nisl ipsum, tempor nec molestie nec, lobortis in magna. Quisque pharetra luctus iaculis. Pellentesque lobortis augue in arcu condimentum ornare commodo ipsum egestas. Nullam in urna augue. Donec posuere turpis eget mi adipiscing adipiscing.'),
        layout('column_next'),
        text('Column 2'),
        text('Integer quis ante sem. Duis nec eros ac mi egestas pharetra. Proin at metus odio. Morbi lacinia justo felis. In eget luctus eros. Pellentesque sed ante libero, quis consequat turpis. Fusce ultrices vehicula consequat. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce mattis aliquet felis non ornare. Integer quis erat eget leo lacinia sollicitudin. Nullam hendrerit sodales mi at viverra. Aliquam erat volutpat.'),
        layout('column_end'),

        layout('spacer'),
        text('**Spacer**'),
        text('`layout(\'spacer\')`'),
        text('Nullam imperdiet ligula vel arcu mollis ac euismod odio sagittis. Nam fringilla enim quam. Duis vitae sem id justo consectetur adipiscing viverra nec dolor. Praesent aliquam mollis auctor. Donec nibh justo, laoreet ut tincidunt quis, bibendum ut libero. Nulla facilisi. Donec nisl ipsum, tempor nec molestie nec, lobortis in magna. Quisque pharetra luctus iaculis. Pellentesque lobortis augue in arcu condimentum ornare commodo ipsum egestas. Nullam in urna augue. Donec posuere turpis eget mi adipiscing adipiscing.'),
        layout('spacer'),
        text('Integer quis ante sem. Duis nec eros ac mi egestas pharetra. Proin at metus odio. Morbi lacinia justo felis. In eget luctus eros. Pellentesque sed ante libero, quis consequat turpis. Fusce ultrices vehicula consequat. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce mattis aliquet felis non ornare. Integer quis erat eget leo lacinia sollicitudin. Nullam hendrerit sodales mi at viverra. Aliquam erat volutpat.'),

        layout('spacer'),
        text('Controls\n----\nIn this test the controls are anonymous, that is they are not connected to any database fields.'),
        input('input', description = '`input(name)` defaults to a textbox as no field matches'),
        textbox('textbox', description = '`textbox(name)` should allow any text'),
        intbox('intbox', description = '`intbox(name)` integers only'),
        datebox('datebox', description = '`datebox(name)` dates only'),
        password('password', description = '`password(name)`'),
        checkbox('checkbox2', description = '`checkbox(name)` a 2 state (True/False) checkbox'),
        checkbox('checkbox3', validation = dict(not_empty = False), description = '`checkbox(name, validation = dict(not_empty = False))` a 3 state (True/False/Null) checkbox'),
        dropdown('dropdown', ['Red', 'Blue', 'Green'], description = "`dropdown(name, ['Red', 'Blue', 'Green'])`"),
        dropdown_code('dropdown_code', dict(descriptions = ['Red', 'Blue', 'Green'], keys = [1, 2, 3]), description = "`dropdown_code(name, dict(descriptions = ['Red', 'Blue', 'Green'], keys = [1, 2, 3])`", label = 'dropdown_code'),
        textarea('textarea', description = '`textarea(name)` a basic textarea'),
        wmd('wmd', description = '`wmd(name)` markdown textarea'),

        layout('spacer'),
        text('Controls with defaults\n----\nThese controls now have default values.'),
        input('input', default = 'default', description = 'default'),
        textbox('textbox', default = 'default', description = 'default'),
        intbox('intbox', default = 1234, description = '1234'),
        datebox('datebox', default = '??', description = '`datebox(name)` dates only'),
        checkbox('checkbox2', default = True, description = 'True'),
        checkbox('checkbox3', default = True, validation = dict(not_empty = False), description = 'True'),
        dropdown('dropdown', ['Red', 'Blue', 'Green'], default = 'Blue', description = 'Blue'),
        dropdown_code('dropdown_code', dict(descriptions = ['Red', 'Blue', 'Green'], keys = [1, 2, 3]), description = "Blue **THIS IS WRONG WE ARE SENDING DEFAULT = 'Blue' NOT DEFAULT = 1**", label = 'dropdown_code', default = 'Blue'),
        textarea('textarea', default = 'default\ntext', description = 'default \\n text'),
        wmd('wmd', default = 'default text **what fun** ;p', description = 'default text \*\*what fun\*\* ;p'),



        params =  {"form_type": "action"},
    )


    def call(self, node_token):
        self['main'].show(node_token)


class Node2(Node):

    main = form(
        text('**Buttons**'),
        button('test.Node2:Single+Button', label = 'Single Button'),
        button_box([['Button Box 1', 'test.Node2:Button+Box+1'],
                    ['Button Box 2', 'test.Node2:Button+Box+2'],
                    ['Button Box 3', 'test.Node2:Button+Box+3'],
                    ['Button Box 4', 'test.Node2:Button+Box+4'],
                    ['Button Box 5', 'test.Node2:Button+Box+5']]),
        text('**Lists**'),
        button_link('test.Node2:Single+Link', label = 'Single Link'),
        text('List of links using data.'),
        link_list('links'),
        text('List of links using fixed values.'),
        link_list(values = [['Link List Values 1', 'n:test.Node2:Link+List+Values+1'],
                            ['Link List Values 2', 'n:test.Node2:Link+List+Values+2'],
                            ['Link List Values 3', 'n:test.Node2:Link+List+Values+3'],
                            ['Link List Values 4', 'n:test.Node2:Link+List+Values+4'],
                            ['Link List Values 5', 'n:test.Node2:Link+List+Values+5']]),
        params = {"form_type": "action"}
    )


    def call(self, node_token):
        name = node_token.command.replace('+', ' ')
        if name:
            data = dict(__message = 'clicked: %s' % name)
        else:
            data = {}
        data['links'] = [['Link List Data 1', 'n:test.Node2:Link+List+Data+1'],
                         ['Link List Data 2', 'n:test.Node2:Link+List+Data+2'],
                         ['Link List Data 3', 'n:test.Node2:Link+List+Data+3'],
                         ['Link List Data 4', 'n:test.Node2:Link+List+Data+4'],
                         ['Link List Data 5', 'n:test.Node2:Link+List+Data+5']]
        self['main'].show(node_token, data)

class Node3(TableNode):

    main = form(
        input('name'),
        input('hex'),
        table = "colour",
        params =  {"form_type": "action"},
        title_field = 'name'
    )

class Node4(TableNode):

    main = form(
        input('text'),
        input('int'),
        autocomplete('colour', 'colour/name'),

        table = "table1",
        params =  {"form_type": "action"},
    )

class Node5(AutoForm):

    table = "table1"

class People(AutoForm):

    table = "people"

class DataLoader(Node):


    table = '_core_job_scheduler'
    permissions = ['LoggedIn']

    def call(self, node_token):

        if node_token.command == 'load':
            file = node_token.data.get('file')
            table = node_token.data.get('table')
            jobId = application.job_scheduler.add_job("loader", "data_load_from_file", table = table, file = file)
            node_token.link = "%s:refresh:id=%s" % (self.name, jobId)
            node_token.action = 'redirect'

        elif node_token.command == 'refresh':
            jobId = node_token.data.get('id')
            node_token.out = dict(data = self.get_status(jobId), form = True)
            node_token.action = 'status'

        elif node_token.command == 'status':
            jobId = node_token.data.get('id')
            node_token.out = dict(data = self.get_status(jobId))
            node_token.action = 'status'

        node_token.title = "job %s" % jobId


    def get_status(self, jobId):
        data_out = r.search_single_data(self.table, where = "id=%s" % jobId)
        out = dict(id = jobId,
                   start = data_out['job_started'],
                   message = data_out['message'],
                   percent = data_out['percent'],
                   end = data_out['job_ended'])
        return out



class Truncate(Node):

    main = form(
        text("Truncate table :)"),
        dropdown('table', 'DATA', data_field = 'tables'),
        button('test.Truncate:truncate:', label = 'Truncate'),
        params =  {"form_type": "action"},
    )
    completed = form(
        text("Table {table} has been truncated.  {records} record(s)."),
        extra_data('table'),
        extra_data('records'),
        params =  {"form_type": "action"},
    )
    def call(self, node_token):
        if node_token.command == 'list':
            self.list_tables(node_token)
        elif node_token.command == 'truncate':
            table_name = node_token.data.get('table')
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
            session.commit()
            session.close()
            data = dict(table = table_name,
                        records = count)
            self['completed'].show(node_token, data)


    def list_tables(self, node_token):
        tables = []
        for table in r.tables:
            if r[table].table_type == 'user':
                tables.append(r[table].name)

        data = dict(tables = tables)
        self['main'].show(node_token, data)

import data_creator
class Generate(Node):


    generators = dict(
        full_name = data_creator.make_name,
        int = data_creator.make_int,
        postcode = data_creator.make_postcode,
        town = data_creator.make_town,
    )

    def call(self, node_token):

        table = 'people'
        count = 10000
        commit_size = 100
        fields = [
            dict(name = 'name', generator = 'full_name'),
            dict(name = 'age', generator = 'int', params = dict( min = 16, max = 110)),
            dict(name = 'postcode', generator = 'postcode'),
            dict(name = 'town', generator = 'town'),
        ]
        session = r.Session()
        for i in xrange(count):
            obj = r.get_instance(table)
            postcode = None
            for field in fields:
                gen = field['generator']
                try:
                    params = field['params'].copy()
                except KeyError:
                    params = {}

                # towns are based on postcodes
                if gen == 'town' and postcode:
                    params['base'] = postcode

                if params:
                    value = self.generators[gen](**params)
                else:
                    value = self.generators[gen]()

                # cache any special 'reusable' values
                if gen == 'postcode':
                    postcode = value


                setattr(obj, field['name'], value)

            session.save(obj)

            if i and i % commit_size == 0:
                try:
                    session.commit()
                    print '---- %s ----' % i
                except:
                    # FIXME we are getting funny unicode error due to
                    # town names with none ascii names
                    print 'GGGRR we are struck by the evil unicode error'
                    session.rollback()
                    pass

        session.commit()
        session.close()

        node_token.action = 'general_error'
        node_token.out = 'Generated'
