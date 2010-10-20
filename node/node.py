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
import logging
import datetime

import authenticate
import database.util as util
import custom_exceptions
from web.global_session import global_session
from page_item import info, input, textarea, result_link
from form import form, FormFactory

r = global_session.database

log = logging.getLogger('rebase.node')





class Node(object):

    permissions = []
    commands = {}

    first_run = True # used for setting up commands etc

    static = True # If True the node is thread safe

    table = None # forms need this defined

    def __init__(self, node_name = None):

        # FIXME can this die?
        self.name = node_name

        self.volatile = False # set to True if forms are volatile

        self.extra_data = {}

        # do any command setup
        if self.__class__.first_run:
            # initiate any forms
            self.__class__._forms = {}
            self.__class__._available_forms = {}
            self.__class__._non_result_forms = {}
            self.__class__._result_forms = {}
            self.initiate_forms()

            self.__class__.first_run = False
            self.setup_commands()
            # TD do we need this?
            self.setup_extra_commands()

    def __repr__(self):
        return '<Node `%s`>' % self.name

    def initiate_forms(self):
        # find all the form in this node
        # add them to _available_forms so they can
        # easily be generated when needed
        for form_name in dir(self):
            if isinstance(getattr(self, form_name), FormFactory):
                formwrapper = getattr(self, form_name)
                self._available_forms[form_name] = formwrapper
                # store list of non-result forms
                if formwrapper.kw.get('form_type') != 'results':
                    self._non_result_forms[form_name] = formwrapper
                else:
                    self._result_forms[form_name] = formwrapper


    def setup_commands(self):
        pass

    def setup_extra_commands(self):
        pass

    def __getitem__(self, form_name):
        """See if we have a form of this name and if so return it"""

        # return form if it is cached
        if form_name in self._forms:
            return self._forms[form_name]

        # not cached do we know this form if so build it
        if form_name in self._available_forms:
            form = self._available_forms[form_name](form_name, self)
            if not form.volatile:
                # cache form
                self._forms[form_name] = form
            return form

        raise Exception('Form with name `%s` does not exist in this node.' % form_name)

    def get_form_name_list(self):
        """returns the names of all the non-result forms available to the node"""
        return self._non_result_forms.keys()

    def get_result_form_name_list(self):
        """returns the names of all the non-result forms available to the node"""
        return self._result_forms.keys()

    def get_form_name_list_from_layout(self):
        if self.form_layout:
            # we have a layout so let's use it to get the form data
            form_names = []
            for section in self.form_layout:
                form_names.extend(section)
            return form_names
        else:
            # just return the forms we have
            return self.get_form_name_list()


    def call(self, node_token):
        """called when the node is used.  Checks to see if there
        is a function to call for the given command"""

        # first check if the command is available
        command_info = self.commands.get(node_token.command)
        if not command_info:
            return
        # check we have the needed permissions
        if command_info.get('permissions'):
            if not authenticate.check_permission(command_info.get('permissions')):
                node_token.forbidden()
                print 'forbidden'
                return

        command = command_info.get('command')

        if command:
            command = getattr(self, command)
            command(node_token)
        else:
            error = "Command '%s' in node '%s' not known" % (node_token.command, self.name)
            node_token.general_error(error)

    def check_permissions(self):
        return authenticate.check_permission(self.permissions)


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



    def update_bookmarks(self, node_token):
        user_id = global_session.session['user_id']
        impersonating = global_session.session['impersonating']
        # only update bookmarks for proper users
        if user_id and not impersonating:
            try:
                result = r.search_single_data("bookmarks",
                                         "user_id = ? and bookmark = ?",
                                         fields = ['title', 'bookmark', 'entity_table', 'entity_id', 'accessed_date'],
                                         values = [user_id, node_token.bookmark["bookmark_string"]])
                result["accessed_date"] = util.convert_value(datetime.datetime.now())
                result["title"] = node_token.title
            except custom_exceptions.SingleResultError:
                result = {"__table": "bookmarks",
                          "entity_id": node_token.bookmark["entity_id"],
                          "user_id": user_id,
                          "title": node_token.get_title(),
                          "entity_table": node_token.bookmark["table_name"],
                          "accessed_date": util.convert_value(datetime.datetime.now())}
            # save
            util.load_local_data(r, result)

        else:
            # anonymous user
            result = {"entity_id": node_token.bookmark["entity_id"],
                      "title": node_token.get_title(),
                      "entity_table": node_token.bookmark["table_name"],
                      "accessed_date": util.convert_value(datetime.datetime.now())}

        # update bookmark output to front-end
        node_token.bookmark = result




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

    def finish_node_processing(self, node_token):

        if node_token.bookmark and node_token.bookmark != 'CLEAR':
            self.update_bookmarks(node_token)

    def initialise(self, node_token):
        """called first when the node is used"""
        pass

    def finalise(self, node_token):
        """called last when node is used"""
        pass


