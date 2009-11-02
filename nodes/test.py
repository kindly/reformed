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

import formencode as fe
from formencode import validators
import node
from node import TableNode, Node
from .reformed import reformed as r
import reformed.util as util
import sqlalchemy as sa


class DataLoader(Node):

    fields = [
        ['jobId', 'info', 'job #:'],
        ['start', 'info', 'start:'],
        ['message', 'info', 'msg'],
        ['percent', 'progress', 'progress: ']
    ]

    def call(self):

        if self.command == 'load':
            file = self.data.get('file')
            table = self.data.get('table')
            jobId = r.reformed.job_scheduler.add_job("loader", "data_load_from_file", "%s, %s" % (table, file))
            data = node.create_form_data(self.fields)
            data['jobId'] = jobId
            self.out = data
            self.action = 'status'
        elif self.command == 'status':
            session = r.reformed.Session()
            jobId = self.data.get('id')
            obj = r.reformed.get_class('_core_job_scheduler')
            filter = {'id': jobId}
            data = session.query(obj).filter_by(**filter).one()
            data_out = util.get_row_data(data, keep_all = False, basic = True)
            out = {'jobId' : jobId,
                   'start': data_out['job_started'],
                   'message':data_out['message'],
                   'percent':data_out['percent'],
                   'end':data_out['job_ended']}
            self.out = {'status': out, 'jobId' : jobId}
            self.action = 'status'
            session.close()




class Donkey(TableNode):

    table = "donkey"
    fields = [
        ['name', 'textbox', 'name:'],
        ['age', 'textbox', 'age:']
    ]
    list_title = 'donkey %s'
     
class People(TableNode):

    table = "people"

    subforms = {
        'email':{
            'fields': [
                ['email', 'textbox', 'email:']
            ],
            "parent_id": "id",
            "child_id": "people_id",
            "table": "email",
            "params":{
                "form_type": "grid"
            }                  
        },
        'sponsorship':{
            'fields': [
                ['amount', 'textbox', 'amount:'],
                ['donkey_id', 'textbox', 'donkey:']
            ],
            "parent_id": "id",
            "child_id": "people_id",
            "table": "donkey_sponsorship",
            "params":{
                "form_type": "grid"
            }
        }
    }

    fields = [
        ['name', 'textbox', 'name:'],
        ['address_line_1', 'textbox', 'address:'],
        ['address_line_2', 'textbox', 'town:'],
        ['postcode', 'textbox', 'postcode:'],
        ['email', 'subform', 'email'],
        ['sponsorship', 'subform', 'sponsorship']
    ]

    list_title = 'person %s'




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
