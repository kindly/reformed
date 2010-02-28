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

import reformed.util as util
from reformed import custom_exceptions
import formencode as fe
import sqlalchemy as sa
import datetime
from global_session import global_session
from page_item import link, link_list, info, input
from form import Form
r = global_session.database

class Node(object):

    permissions = []
    commands = {}

    def __init__(self, data, node_name, last_node = None):

        _forms = {}
        for form_name, form in self.__class__.__dict__.iteritems():
            if isinstance(form, Form):
                form.set_name(form_name)
                form.set_node(self)
                _forms[form_name] = form

        self.fields = _forms["main"].fields

        self.out = []
        self.name = node_name
        self.title = None
        self.link = None

        self.action = None
        self.bookmark = None
        self.user = None
        self.next_node = None
        self.next_data = None
        self.extra_data = {}
        self.command = data.get('command')
        self.allowed = self.check_permissions()

        self.last_node = data.get('lastnode')
        self.data = data.get('data')
        if type(self.data).__name__ != 'dict':
            self.data = {}

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

    def call(self):
        """called when the node is used.  Checks to see if there
        is a function to call for the given command"""

        command_info = self.commands.get(self.command)
        if not command_info:
            return
        command = command_info.get('command')

        if command_info.get('permissions'):
            user_perms = set(global_session.session.get('permissions'))
            if not set(command_info.get('permissions')).intersection(user_perms):
                self.action = 'forbidden'
                self.command = None
                print 'forbidden'
                return

        if command:
            command = getattr(self, command)
            command()
        else:
            self.action = 'general_error'
            self.out = "Command '%s' in node '%s' not known" % (self.command, self.name)

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

    def get_data_int(self, key, default = 0):
        """ Get integer value out of self.data[key] or default """
        try:
            value = int(self.data.get(key, default))
        except:
            value = default
        return value

    def update_bookmarks(self):

        user_id = global_session.session['user_id']

        # only update bookmarks for proper users
        if user_id:
            try:
                result = r.search_single("bookmarks",
                                         "user_id = ? and bookmark = ?",
                                         fields = ['title', 'bookmark', 'entity_table', 'entity_id', 'accessed_date'],
                                         values = [user_id, self.bookmark["bookmark_string"]])
                result["accessed_date"] = util.convert_value(datetime.datetime.now())
                result["title"] = self.title
            except custom_exceptions.SingleResultError:
                result = {"__table": "bookmarks",
                          "entity_id": self.bookmark["entity_id"],
                          "user_id": user_id,
                          "bookmark": self.bookmark["bookmark_string"],
                          "title": self.title,
                          "entity_table": self.bookmark["table_name"],
                          "accessed_date": util.convert_value(datetime.datetime.now())}
            # save
            util.load_local_data(r, result)

        else:
            # anonymous user
            result = {"__table": "bookmarks",
                      "entity_id": self.bookmark["entity_id"],
                      "bookmark": self.bookmark["bookmark_string"],
                      "title": self.title,
                      "entity_table": self.bookmark["table_name"],
                      "accessed_date": util.convert_value(datetime.datetime.now())}

        # update bookmark output to front-end
        self.bookmark = result


    def create_form_data(self, fields, params=None, data=None, read_only=False):
        out = {
            "form": {
                "fields":self.create_fields(fields)
            },
            "type": "form",
        }
        if data:
            out['data'] = data
        else:
            out['data'] = {}
        if params:
            out['form']['params'] = params.copy()
        if read_only:
            if not out['form']['params']:
                out['form']['params'] = {}
            out['form']['params']['read_only'] = True
        return out

    def create_fields(self, fields_list):

        fields = []
        for field in fields_list:
            row = field.convert(self, fields_list)
            fields.append(row)
        return fields

    def set_form_message(self, message):
        """Sets the button info to be displayed by a form."""
        self.out['data']['__message'] = message

    def set_form_buttons(self, button_list):
        """Sets the button info to be displayed by a form."""
        self.out['data']['__buttons'] = button_list

    def validate_data(self, data, field, validator):
        try:
            return validator().to_python(data.get(field))
        except:
            return None

    def validate_data_full(self, data, validators):
        validated_data = {}
        for (field, validator) in validators:
            validated_data[field] = self.validate_data(data, field, validator)
        return validated_data

    def finish_node_processing(self):

        if self.bookmark and self.bookmark != 'CLEAR':
            self.update_bookmarks()

    def initialise(self):
        """called first when the node is used"""
        pass

    def finalise(self):
        """called last when node is used"""
        pass


