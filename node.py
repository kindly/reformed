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

import reformed.reformed as r
import reformed.util as util
import formencode as fe
import sqlalchemy as sa

class Node(object):

    def __init__(self, data, node_name, last_node = None):
        self.out = []
        self.name = node_name
        self.action = None
        self.next_node = None
        self.next_data = None
        self.last_node = data.get('lastnode')
        self.data = data.get('data')
        if type(self.data).__name__ != 'dict':
            self.data = {}
        self.command = data.get('command')

        if self.last_node == self.__class__.__name__:
            self.first_call = False
        else:
            self.first_call = True
        print '~~~~ NODE DATA ~~~~'
        print 'command:', self.command
        print 'last node:', self.last_node
        print 'first call:', self.first_call
        print 'data:', self.data
        print '~' * 19

    def initialise(self):
        """called first when the node is used"""
        pass

    def call(self):
        """called when the node is first used"""
        pass

    def finalise(self):
        """called last when node is used"""
        pass


class TableNode(Node):

    """Node for simple table level elements"""
    table = "unknown"
    fields = []
    form_params =  {"form_type": "normal"}
    list_title = 'item %s'

    def call(self):
        if  self.command == 'view':
            self._view()
        elif self.command == 'save':
            self._save()
        elif self.command == 'list':
            self._list()
        elif self.command == 'delete':
            self._delete()
        elif self.command == 'new':
            self._new()





    def _new(self):

        data_out = {'__id': 0}
        data = create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'


    def _view(self):
        id = self.data.get('__id')
        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        try:
            data = session.query(obj).filter_by(_core_entity_id = id).one()
            data_out = util.get_row_data_basic(data)
            data_out['__id'] = id
        except sa.orm.exc.NoResultFound:
            data_out = {}
        data = create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'


    def _save(self):

        id = self.data.get('__id')
        session = r.reformed.Session()
        try:
            if id != '0':
                obj = r.reformed.get_class(self.table)
                data = session.query(obj).filter_by(_core_entity_id = id).one()
            else:
                data = r.reformed.get_instance(self.table)
            for field in self.fields:
                field_name = field[0]
                value = self.data.get(field_name)
                setattr(data, field_name, value)
            try:
                session.save_or_update(data)
                session.commit()
            except fe.Invalid, e:
                session.rollback()
                print "we fucked!", e.msg
                errors = {}
                for key, value in e.error_dict.items():
                    errors[key] = value.msg
                print repr(errors)
                self.out = errors
                self.action = 'save_error'
        except sa.orm.exc.NoResultFound:
            errors = {'~': 'record not found'}
            self.out = errors
            self.action = 'save_error'
        session.close()


    def _delete(self):

        id = self.data.get('__id')
        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        try:
            data = session.query(obj).filter_by(_core_entity_id = id).one()
            session.delete(data)
            session.commit()
            self.next_node = self.name
            self.next_data = {'command': 'list'}
        except sa.orm.exc.NoResultFound:
            errors = {'~': 'record not found'}
            self.out = errors
            self.action = 'delete_error'
        session.close()


    def _list(self):
        print '######## %s'  % self.table
        results = r.reformed.search(self.table)
        out = []
        for result in results:
            row = {"table": result["__table"],
                   "id": result["_core_entity.id"],
                   "title": result["_core_entity.title"],
                   "summary": result["_core_entity.summary"]}
            out.append(row)

        self.out = out
        self.action = 'listing'


def create_fields(fields_list):

    fields = []
    for field in fields_list:
        row = {}
        row['name'] = field[0]
        row['type'] = field[1]
        row['title'] = field[2]
        if len(field) > 3:
            row['params'] = field[3]
        fields.append(row)
    return fields



def create_form_data(fields, params=None, data=None):
    out = {
        "form": {
            "fields":create_fields(fields) 
        },
        "type": "form", 
    }
    if data:
        out['data'] = data
    if params:
        out['form']['params'] = params
    return out

def validate_data(data, field, validator):
    try:
        return validator().to_python(data.get(field))
    except:
        return None

def validate_data_full(data, validators):
    validated_data = {}
    for (field, validator) in validators:
        validated_data[field] = validate_data(data, field, validator)
    return validated_data
