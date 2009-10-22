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
import reformed.util as util
import sqlalchemy as sa

class Donkey(TableNode):

    table = "donkey"
    fields = [
        ['name', 'textbox', 'name:'],
        ['age', 'textbox', 'age:']
    ]
    list_title = 'donkey %s'
     
class People(TableNode):

    table = "people"
    email_subform = {"form": {
                    "fields": [
                        {
                            "type": "textbox",
                            "name": "email",
                            "title": "email:"
                        }
                    ]}}
    fields = [
        ['name', 'textbox', 'name:'],
        ['address_line_1', 'textbox', 'address:'],
        ['postcode', 'textbox', 'postcode:'],
        ['subform', 'subform', 'emails', email_subform]
    ]
    list_title = 'person %s'

    def _view(self):
        id = self.data.get('__id')
        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        try:
            data = session.query(obj).filter_by(_core_entity_id = id).one()
            data_out = util.get_row_data(data, keep_all = False, basic = True)
            data_out['__id'] = id
            people_id = data.id
        except sa.orm.exc.NoResultFound:
            data_out = {}
            people_id = 0
        obj = r.reformed.get_class('email')
        try:
            data = session.query(obj).filter_by(people_id = people_id).all()
            data_out['email'] = util.create_data_array(data, keep_all=False, basic=True)
     #       data_out['email']['__id'] = data.id
        except sa.orm.exc.NoResultFound:
            data_out['email'] = {}

        data = node.create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'
        session.close()




class Search(Node):

    def call(self, limit = 100):
        where = "_core_entity.title like '%%%s%%'" % self.command
        results = r.reformed.search('_core_entity', where, limit=limit)
        out = []
        for result in results:
            row = {"id": result["_core_entity.id"],
                   "title": result["_core_entity.title"],
                   "summary": result["_core_entity.summary"]}
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
            ['person', 'textbox', 'person id:', {'autocomplete': '/ajax/people/name'}],
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
