from pprint import pprint
from collections import defaultdict

import whoosh.analysis
from whoosh.query import Term, Or, And, Phrase

from node.node import Node, TableNode, AutoForm, JobNode, AutoFormPlus
from node.form import form
from node.page_item import *
import database.parsers as parsers
import database.util as util

from web.global_session import global_session

r = global_session.database
application = global_session.application

def make_menu(node_manager):
    node_manager.add_menu(dict(name = 'people', title = 'people'))

def parse_communication(communication, display = False):

    index = 0 if display else 1

    email = parsers.email(communication)[index]
    phone_number = parsers.phonenumber(communication)[index]
    postcode = parsers.postcode(communication)[index]
    dob = parsers.date(communication)[index]

    return locals()


class NewPerson(Node):

    main = form(
        input('name', label = 'Name', description = "Persons name."),
        layout('spacer', label = 'spacer'),
        input('communication', label = 'Contact info', description = "Enter either email, postcode or phone number."),
        layout('spacer'),
        layout('spacer'),

        ##FIXME data is not passed to evaluate duplicate properely
        button_box([['add', 'fu@$:process'],
                    ['cancel', 'BACK'],]
                   ),
        params =  {"form_type": "normal"},
        volitile = True
    )

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'people', title = 'new person', node = '$'))

    def call(self, node_token):
        data = node_token["main"].data
        if node_token.command == "process":
            node_token.redirect("new_person.ProcessResults", data)
            return
        data = dict(__message = "Add new person.", )
        self['main'].show(node_token, data)


class ProcessResults(Node):

    list = form(
        result_link('__name', label = "title"),
        info('summary', data_type = 'info'),
        form_type = "results",
        layout_title = "results",
    )

    def call(self, node_token):

        data = node_token.get_node_data().data
        results = self.get_results(data)

        if results:
            ##FIXME there should be a better way to do this
            node_token.set_layout("listing", [["list"]])
            self.show_list(node_token, results)
        else:
            node_token.next_node("new_person.MakeContact", data)


    def show_list(self, node_token, results):

        data = {'__array' : results}
        self["list"].create_form_data(node_token, data)
        node_token.form(self)
        #node_token.set_layout("listing", [["list"]])
        data['__buttons'] = [['add new', '@new_person.MakeContact'],
                             ['cancel', 'BACK']]

        data['__message'] = "These are the potential duplicates"

    def run_full_text_search(self, data):

        index = r.application.text_index
        searcher = index.searcher()

        sn = r.search_names
        terms = []

        ##FIXME what if there if there is not name or data
        names = data["name"]
        ana = whoosh.analysis.StandardAnalyzer()
        communication = data["communication"]

        comms = parse_communication(communication)
        email = comms["email"]
        phone_number = comms["phone_number"]
        dob = comms["dob"]
        postcode = comms["postcode"]

        email_terms = []
        if names:
            terms.append(Phrase(sn["name"], names))
            for token in ana(unicode(names)):
                terms.append(Term(sn["name"], token.text))

        if email:
            email_terms = [token.text for token in ana(email)]
            for email_term in email_terms:
                terms.append(Term(sn["email"], email_term))
            terms.append(Phrase(sn["email"], email_terms, boost = 2))

        if phone_number:
            terms.append(Term(sn["number"], phone_number, boost = 2))
        if dob:
            terms.append(Term(sn["dob"], dob, boost = 2))
        if postcode:
            terms.append(Term(sn["postcode"], postcode, boost = 2))

        if not terms:
            return []

        print terms

        query = Or(terms)

        result = searcher.search(query)

        core_ids = [a["core_id"] for a in result]

        return core_ids

    def match_results(self, data, field, value):

        ana = whoosh.analysis.StandardAnalyzer()

        for token in ana(value):
            if token.text in data["name"] and field == "name":
                return True
            if token.text in data["communication"] and field != "name":
                return True


    def get_results(self, data):

        si = r.search_ids
        core_ids = self.run_full_text_search(data)

        if not core_ids:
            return

        query = {"_core_id": ("in", core_ids)}

        results = r.search("search_info",
                           query,
                           )

        current_core_id = None

        result_lookup = defaultdict(dict)

        for result in results:
            result_core_id = result.get("_core_id")
            value = result.get("value")
            field = si[str(result.get("field"))]
            if field == "name":
                result_lookup[result_core_id]["__name"] = value

            if self.match_results(data, field, value):
                result_lookup[result_core_id][field] = value

        ordered_results = []
        for core_id in core_ids:
            result_dict = result_lookup[int(core_id)]
            summary = "matches \n\n" + "\n".join(["%s: %s" % (k, v)
                                               for (k, v) in result_dict.items()
                                               if not k == "__name"])
            result_dict["__id"] = core_id
            result_dict["summary"] = summary
            result_dict['result_url'] = '%s:edit?id=%s' % (self.name, core_id)
            ordered_results.append(result_dict)


        return ordered_results


