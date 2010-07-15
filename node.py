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

import authenticate
import reformed.util as util
from reformed import custom_exceptions
import datetime
from global_session import global_session
from page_item import result_image, info, input, textarea, result_link
from form import form, FormFactory
import logging
r = global_session.database

log = logging.getLogger('rebase.node')





class Node(object):

    permissions = []
    commands = {}

    first_run = True # used for setting up commands etc

    static = True # If True the node is thread safe

    table = None # forms need this defined

    def __init__(self, node_name):

        # FIXME can this die?
        self.name = node_name

        # TD prepare the forms.  ? does this need doing for all the forms
        # or can we take a more lazy approach?
        self._forms = {}
        self.volatile = False # set to True if forms are volatile

        self.extra_data = {}

        # initiate forms
        for form_name in dir(self):
            if isinstance(getattr(self, form_name), FormFactory):
                formwrapper = getattr(self, form_name)
                # this is where we get the form initialised
                form = formwrapper(form_name, self)
                if form.volatile:
                    self.volatile = True

                self._forms[form_name] = form

        # do any command setup
        if self.__class__.first_run:
            self.__class__.first_run = False
            self.setup_commands()
            # TD do we need this?
            self.setup_extra_commands()

    def setup_commands(self):
        pass

    def setup_extra_commands(self):
        pass

    def __getitem__(self, value):
        return self._forms[value]

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
                node_token.action = 'forbidden'
                node_token.command = None
                print 'forbidden'
                return

        command = command_info.get('command')

        if command:
            command = getattr(self, command)
            command(node_token)
        else:
            node_token.action = 'general_error'
            node_token.out = "Command '%s' in node '%s' not known" % (node_token.command, self.name)

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

        # only update bookmarks for proper users
        if user_id:
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
                          "title": node_token.title,
                          "entity_table": node_token.bookmark["table_name"],
                          "accessed_date": util.convert_value(datetime.datetime.now())}
            # save
            util.load_local_data(r, result)

        else:
            # anonymous user
            result = {"entity_id": node_token.bookmark["entity_id"],
                      "title": node_token.title,
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
    form_params =  {"form_type": "normal"}
    list_title = 'item %s'
    title_field = 'name'


    listing = form(
        #link('title', data_type = 'link', css = 'form_title'),
        result_link('title'),
        #result_image('thumb'),
        info('summary', data_type = 'info'),
  #      link_list('edit', data_type = 'link_list'),

        params = {"form_type": "results"}
    )




    def setup_commands(self):
        commands = self.__class__.commands
        commands['view'] = dict(command = 'view')
        commands['list'] = dict(command = 'list')
        commands['edit'] = dict(command = 'edit')
        commands['_save'] = dict(command = 'save')
        commands['delete'] = dict(command = 'delete')
        commands['new'] = dict(command = 'new')

    def save(self, node_token):
        self["main"].save(node_token)

    def new(self, node_token):
        self["main"].new(node_token)

    def edit(self, node_token):
        self["main"].view(node_token, read_only = False)

    def view(self, node_token, read_only=True):
        self["main"].view(node_token, read_only)

    def delete(self, node_token):
        self["main"].delete(node_token, node_token)

    def list(self, node_token, limit=20):
        self["main"].list(node_token, limit)


class JobNode(Node):

    """Job nodes send a job to the processer and allow the job to be monitored"""

    job_type = None
    job_function = None
    params = []
    base_params = {}

    table = '_core_job_scheduler'

    def setup_commands(self):
        commands = self.__class__.commands
        commands['load'] = dict(command = 'load')
        commands['refresh'] = dict(command = 'refresh')
        commands['status'] = dict(command = 'status')

    def load(self, node_token):

        # add the job to the scheduler

        # build up the parameters to pass
        params = self.base_params.copy()
        for param in self.params:
            params[param] = node_token.data.get(param)
        jobId = global_session.application.job_scheduler.add_job(self.job_type, self.job_function, **params)
        node_token.link = "%s:refresh:id=%s" % (self.name, jobId)
        node_token.action = 'redirect'


    def refresh(self, node_token):
        # TD does this need to be different from status? can we combine?
        jobId = node_token.data.get('id')
        node_token.out = dict(data = self.get_status(jobId), form = True)
        node_token.action = 'status'
        print 'status'
        # ??
     #   node_token.title = "job %s" % jobId

    def status(self, node_token):
        # report the status of the job
        jobId = node_token.data.get('id')
        node_token.out = dict(data = self.get_status(jobId))
        node_token.action = 'status'



    def get_status(self, jobId):
        data_out = r.search_single_data(self.table, where = "id=%s" % jobId)
        out = dict(id = jobId,
                   start = data_out['job_started'],
                   message = data_out['message'],
                   percent = data_out['percent'],
                   end = data_out['job_ended'])
        return out



class AutoForm(TableNode):

    def initialise(self, node_token):

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

        main = form(*fields, table = self.table, params = self.form_params)
        self._forms["main"] = main("main", self)




