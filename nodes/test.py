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


class DataLoader(TableNode):

    fields = [
        ['jobId', 'info', 'job #:'],
        ['job_started', 'info', 'start:'],
        ['message', 'info', 'msg:'],
        ['percent', 'progress', 'progress: ']
    ]
    extra_fields = ['job_ended']
    table = '_core_job_scheduler'

    def call(self):

        if self.command == 'load':
            file = self.data.get('file')
            table = self.data.get('table')
            jobId = r.reformed.job_scheduler.add_job("loader", "data_load_from_file", "%s, %s" % (table, file))
            self.link = "%s:refresh:id=%s" % (self.name, jobId)
            self.action = 'redirect'

        elif self.command == 'refresh':
            jobId = self.data.get('id')
            data = node.create_form_data(self.fields)
            data['jobId'] = jobId
            data['status'] = self.get_status(jobId)
            self.out = data
            self.action = 'status'

        elif self.command == 'status':
            jobId = self.data.get('id')
            out = self.get_status(jobId)
            self.out = {'status': out, 'jobId' : jobId}
            self.action = 'status'

        self.title = "job %s" % jobId

    def get_status(self, jobId):
            data_out = self.node_search_single("id=%s" % jobId)
            out = {'jobId' : jobId,
                   'start': data_out['job_started'],
                   'message':data_out['message'],
                   'percent':data_out['percent'],
                   'end':data_out['job_ended']}
            return out


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
                ['donkey.name', 'textbox', 'donkey:']
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
        ['dob', 'textbox', 'dob:'],
        ['active', 'checkbox', 'active:'],
        ['email', 'subform', 'email'],
        ['sponsorship', 'subform', 'sponsorship']
    ]

    list_title = 'person %s'




class Search(Node):

    def call(self, limit = 100):
        query = self.data.get('q', '')
        where = "_core_entity.title like '%%%s%%'" % query
        results = r.reformed.search('_core_entity', where, limit=limit)
        out = []
        for result in results:
            row = {"id": result["id"],
                   "title": result["title"],
                   "summary": result["summary"]}
            if result['table'] == 8:
                row['table'] = 'donkey'
            else:
                row['table'] = 'people'
            out.append(row)
        self.out = out
        self.action = 'listing'
        self.title = 'search for "%s"' % query
        self.link = '%s::q=%s' % (self.name, query)


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
