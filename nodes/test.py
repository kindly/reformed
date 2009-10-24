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
        }
    }

    subform_data = {}

    fields = [
        ['name', 'textbox', 'name:'],
        ['address_line_1', 'textbox', 'address:'],
        ['postcode', 'textbox', 'postcode:'],
        ['email', 'subform', 'email']
    ]

    list_title = 'person %s'

    for field in fields:
        if field[1] == 'subform':
            name = field[2]
            subform = subforms.get(name)
            data = node.create_form_data(subform.get('fields'), subform.get('params'))
            data['form']['parent_id'] =  subform.get('parent_id')
            data['form']['child_id'] =  subform.get('child_id')
            print '###', data
            subform_data[name] = data
            field.append(data)


            
    def save_record_rows(self, session, table, fields, data, join_fields):
        for row_data in data:
            row_id = row_data.get('id', 0)
            root = row_data.get('__root')
            if row_id:
                filter = {'id' : row_id}
            else:
                filter = {}
            self.save_record(session, table, fields, row_data, filter, root = root, join_fields = join_fields)

    def save_record(self, session, table, fields, data, filter, root, join_fields = []):
        print 'table %s' % table
        print 'fields %s' % fields
        errors = None

        try:
            if filter:
                print 'existing record'
                obj = r.reformed.get_class(table)
                record_data = session.query(obj).filter_by(**filter).one()
            else:
                print 'new record'
                record_data = r.reformed.get_instance(table)
            for field in fields:
                field_name = field[0]
                field_type = field[1]
                if field_name != 'id' and field_type != 'subform':
                    value = data.get(field_name)
                    print '%s = %s' % (field_name, value)
                    setattr(record_data, field_name, value)
            for field_name in join_fields:
                    value = data.get(field_name)
                    print 'join: %s = %s' % (field_name, value)
                    setattr(record_data, field_name, value)
            try:
                session.save_or_update(record_data)
                session.commit()
                self.saved.append([root, record_data.id])
            except fe.Invalid, e:
                session.rollback()
                print "failed to save\n%s" % e.msg
                errors = {}
                for key, value in e.error_dict.items():
                    errors[key] = value.msg
                print repr(errors)
                self.errors[root] = errors
        except sa.orm.exc.NoResultFound:
            self.errors[root] = 'record not found'

    def _save(self):

        self.saved = []
        self.errors = {}

        session = r.reformed.Session()
        id = self.data.get('id')
        root = self.data.get('__root')
        if id:
            filter = {'id' : id}
        else:
            filter = {}

        self.save_record(session, self.table, self.fields, self.data, filter, root)

        # FIXME how do we deal with save errors more cleverly?
        # need to think about possible behaviours we want
        # and add some 'failed save' options
        if not self.errors:
            for subform_name in self.subforms.keys():
                subform_data = self.data.get(subform_name)
                if subform_data:
                    subform = self.subforms.get(subform_name)
                    table = subform.get('table')
                    fields = subform.get('fields')
                    # do we have a joining field?
                    child_id = subform.get('child_id')
                    if child_id:
                        join_fields= [child_id]
                    self.save_record_rows(session, table, fields, subform_data, join_fields)

        session.close()

        # output data
        out = {}
        if self.errors:
            out['errors'] = self.errors
        if self.saved:
            out['saved'] = self.saved
            print '@@@@@@@@@@@@@',self.saved

        self.out = out
        self.action = 'save'


    def _new(self):

        data_out = {}
        data = node.create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'


    def _view(self):
        id = self.data.get('id')
        if id:
            filter = {'id' : id}
        else:
            id = self.data.get('__id')
            filter = {'_core_entity_id' : id}

        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        try:
            data = session.query(obj).filter_by(**filter).one()
            data_out = util.get_row_data(data, keep_all = False, basic = True)
            data_out['id'] = data.id
            people_id = data.id
        except sa.orm.exc.NoResultFound:
            data_out = {}
            people_id = 0

        for subform_name in self.subforms.keys():
            subform = self.subforms.get(subform_name)
            subform_parent_id = subform.get('parent_id')
            subform_parent_value = getattr(data, subform_parent_id)
            subform_data = self.subform_data.get(subform_name)
            data_out[subform_name] = self.subform(session, subform, subform_data, subform_parent_value)

        data = node.create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'
        session.close()

    def subform(self, session, subform, form_data, parent_value):

        table = subform.get('table')
        child_id = subform.get('child_id')
        obj = r.reformed.get_class(table)
        filter = {child_id : parent_value}
        try:
            data = session.query(obj).filter_by(**filter).all()
            out = util.create_data_array(data, keep_all=False, basic=True)
        except sa.orm.exc.NoResultFound:
            out = {}
        return out


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