class MakeContact(Node):


    main = form(
        input('name', label = 'Name'),
        input('dob', label = 'DOB'),
        input('telephone.number', label = 'Phone Number'),
        input('email.email', label = 'Email'),
        input('address.address_line_1', label = 'Address'),
        input('address.address_line_2', label = 'Address'),
        input('address.address_line_3', label = 'Address'),
        input('address.address_line_4', label = 'Address'),
        input('address.postcode', label = 'Postcode'),
        input('address.town', label = 'Town'),
        input('address.country', label = 'address'),
        input('note.note', label = 'Note'),
        form_type = "normal",
        table = "people",
        title_field = 'name',
        save_redirect = 'new_person.People:edit',
    )

    table = "people"

    def call(self, node_token):
        # retrieve the posted data to populate the form
        data = node_token.get_node_data()
        print data
        new_data = dict()

        node_token.set_layout_buttons([['save', 'f@new_person.SaveContact:_'],
                                   ['cancel', 'BACK'],]
                                )

        new_data["name"] = data.get("name")

        communication = data.get("communication")

        if communication:
            comms = parse_communication(communication, display = True)
            new_data["email.email"] = comms["email"]
            new_data["address.postcode"] = comms["postcode"]
            new_data["telephone.number"] = comms["phone_number"]
            new_data["dob"] = util.convert_value(comms["dob"])


        node_token.set_layout_title("Enter details")
        self["main"].show(node_token, new_data)

class SaveContact(MakeContact):

    def call(self, node_token):
        self["main"].save(node_token)



class DataGenerate(JobNode):

    main = form(
        text("##Data Generator##"),
        dropdown('table', 'DATA', data_field = 'tables', default = 'people'),
        intbox('number_records', default = "100"),
        button('f@new_person.DataGenerate:_generate', label = 'Generate'),
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
        node_data = node_token['main']
        table = node_data.get('table')
        number = node_data.get_data_int('number_records', 0)

        if r[table].table_type == 'user' and number:
            self.base_params = dict(table = table, number_requested = number)
            self.load(node_token, form_name = 'main')

class People(TableNode):

    register_node = dict(table = 'people', title = 'People', cat_node = 'new_person.People:list')

    main = form(
        input('name'),
        input('salutation'),
        input('prefered_name'),
        input('alterative_name'),
        input('dob'),
        #input('gender'),
        #input('source'),
        table = "people",
        form_type = "input",
        title_field = 'name'
    )

    ##Sort
    phone = form(
        input('number'),
        grid_link('id', label = 'edit', field = 'id', base_link = 'd@$:_update?', target_form = 'phone_new'),
        grid_link('id', label = 'delete', field = 'id', base_link = '@$:_delete?', target_form = 'phone_new'),
        read_only = True,
        form_type = 'grid',
        title_field = 'name',
        table = "telephone",
        form_buttons = [['new phone', 'd@$:new', 'phone_new']],
    )


    phone_new = form(
        input('number', label = 'number'),
      #  button('l:test.People:_save:', title = 'save'),
        form_type = "input",
        table = "telephone",
        save_update = 'phone',
        title_field = 'number',
        form_buttons = [['save', 'f@$:_save'],
                        ['cancel', 'CLOSE']],
        layout_title = 'Phone number',
    )

    layout_type = "entity"
    layout_main_form = "main"
    form_layout = [[],[],['main',"phone"]]

    table = "people"

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'people', title = 'list person', node = '$:list'))
