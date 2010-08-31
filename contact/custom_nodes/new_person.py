from node import Node, TableNode, AutoForm, JobNode, AutoFormPlus
from form import form
from page_item import *
from pprint import pprint

from global_session import global_session
r = global_session.database
application = global_session.application


class NewPerson(Node):

    main = form(
        input('name', label = 'Name', description = "Persons name."),
        layout('spacer', label = 'spacer'), 
        input('communication', label = 'Contact info', description = "Enter either email, postcode or phone number."), 
        layout('spacer'), 
        layout('spacer'), 

        button_box([['add', 'new_person.EvaluateDuplicate:_save:'],
                    ['cancel', 'BACK'],]
                   ),
        params =  {"form_type": "normal"},
        volitile = True
    )

    def call(self, node_token):
        self['main'].show(node_token)
        node_token.out["data"]["__message"] = "Add new person."

class EvaluateDuplicate(Node):

    def call(self, node_token):
        node_token.action = 'redirect'
        node_token.link = 'new_person.MakeContact:next:'
        node_token.out = node_token.data
        

class MakeContact(Node):


    main = form(
        input('name', label = 'Name'),
        input('email.email', label = 'Email'),
        input('note.note', label = 'Note'),
        button_box([['save', 'new_person.SaveContact:_save:'],
                    ['cancel', 'BACK'],]
                   ),
        params =  {"form_type": "normal"},
        table = "people",
        title_field = 'name',
    )

    table = "people"

    def call(self, node_token):
        self["main"].show(node_token)
        node_token.out["data"]["__message"] = "Enter details"

class SaveContact(MakeContact):


    def call(self, node_token):
        self["main"].save(node_token, node_token.data)
        node_token.action = 'redirect'
        node_token.link = 'BACK'





class DataGenerate(JobNode):

    main = form(
        text("##Data Generator##"),
        dropdown('table', 'DATA', data_field = 'tables', default = 'people'),
        intbox('number_records', default = "100"),
        button('new_person.DataGenerate:_generate:', label = 'Generate'),
        params =  {"form_type": "action"},
    )

    job_type = 'generate'
    job_function = 'generate'
    params = []

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
        table = node_token.data.get('table')
        try:
            number = int(node_token.data.get('number_records', 0))
        except ValueError:
            number = 0
        if r[table].table_type == 'user' and number:
            self.base_params = dict(table = table, number_requested = number)
            self.load(node_token)

class People(TableNode):

    main = form(
        input('name'),
        input('dob'),
        thumb('image'),
        table = "people",
        params =  {"form_type": "normal"},
        title_field = 'name',
    )

    table = "people"

