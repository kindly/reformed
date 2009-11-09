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
from global_session import global_session

class Node(object):

    permissions = []

    def __init__(self, data, node_name, last_node = None):
        self.out = []
        self.name = node_name
        self.title = None
        self.link = None
        self.action = None
        self.bookmark = None
        self.next_node = None
        self.next_data = None

        self.allowed = self.check_permissions()

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

    def check_permissions(self):
        if self.permissions:
            user_perms = set(global_session.session.get('permissions'))
            if not set(self.permissions).intersection(user_perms):
                return False
        return True

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

    """Node for table level elements"""
    table = "unknown"
    fields = []
    field_list = []     # list of fields to be retrieved by searches (auto created)
    extra_fields = []
    form_params =  {"form_type": "normal"}
    list_title = 'item %s'
    title_field = 'name'

    subforms = {}
    subform_data = {}
    subform_field_list = {}

    first_run = True



    def __init__(self, *args, **kw):
        super(TableNode, self).__init__(*args, **kw)
        if self.__class__.first_run:
            self.__class__.first_run = False
            print 'first run'
            self.setup_forms()

    def setup_forms(self):
        for field in self.fields:
            # add subform data
            if field[1] == 'subform':
                name = field[2]
                subform = self.__class__.subforms.get(name)
                data = create_form_data(subform.get('fields'), subform.get('params'))
                data['form']['parent_id'] =  subform.get('parent_id')
                data['form']['child_id'] =  subform.get('child_id')
                self.__class__.subform_data[name] = data
                field.append(data)
                self.setup_subforms(name)
            # build the field list
            self.field_list.append(field[0])
        # add any extra fields to the field list
        for field in self.extra_fields:
            self.field_list.append(field)

    def setup_subforms(self, name):
        extra_fields = []
        for field in self.subforms.get(name).get('fields'):
            extra_fields.append(field[0])
        self.subform_field_list[name] = extra_fields

    def call(self):
        if  self.command == 'view':
            self.view()
        elif self.command == '_save':
            self.save()
        elif self.command == 'list':
            self.list()
        elif self.command == '_delete':
            self.delete()
        elif self.command == 'new':
            self.new()


    def node_search_single(self, where):
        return r.reformed.search_single(self.table, where, fields = self.field_list)


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

    def save(self):

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

        self.out = out
        self.action = 'save'


    def new(self):

        data_out = {}
        data = create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'


    def view(self):
        id = self.data.get('id')
        if id:
            where = 'id=%s' % id
        else:
            id = self.data.get('__id')
            where = '_core_entity_id=%s' % id

        try:
            data_out = self.node_search_single(where)
            id = data_out.get('id')
            self.title = data_out.get(self.title_field)

        except sa.orm.exc.NoResultFound:
            data = None
            data_out = {}
            id = None
            self.title = 'unknown'
            print 'no data found'

        if data_out:
            for subform_name in self.subforms.keys():
                data_out[subform_name] = self.subform(subform_name, data_out)

        data = create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'
        self.bookmark = 'n:%s:view:id=%s' % (self.name, id)


    def delete(self):
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
            session.delete(data)
            session.commit()
            self.next_node = self.name
            self.next_data = {'command': 'list'}
        except sa.orm.exc.NoResultFound:
            errors = {'~': 'record not found'}
            self.out = errors
            self.action = 'delete_error'
        session.close()


    def list(self, limit=20):
        results = r.reformed.search('_core_entity', "%s.id >0" % self.table, limit=limit)
        out = []
        for result in results:
            row = {"table": self.table,
                   "id": result["id"],
                   "title": result["title"],
                   "summary": result["summary"]}
            out.append(row)

        self.out = out
        self.action = 'listing'
        self.title = 'listing'

    def subform(self, subform_name, data_out):
        subform_data = self.subform_data.get(subform_name)
        subform = self.subforms.get(subform_name)
        subform_parent_id = subform.get('parent_id')
        parent_value = data_out.get(subform_parent_id)
        table = subform.get('table')
        child_id = subform.get('child_id')
        field_list = self.subform_field_list[subform_name]

        where = "%s=%s" % (child_id, parent_value)
        try:
            out = r.reformed.search(table, where, fields = field_list)
        except sa.orm.exc.NoResultFound:
            out = {}
        return out


class AutoForm(TableNode):

    def __init__(self, *args, **kw):
        if self.__class__.first_run:
            self.setup()
        super(AutoForm, self).__init__(*args, **kw)

    def setup(self):
        fields = []
        obj = r.reformed.get_instance(self.table)
        columns = obj._table.schema_info
        for field in columns.keys():
            if field not in ['modified_date', 'modified_by']:
                fields.append([field, 'textbox', '%s:' % field])
        self.__class__.fields = fields




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
