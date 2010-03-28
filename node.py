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
from form import form, Form
r = global_session.database

class Node(object):

    permissions = []
    commands = {}

    def __init__(self, data, node_name, prev_node = None):

        self.name = node_name

        self._forms = {}
        for form_name in dir(self):
            if isinstance(getattr(self, form_name), Form):
                form = getattr(self, form_name)
                form.set_name(form_name)
                form.set_node(self)
                self._forms[form_name] = form

        self.out = []
        self.title = None
        self.link = None

        self.action = None
        self.bookmark = None
        self.user = None
        self.next_node = None
        self.next_data = None
        self.next_data_out = None
        self.extra_data = {}
        self.command = data.get('command')
        self.allowed = self.check_permissions()
        self.prev_node = prev_node
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

    def __getitem__(self, value):
        return self._forms[value]

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


    def set_form_message(self, message):
        """Sets the button info to be displayed by a form."""
        self.out['data']['__message'] = message

    def set_form_buttons(self, button_list):
        """Sets the button info to be displayed by a form."""
        if not self.out.get('data'):
            self.out["data"] = {}

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

    first_run = True

    listing = form(
        link('title', data_type = 'link', css = 'form_title'),
        info('summary', data_type = 'info'),
        link_list('edit', data_type = 'link_list'),

        params = {"form_type": "results"}
    )


    def __init__(self, *args, **kw):
        super(TableNode, self).__init__(*args, **kw)
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

    def save(self):
        self["main"].save()

    def new(self):
        self["main"].new()

    def edit(self):
        self["main"].view(read_only = False)

    def view(self, read_only=True):
        self["main"].view(read_only)

    def delete(self):
        self["main"].delete()

    def list(self, limit=20):
        self["main"].list(limit)



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





