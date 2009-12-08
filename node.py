##   This file is part of Reformed.
##
##   Reformed is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License version 2 as
##   published by the Free Software Foundation.
##
##   Reformed is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even cthe implied warranty of
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
        self.extra_data = {}
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

    def build_node(self, title, command, data = '', node = None):
        if not node:
            node = self.name
        new_node = 'n:%s:%s:%s' % (node, command, data)
        if self.extra_data:
            if data:
                new_node += '&%s' % self.build_url_string_from_dict(self.extra_data)
            else:
                new_node += self.extra_data
        if title:
             new_node = '%s|%s' % (new_node, title)
        return new_node


    def build_function_node(self, title, function, data = '', command = ''):
        new_node = 'd:%s:%s:%s' % (function, command, data)
        if self.extra_data:
            if data:
                new_node += '&%s' % self.build_url_string_from_dict(self.extra_data)
            else:
                new_node += self.build_url_string_from_dict(self.extra_data)
        if title:
             new_node = '%s|%s' % (new_node, title)
        return new_node

    def build_url_string_from_dict(self, dict):
        # returns a url encoded string of a dict
        # FIXME not safe needs proper encodings
        out = []
        for key in dict.keys():
            out.append('%s=%s' % (key, dict[key]))
        return '&'.join(out)


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
    core_table = True
    fields = []
    field_list = []     # list of fields to be retrieved by searches (auto created)
    extra_fields = []
    form_params =  {"form_type": "normal"}
    list_title = 'item %s'
    title_field = 'name'

    subforms = {}
    subform_data = {}
    subform_field_list = {}

    code_groups = {}
    code_list = {}
    first_run = True

    list_fields = [
        ['title', 'link', 'title'],
        ['summary', 'info', 'summary'],
        ['edit', 'link_list', '']
    ]
    list_params = {"form_type": "results"}


    def __init__(self, *args, **kw):
        super(TableNode, self).__init__(*args, **kw)
        self.setup_code_groups()
        if self.__class__.first_run:
            self.__class__.first_run = False
            self.setup_forms()

    def setup_code_groups(self):
        self.__class__.code_list = {}
        for code_group_name in self.code_groups.keys():
            code_group = self.code_groups[code_group_name]
            table = code_group.get('code_table')
            field = code_group.get('code_field')
            codes = r.reformed.search(table, 'id>0', fields = [field])['data']
            code_array = []
            for row in codes:
                code_array.append(row.get(field))
            self.__class__.code_list[code_group_name] = code_array


    def setup_forms(self):
        for field in self.fields:
            # add subform data
            if field[1] == 'subform':
                name = field[0]
                subform = self.__class__.subforms.get(name)
                data = create_form_data(subform.get('fields'), subform.get('params'))
                data['form']['parent_id'] =  subform.get('parent_id')
                data['form']['child_id'] =  subform.get('child_id')
                data['form']['table_name'] =  subform.get('table')
                self.__class__.subform_data[name] = data
                field.append(data)
                self.setup_subforms(name)
            # add data for code groups
            elif field[1] == 'code_group':
                name = field[0]
                data = {}
                data['codes'] = self.__class__.code_list.get(name)
                field.append(data)
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
        if  self.command == 'edit':
            self.view(read_only = False)
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
        ignore_types = ['subform', 'code_group']
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
                if field_name != 'id' and field_type not in ignore_types and field_name != u'version_id':
                    # update/add the value
                    value = data.get(field_name)
                    print '%s = %s' % (field_name, value)
                    setattr(record_data, field_name, value)
            # if this is a subform we need to update/add the join field
            # FIXME is this needed here or just for new?
            # maybe shift up a few lines to new record
            for field_name in join_fields:
                    value = data.get(field_name)
                    print 'join: %s = %s' % (field_name, value)
                    setattr(record_data, field_name, value)
            try:
                session.save_or_update(record_data)
                session.commit()
                self.saved.append([root, record_data.id, record_data._version])
                return record_data
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

        record_data = self.save_record(session, self.table, self.fields, self.data, filter, root)

        # FIXME how do we deal with save errors more cleverly?
        # need to think about possible behaviours we want
        # and add some 'failed save' options
        if not self.errors:
            # subforms
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
            # code_groups
            if self.code_groups:
                self.save_group_codes(session, record_data)
        session.commit()
        session.close()

        # output data
        out = {}
        if self.errors:
            out['errors'] = self.errors
        if self.saved:
            out['saved'] = self.saved

        self.out = out
        self.action = 'save'

    def save_group_codes(self, session, record_data):
        for code_group_name in self.code_groups.keys():
            code_group = self.code_groups[code_group_name]
            table = code_group.get('flag_table')
            flag_child_field = code_group.get('flag_child_field')
            flag_parent_field = code_group.get('flag_parent_field')
            code_field = code_group.get('code_field')
            parent_value = getattr(record_data, flag_parent_field)
            code_group_data = self.data.get(code_group_name)

            #FIXME everything following this until session.commit() is rubbish
            # although it works i'm sure
            # a) it's not very efficient
            # b) it feels realy hacky
            # c) i just don't like it
            # still it will do for now

            if not code_group_data:
                code_group_data = []
            yes_codes = set(self.code_list[code_group_name]).intersection(set(code_group_data))
            no_codes = set(self.code_list[code_group_name]).difference(set(code_group_data))
            print "YES CODES", yes_codes
            print "NO CODES", no_codes
            print 'table', table
            print 'flag_child_field', flag_child_field
            print 'flag_parent_field', flag_parent_field
            print 'code_field', code_field
            print 'parent_value', parent_value

            for code in no_codes:
                filter = {flag_child_field: parent_value, code_field: code}
                obj = r.reformed.get_class(table)
                try:
                    data = session.query(obj).filter_by(**filter).one()
                    if data:
                        session.delete(data)
                except sa.orm.exc.NoResultFound:
                    pass


            for code in yes_codes:
                where = "%s='%s' and %s='%s'" % (flag_child_field, parent_value, code_field, code)
                result = r.reformed.search(table, where)['data']
                if not result:
                    # need to add this field
                    record_data = r.reformed.get_instance(table)
                    setattr(record_data, flag_child_field, parent_value)
                    setattr(record_data, code_field, code)
                    session.save_or_update(record_data)
                    print 'saved', record_data

    def new(self):

        data_out = {}
        data = create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'


    def view(self, read_only=True):
        id = self.data.get('id')
        if id:
            where = 'id=%s' % id
        else:
            id = self.data.get('__id')
            where = '_core_entity_id=%s' % id

        try:
            data_out = self.node_search_single(where)
            id = data_out.get('id')
            if self.title_field and data_out.has_key(self.title_field):
                self.title = data_out.get(self.title_field)
            else:
                self.title = '%s: %s' % (self.table, id)

        except sa.orm.exc.NoResultFound:
            data = None
            data_out = {}
            id = None
            self.title = 'unknown'
            print 'no data found'

        if data_out:
            for subform_name in self.subforms.keys():
                data_out[subform_name] = self.subform(subform_name, data_out)
            for code_group_name in self.code_list:
                data_out[code_group_name] = self.code_data(code_group_name, data_out)

        data = create_form_data(self.fields, self.form_params, data_out, read_only)
        self.out = data
        self.action = 'form'
        self.bookmark = self.build_node('', 'view', 'id=%s' %  id)


    def code_data(self, code_group_name, data_out):
        codes = self.code_groups.get(code_group_name)
        flag_table = codes.get('flag_table')
        flag_child_field = codes.get('flag_child_field')
        flag_parent_field = codes.get('flag_parent_field')
        flag_code_field = codes.get('flag_code_field')
        parent_value = data_out.get(flag_parent_field)

        where = "%s = '%s'" % (flag_parent_field, parent_value)
        results = r.reformed.search(flag_table, where, fields = [flag_code_field])['data']

        out = []
        for row in results:
            out.append(row[flag_code_field])
        return out

    def delete(self):
        id = self.data.get('id')
        if id:
            filter = {'id' : id}
        else:
            id = self.data.get('__id')
            filter = {'_core_entity_id' : id}
        # FIXME i'd rather get this data ourself and not rely on the returned info
        table = self.data.get('table_name', self.table)

        session = r.reformed.Session()
        obj = r.reformed.get_class(table)
        try:
            data = session.query(obj).filter_by(**filter).one()
            # code_groups
            if self.code_groups:
                self.save_group_codes(session, data)
            session.delete(data)
            session.commit()
            # FIXME this needs to be handled more nicely
            if self.form_params['form_type'] != 'grid' and self.table == table:
                self.next_data = {'command': 'list', 'data' : self.extra_data}
                self.next_node = self.name
            else:
                self.out = {'deleted': [self.data]}
                self.action = 'delete'
        except sa.orm.exc.NoResultFound:
            error = 'Record not found.'
            self.out = error
            self.action = 'general_error'
        except sa.exc.IntegrityError, e:
            print e

            error = 'The record cannot be deleted,\nIt is referenced by another record.'
            self.out = error
            self.action = 'general_error'
            session.rollback()
        session.close()


    def list(self, limit=20):
        query = self.data.get('q', '')
        limit = self.data.get('l', limit)
        offset = self.data.get('o', 0)

        if r.reformed[self.table].entity:
            results = r.reformed.search('_core_entity',
                                        where = "%s.id >0" % self.table,
                                        limit = limit,
                                        offset = offset,
                                        count = True)
        else:
            results = r.reformed.search(self.table,
                                        where = "id >0",
                                        limit = limit,
                                        offset = offset,
                                        count = True)

        data = results['data']
        # build the links
        if r.reformed[self.table].entity:
            for row in data:
                row['title'] = self.build_node(row['title'], 'edit', '__id=%s' % row['id'])
                row['edit'] = [self.build_node('Edit', 'edit', '__id=%s' % row['id']),
                               self.build_node('View', 'view', '__id=%s' % row['id']),
                               self.build_function_node('Delete', 'node_delete')
                              ]
                # the id is actually the _core_entity id so let's rename it to __id
                row['__id'] = row['id']
                del row['id']
        else:
            for row in data:
                if self.title_field and row.has_key(self.title_field):
                    row['title'] = self.build_node(row[self.title_field], 'edit', 'id=%s' % row['id'])
                else:
                    row['title'] = self.build_node('%s: %s' % (self.table, row['id']), 'edit', 'id=%s' % row['id'])

        out = create_form_data(self.list_fields, self.list_params, data)

        # add the paging info
        out['paging'] = {'row_count' : results['__count'],
                         'limit' : limit,
                         'offset' : offset,
                         'base_link' : 'n:%s:list:q=%s' % (self.name, query)}

        self.out = out
        self.action = 'form'
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
            out = r.reformed.search(table, where, fields = field_list)["data"]
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
            if field not in ['_modified_date', '_modified_by']:
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



def create_form_data(fields, params=None, data=None, read_only=False):
    out = {
        "form": {
            "fields":create_fields(fields)
        },
        "type": "form",
    }
    if data:
        out['data'] = data
    if params:
        out['form']['params'] = params.copy()
    if read_only:
        if not out['form']['params']:
            out['form']['params'] = {}
        out['form']['params']['read_only'] = True
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




