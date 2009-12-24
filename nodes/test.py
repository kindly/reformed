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
from node import TableNode, Node, AutoForm
from .reformed.reformed import reformed as r
import sqlalchemy as sa
from global_session import global_session
from .reformed import reformed as table_functions

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

class UserGroup(TableNode):
    table = 'user_group'
    core_table = False
    title_field = 'groupname'
    fields = [
        ['groupname', 'Text', 'groupname:'],
        ['permission', 'code_group', 'permission:']
    ]
    code_groups = {'permission':{
                                    'code_table': 'permission',
                                    'code_field': 'permission',
                                    'flag_table': 'user_group_permission',
                                    'flag_child_field': 'groupname',
                                    'flag_code_field': 'permission',
                                    'flag_parent_field': 'groupname'
                                  }
                    }

class Permission(AutoForm):
    table = 'permission'
    core_table = False
    title_field = 'permission'


class User(TableNode):


    table = "user"
    fields = [
        ['name', 'Text', 'name:'],
        ['password', 'Text', 'password:'],
        ['usergroup', 'code_group', 'usergroups:']
    ]
    list_title = 'user %s'
    code_groups = {'usergroup':{
                                    'code_table': 'user_group',
                                    'code_field': 'groupname',
                                    'flag_table': 'user_group_user',
                                    'flag_child_field': 'name',
                                    'flag_code_field': 'groupname',
                                    'flag_parent_field': 'name'
                                  }
                    }

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
        limit = self.data.get('l', limit)
        offset = self.data.get('o', 0)

        where = "_core_entity.title like ?"
        results = r.search( '_core_entity',
                            where,
                            limit = limit,
                            offset = offset,
                            values = ['%%%s%%' % query],
                            fields=['table', 'title', 'summary'],
                            count = True,
                           )
        data = results['data']

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

        out = node.create_form_data(self.list_fields, self.list_params, data)

        # add the paging info
        out['paging'] = {'row_count' : results['__count'],
                         'limit' : limit,
                         'offset' : offset,
                         'base_link' : 'n:%s::q=%s' % (self.name, query)}
        self.out = out
        self.action = 'form'
        self.title = 'search for "%s"' % query


class Login(Node):

    fields = [
        ['name', 'Text', 'username:'],
        ['password', 'password', 'password:'],
        ['button', 'submit', 'moo', {'action': 'next', 'node': 'test.Login'}]
    ]
    form_params =  {"form_type": "action"}
    validations = [
        ['name', validators.UnicodeString],
        ['password', validators.UnicodeString]
    ]
    def call(self):
        vdata = node.validate_data_full(self.data, self.validations)
        if vdata['name'] and vdata['password']:
            where = "name='%s' and password='%s'" % (vdata['name'], vdata['password'])
            try:
                data_out = r.search_single('user', where)
                self.login(data_out)
            except:
                self.action = 'general_error'
                self.out = 'wrong guess'
        else:
            data = node.create_form_data(self.fields)
            self.action = 'form'
            self.out = data

    def login(self, data):
        global_session.session['user_id'] = data.get('id')
        global_session.session['permissions'] = ['logged_in']
        self.action = 'html'
        data = "<p>Hello %s you are now logged in, what fun!</p>" % data['name']
        self.out = {'html': data}


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

class AutoFormPlus(TableNode):

    field_type_2_input = {
        'Integer' : 'intbox',
        'Boolean' : 'checkbox',
        'DateTime' : 'datebox',
        'Date' : 'datebox',
        'Email' : 'emailbox',
        'Text' : 'textbox'
    }

    def initialise(self):
        self.table = self.data.get('table')
        self.extra_data = {'table':self.table}
        fields = []
        field_list = []
        obj = r[self.table]
        columns = obj.schema_info
        for field in columns.keys():
            if field not in ['_modified_date', '_modified_by','_core_entity_id', '_version']:
                if field in columns:
                    field_schema = obj.schema_info[field]
                    params = {'validation' : field_schema}
                    try:
                        field_type = obj.fields[field].__class__.__name__
                        fields.append([field, field_type, '%s:' % field, params])
                    except:
                        fields.append([field, 'Text', '%s:' % field, params])

                field_list.append(field)
        self.field_list = field_list
        self.fields = fields
        self.form_params =  {"form_type": "normal",
                             "extras" : self.extra_data,
                             "title" : obj.name
                            }


