from node import Node, TableNode, AutoForm, JobNode, AutoFormPlus
from form import form
from page_item import *
from pprint import pprint
from whoosh.query import Term, Or, And, Phrase
import reformed.parsers as parsers
import whoosh.analysis

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

        button_box([['add', 'f:new_person.EvaluateDuplicate::'],
                    ['cancel', 'BACK'],]
                   ),
        params =  {"form_type": "normal"},
        volitile = True
    )

    def call(self, node_token):
        data = dict(__message = "Add new person.", name = "fred" )
        self['main'].show(node_token, data)

class EvaluateDuplicate(Node):

    def call(self, node_token):
        data = node_token['main'].data
        #node_token.redirect('new_person.MakeContact::', node_data = data)
        node_token.general_error(str(self.get_results(data)))
        #if not_results:
        #node_token.next_node('f:new_person.MakeContact', node_data = data, command = 'next')

    def run_full_text_search(self, data):

        index = r.application.text_index
        searcher = index.searcher()

        sn = r.search_names
        terms = []

        names = data["name"]
        ana = whoosh.analysis.StandardAnalyzer()
        communication = data["communication"]

        email = parsers.email(communication)
        phone_number = parsers.phonenumber(communication)
        postcode = parsers.postcode(communication)
        dob = parsers.date(communication)

        print postcode 

        email_terms = []
        
        if names:
            terms.append(Phrase(sn["name"], names))
            for token in ana(names):
                terms.append(Term(sn["name"], token.text))

        if email:
            email_terms = [token.text for token in ana(email[1])]
            for email_term in email_terms:
                terms.append(Term(sn["email"], email_term))
            terms.append(Phrase(sn["email"], email_terms, boost = 2))

        if phone_number:
            terms.append(Term(sn["number"], phone_number[1], boost = 2))
        if dob:
            terms.append(Term(sn["dob"], dob[1], boost = 2))
        if postcode:
            terms.append(Term(sn["postcode"], postcode[1], boost = 2))

        query = Or(terms)

        print query

        result = searcher.search(query)

        core_ids = [a["core_id"] for a in result]

        return core_ids

    def match_results(self, data, field, value):

        ana = whoosh.analysis.StandardAnalyzer()

        if field == "name":
            for token in ana(value):
                if token.text in data["name"]:
                    return True

        if field == "email":
            for token in ana(value):
                if token.text in data["communication"]:
                    return True

        if value in data["communication"]:
            return True

    def get_results(self, data):

        si = r.search_ids
        core_ids = self.run_full_text_search(data)

        if not core_ids:
            return

        query = {"_core_id": ("in", core_ids)}

        results = r.search("search_info",
                           query,
                           order_by = "_core_id")
        
        current_core_id = None

        current_result = {}

        result_lookup = {}

        for result in results:
            result_core_id = result.get("_core_id")
            if current_core_id != result_core_id and current_core_id:
                current_result["_core_id"] = current_core_id 
                result_lookup[current_core_id] = current_result
                current_result = {}
                current_core_id = result_core_id
            else:
                current_core_id = result_core_id

            value = result.get("value")
            field = si[str(result.get("field"))]

            if self.match_results(data, field, value):
                current_result[field] = value
        else:
            current_result["_core_id"] = current_core_id
            result_lookup[result_core_id] = current_result

        ordered_results = []
        for core_id in core_ids:
            ordered_results.append(result_lookup[int(core_id)])


        return ordered_results


class MakeContact(Node):


    main = form(
        input('name', label = 'Name'),
        input('email.email', label = 'Email'),
        input('note.note', label = 'Note'),
        button_box([['save', 'new_person.SaveContact:_:'],
                    ['cancel', 'BACK'],]
                   ),
        params =  {"form_type": "normal"},
        table = "people",
        title_field = 'name',
        save_redirect = 'new_person.People:edit',
    )

    table = "people"

    def call(self, node_token):
        # retrieve the posted data to populate the form
        data = node_token.get_node_data().data
        data['__message'] = "Enter details"
        self["main"].show(node_token, data)

class SaveContact(MakeContact):

    def call(self, node_token):
        self["main"].save(node_token)



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
        node_data = node_token['main']
        table = node_data.get('table')
        number = node_data.get_data_int('number_records', 0)

        if r[table].table_type == 'user' and number:
            self.base_params = dict(table = table, number_requested = number)
            self.load(node_token, form_name = 'main')

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

