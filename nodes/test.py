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

from formencode import validators
import node
from node import TableNode, Node
from .reformed import reformed as r

class Donkey(TableNode):

    table = "donkey"
    fields = [
        ['name', 'textbox', 'name:'],
        ['age', 'textbox', 'age:']
    ]
    list_title = 'donkey %s'
     
class People(TableNode):

    table = "people"
    fields = [
        ['name', 'textbox', 'name:'],
        ['address_line_1', 'textbox', 'address:'],
        ['postcode', 'textbox', 'postcode:']
    ]
    list_title = 'person %s'


class Search(Node):

    def call(self):

        results = r.reformed.search('_core_entity')
        out = []
        for result in results:
            row = {"id": result["_core_entity.id"],
                   "title": 'result id %s' % result["_core_entity.id"]}
            if result['_core_entity.table'] == 8:
                row['table'] = 'donkey'
            else:
                row['table'] = 'people'
            out.append(row)
        self.out = out
        self.action = 'listing'


class Sponsorship(Node):

    def call(self):

        fields = [
            ['info', 'info', 'please enter the id'],
            ['person', 'textbox', 'person id:', {'autocomplete':['111134556','1123','345','1211']}],
            ['button', 'submit', 'moo', {'action': 'next', 'node': 'test.Sponsorship'}]
        ]
        fields2 = [
            ['info', 'info', 'please enter the donkey id'],
            ['donkey', 'textbox', 'donkey id:'],
            ['button', 'submit', 'moo', {'action': 'next', 'node': 'test.Sponsorship'}]
        ]
        validations = [
            ['person', validators.Int],
            ['donkey', validators.Int]
        ]
        vdata = node.validate_data_full(self.data, validations)

        if vdata['donkey'] and  vdata['person']:
            data = {'html': 'person %s, donkey %s' % (vdata['person'], vdata['donkey'])}
            self.action = 'html'
        elif vdata['person']:
            data = node.create_form_data(fields2, data=vdata)
            self.action = 'form'
        else:
            data = node.create_form_data(fields, data=vdata)
            self.action = 'form'
        self.out = data