class TableNode(Node):

    """Node for table level elements"""
    table = None
    core_table = True
    extra_fields = []
    form_params =  {"form_type": "normal"}
    list_title = 'item %s'
    title_field = 'name'

    subforms = {}
    subform_data = {}
    subform_field_list = {}

    code_list = {}
    first_run = True

    list_fields = [
        input('title', data_type = 'link', control = link(css = 'form_title')),
        input('summarty', data_type = 'info', control = info()),
        input('edit', data_type = 'link_list', control = link_list()),
    ]

    list_params = {"form_type": "results"}


    def __init__(self, *args, **kw):
        super(TableNode, self).__init__(*args, **kw)
        self.setup_forms()
        if self.__class__.first_run:
            self.__class__.first_run = False
            self.setup_commands()
            self.setup_extra_commands()

    def setup_extra_commands(self):
        pass

    def setup_commands(self):
        commands = self.__class__.commands
        commands['view'] = dict(command = 'view')
        commands['list'] = dict(command = 'list')
        commands['edit'] = dict(command = 'edit')
        commands['_save'] = dict(command = 'save')
        commands['delete'] = dict(command = 'delete')
        commands['new'] = dict(command = 'new')

    def setup_forms(self):
        for field in self.fields:
            # add subform data
            if field.page_item_type == 'subform':
                name = field.name
                subform = self.__class__.subforms.get(name)
                data = self.create_form_data(subform.get('fields'), subform.get('params'))
                data['form']['parent_id'] =  subform.get('parent_id')
                data['form']['child_id'] =  subform.get('child_id')
                data['form']['table_name'] =  subform.get('table')
                data['control'] = 'subform'
                self.__class__.subform_data[name] = data
                field.subform = data
                self.setup_subforms(name)

    def setup_subforms(self, name):
        extra_fields = []
        for field in self.subforms.get(name).get('fields'):
            extra_fields.append(field.name)
        self.subform_field_list[name] = extra_fields


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
                obj = r.get_class(table)
                record_data = session.query(obj).filter_by(**filter).one()
            else:
                print 'new record'
                record_data = r.get_instance(table)
            for field in fields:
                print field
                field.save(self, record_data, data, session)

            # if this is a subform we need to update/add the join field
            # FIXME is this needed here or just for new?
            # maybe shift up a few lines to new record
            for field_name in join_fields:
                    value = data.get(field_name)
                    print 'join: %s = %s' % (field_name, value)
                    setattr(record_data, field_name, value)
            version = data.get("_version")
            if version:
                setattr(record_data, "_version", version)
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

        session = r.Session()
        id = self.data.get('id')
        root = self.data.get('__root')
        if id:
            filter = {'id' : id}
        else:
            filter = {}
        subform = self.data.get("__subform")
        if subform:
            child_id = self.subforms[subform]["child_id"]
            fields = self.subforms[subform]["fields"] + [input(child_id, data_type = "Integer")]
            table = self.subforms[subform]["table"]
        else:
            table = self.table
            fields = self.fields

        record_data = self.save_record(session, table, fields, self.data, filter, root)


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

    def new(self):

        data_out = {}
        data = self.create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'

    def edit(self):
        self.view(read_only = False)

    def view(self, read_only=True):
        id = self.data.get('id')
        if id:
            where = 'id=%s' % id
        else:
            id = self.data.get('__id')
            where = '_core_entity_id=%s' % id

        try:
            session = r.Session()
            obj = r.search_single(self.table, where, session = session)

            data_out = {}

            for field in self.fields:
                field.load(self, obj, data_out, session)

            for field in util.INTERNAL_FIELDS:
                extra_field = getattr(obj, field)
                if extra_field:
                    data_out[field] = util.convert_value(extra_field)

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
                ## FIXME look at logic to determining what data is sent
                if self.subforms[subform_name]["params"]["form_type"] != "action":
                    data_out[subform_name] = self.subform(subform_name, data_out)

        data = self.create_form_data(self.fields, self.form_params, data_out, read_only)
        self.out = data
        self.action = 'form'

        self.bookmark = dict(
            table_name = obj._table.name,
            bookmark_string = self.build_node('', 'view', 'id=%s' %  id),
            entity_id = id
        )


    def delete(self):
        assert 1 <> 1
        id = self.data.get('id')
        if id:
            filter = {'id' : id}
        else:
            id = self.data.get('__id')
            filter = {'_core_entity_id' : id}
        # FIXME i'd rather get this data ourself and not rely on the returned info
        table = self.data.get('table_name', self.table)

        session = r.Session()
        obj = r.get_class(table)
        try:
            data = session.query(obj).filter_by(**filter).one()
            # see if fields have special delete
            for field in self.fields:
                field.delete(self, data, data, session)

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
        limit = self.get_data_int('l', limit)
        offset = self.get_data_int('o')

        if r[self.table].entity:
            results = r.search('_core_entity',
                                        where = "%s.id >0" % self.table,
                                        limit = limit,
                                        offset = offset,
                                        count = True)
        else:
            results = r.search(self.table,
                                        where = "id >0",
                                        limit = limit,
                                        offset = offset,
                                        count = True)

        data = results['data']
        # build the links
        if r[self.table].entity:
            for row in data:
                row['title'] = self.build_node(row['title'], 'edit', '__id=%s' % row['id'])
                row['edit'] = [self.build_node('Edit', 'edit', '__id=%s' % row['id']),
                               self.build_node('Delete', '_delete', '__id=%s' % row['id']),
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

                row['edit'] = [self.build_node('Edit', 'edit', 'id=%s' % row['id']),
                               self.build_node('Delete', '_delete', 'id=%s' % row['id']),
                              ]
        data = {'__array' : data}
        out = self.create_form_data(self.list_fields, self.list_params, data)

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
            out = r.search(table, where, fields = field_list)["data"]
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
        obj = r.get_instance(self.table)
        columns = obj._table.schema_info
        for field in columns.keys():
            if field not in ['_modified_date', '_modified_by']:
                fields.append([field, 'Text', '%s:' % field])
        self.__class__.fields = fields