class TableNode(Node):

    """Node for table level elements"""

    table = None
    core_table = True
    extra_fields = []
    list_title = 'item %s'
    title_field = 'name'

    listing = form(
        result_link('title'),
        info('summary', data_type = 'info'),
        form_type = "results",
        layout_title = "results",
    )


    form_layout = None
    layout_main_form = 'main'

    def setup_commands(self):
        commands = {}
     #   commands['view'] = dict(command = 'view')
        commands['list'] = dict(command = 'list')
        commands['edit'] = dict(command = 'edit')
        commands['_save'] = dict(command = 'save')
        commands['_delete'] = dict(command = 'delete')
        commands['new'] = dict(command = 'new')
        commands['_update'] = dict(command = 'update')
        self.__class__.commands = commands


    def list(self, node_token, limit=20):
        for form_name in self.get_result_form_name_list():
            form = self[form_name]
            form.list(node_token, limit)

    def edit(self, node_token):
        # process each of the forms
        for form_name in self.get_form_name_list_from_layout():
            self[form_name].view(node_token, read_only = False)
        # add the layout information
        if  self.form_layout:
            node_token.set_layout(self.layout_type, self.form_layout)

    def save(self, node_token):
        for form_name in node_token.form_tokens():
            self[form_name].save(node_token)

    def update(self, node_token):
        for form_name in node_token.form_tokens():
            self[form_name].view(node_token, read_only = False)

    def new(self, node_token):
        if node_token.form_tokens():
            for form_name in node_token.form_tokens():
                self[form_name].new(node_token)
        else:
            for form_name in self.get_form_name_list_from_layout():
                self[form_name].new(node_token)

    def delete(self, node_token):
        for form_name in node_token.form_tokens():
            self[form_name].delete(node_token)


class EntityNode(TableNode):
    layout_type = 'entity'


class JobNode(Node):

    """Job nodes send a job to the processer and allow the job to be monitored"""

    job_type = None
    job_function = None
    params = []
    base_params = {}

    table = '_core_job_scheduler'

    def setup_commands(self):
        commands = {}
        commands['load'] = dict(command = 'load')
        commands['refresh'] = dict(command = 'refresh')
        commands['_status'] = dict(command = 'status')
        self.__class__.commands = commands

    def load(self, node_token, form_name = None):

        # add the job to the scheduler

        # build up the parameters to pass
        params = self.base_params.copy()
        if form_name:
            node_data = node_token[form_name]
        else:
            node_data = node_token.get_node_data()

        for param in self.params:
            params[param] = node_data.get(param)
        jobId = global_session.application.job_scheduler.add_job(self.job_type, self.job_function, **params)
        redirect = "%s:refresh?id=%s" % (self.name, jobId)
        node_token.redirect(redirect)


    def refresh(self, node_token):
        # TD does this need to be different from status? can we combine?
        node_data = node_token.get_node_data()
        jobId = node_data.get('id')
        node_token.status(dict(data = self.get_status(jobId), form = True))
        node_token.set_node_data(dict(id = jobId))

    def status(self, node_token):
        # report the status of the job
        node_data = node_token.get_node_data()
        jobId = node_data.get('id')
        node_token.status(dict(data = self.get_status(jobId)))



    def get_status(self, jobId):
        data_out = r.search_single_data(self.table, where = "id=%s" % jobId)
        status_data = dict(id = jobId,
                   start = data_out['job_started'],
                   message = data_out['message'],
                   percent = data_out['percent'],
                   end = data_out['job_ended'])
        return status_data



class AutoForm(TableNode):

    def __init__(self, node_name):
        super(AutoForm, self).__init__(node_name)

        rtable = r[self.table]

        self.extra_data = {'table':self.table}

        title_field = rtable.title_field

        fields = []

        for field in rtable.ordered_fields:
            if field.category <> "field":
                continue

            extra_info = {}
            if field.description:
                extra_info['description'] = field.description

            if field.type == "Text" and field.length > 500:
                fields.append(textarea(field.name, css = "large", **extra_info))
            else:
                fields.append(input(field.name, **extra_info))

        main = form(*fields, table = self.table, params = self.form_params, volatile = True)
        # add this to the available forms
        self._available_forms['main'] = main


class AutoFormPlus(TableNode):

    def initialise(self, node_token):
        node_data = node_token.get_node_data()
        table = node_data.get('table', '')

        table = table.encode('ascii')
        # This seems to be needed but I'm not sure why
        # but without it the listings are incorrect.
        # TODO investigate a little
        self.table = table
        rtable = r[table]

        self.extra_data = {'table':table}

        title_field = rtable.title_field

        fields = []

        for field in rtable.ordered_fields:
            if field.category <> "field":
                continue

            extra_info = {}
            if field.description:
                extra_info['description'] = field.description

            if field.type == "Text" and field.length > 500:
                fields.append(textarea(field.name, css = "large", **extra_info))
            else:
                fields.append(input(field.name, **extra_info))

        main = form(*fields, table = table, form_type = 'input', volatile = True)
        # add this to the available forms
        self._available_forms['main'] = main
