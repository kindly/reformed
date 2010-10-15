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

from node.node import TableNode, Node 
from node.page_item import *
from web.global_session import global_session

r = global_session.database

class HomePage(Node):

    def call(self):
        page = [
            {'title' : 'people',
             'summary' : 'la lal ',
             'options' : [
                {'title' : 'new',
                'link' : 'n:test.People:new'},
                {'title' : 'list',
                'link' : 'n:test.People:list'}
                ]
            },
            {'title' : 'donkey',
             'summary' : 'la lal ',
             'options' : [
                {'title' : 'new',
                'link' : 'n:test.Donkey:new'},
                {'title' : 'list',
                'link' : 'n:test.Donkey:list'}
                ]
            },
            {'title' : 'user',
             'summary' : 'la lal ',
             'options' : [
                {'title' : 'new',
                'link' : 'n:test.User:new'},
                {'title' : 'list',
                'link' : 'n:test.User:list'}
                ]
            }



        ]

        self.out = page
        self.action = 'page'

class DataLoader(TableNode):

    fields = [
        ['jobId', 'info', 'job #:'],
        ['job_started', 'info', 'start:'],
        ['message', 'info', 'msg:'],
        ['percent', 'progress', 'progress: ']
    ]
    extra_fields = ['job_ended']
    table = '_core_job_scheduler'
    permissions = ['logged_in']

    def call(self):

        if self.command == 'load':
            file = self.data.get('file')
            table = self.data.get('table')
            jobId = r.job_scheduler.add_job("loader", "data_load_from_file", "%s, %s" % (table, file))
            self.link = "%s:refresh:id=%s" % (self.name, jobId)
            self.action = 'redirect'

        elif self.command == 'refresh':
            jobId = self.data.get('id')
            data = self.create_form_data(self.fields)
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
        ['name', 'Text', 'name:'],
        ['age', 'Integer', 'age:']
    ]
    list_title = 'donkey %s'

class People(TableNode):

    table = "people"

    subforms = {
        'email':{
            'fields': [
                ['email', 'Text', 'email:']
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
                ['amount', 'Text', 'amount:'],
                ['donkey.name', 'Text', 'donkey:']
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
        ['name', 'Text', 'name:'],
        ['address_line_1', 'Text', 'address:'],
        ['address_line_2', 'Text', 'town:'],
        ['postcode', 'Text', 'postcode:'],
        ['dob', 'Date', 'dob:'],
        ['active', 'Boolean', 'active:'],
        ['email', 'subform', 'email'],
        ['sponsorship', 'subform', 'sponsorship']
    ]

    list_title = 'person %s'




class Search(TableNode):

    def call(self, limit = 100):
        query = self.data.get('q', '')
        limit = self.get_data_int('l', limit)
        offset = self.get_data_int('o')

        where = "_core_entity.title like ?"
        results = r.search( '_core_entity',
                            where,
                            limit = limit,
                            offset = offset,
                            values = ['%%%s%%' % query],
                            fields=['table', 'title', 'summary'],
                            count = True,
                           )
        data = results.data

        for row in data:
            # FIXME want nicer way of getting the table name
            table_name = r[row['table']].name
            table_name = table_name[0].upper() + table_name[1:]
            row['title'] = 'n:test.%s:view:__id=%s|%s: %s' % (table_name,
                                                               row['id'],
                                                               table_name,
                                                               row['title'])

            row['edit'] = ['n:test.%s:edit:__id=%s|Edit' % (table_name,
                                                               row['id']),
                           'n:test.%s:view:__id=%s|View' % (table_name,
                                                           row['id'])                                                  ]

        out = self["listing"].create_form_data(data)

        # add the paging info
        out['paging'] = {'row_count' : results.row_count,
                         'limit' : limit,
                         'offset' : offset,
                         'base_link' : 'n:%s::q=%s' % (self.name, query)}
        self.out = out
        self.action = 'form'
        self.title = 'search for "%s"' % query


class Sponsorship(Node):

    def call(self):

        fields = [
            ['info', 'info', 'please enter the id'],
            ['person', 'Text', 'person id:', {'autocomplete': '/ajax/people/name'}],
            ['button', 'submit', 'moo', {'action': 'next', 'node': 'test.Sponsorship'}]
        ]
        fields2 = [
            ['info', 'info', 'please enter the donkey id'],
            ['donkey', 'Text', 'donkey id:'],
            ['button', 'submit', 'moo', {'action': 'next', 'node': 'test.Sponsorship'}]
        ]
        validations = [
            ['person', validators.Int],
            ['donkey', validators.Int]
        ]
        vdata = self.validate_data_full(self.data, validations)

        if vdata['donkey'] and  vdata['person']:
            data = {'html': 'person %s, donkey %s' % (vdata['person'], vdata['donkey'])}
            self.action = 'html'
        elif vdata['person']:
            data = self.create_form_data(fields2, data=vdata)
            self.action = 'form'
        else:
            data = self.create_form_data(fields, data=vdata)
            self.action = 'form'
        self.out = data



