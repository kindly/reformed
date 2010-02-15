from node import TableNode
from page_item import *

class Ticket(TableNode):

    table = "ticket"
    form_params =  {"form_type": "action"}
    title_field = 'title'

    fields = [
        input('title', data_type = 'Text'),
        layout('hr'),
        layout('column_start'),
        input('accepted', data_type = 'Boolean' , control = dropdown(["true", "false"])),
        input('complete_by', data_type = 'Date'),
        layout('column_next'),
        input('severity', data_type = 'Text' , control = dropdown(True)),
        input('priority_id', data_type = 'Integer' , control = dropdown(True)),
        layout('column_end'),
        layout('hr'),
        input('summary', data_type = 'Text' , control = textarea(css = "large")),
    ]
    list_title = 'ticket %s'

    def view(self, read_only = False):

        self.next_node = "bug.ListTicket"
        self.next_data = dict(data = self.data,
                              command = "view")

class ListTicket(TableNode):

    table = "ticket"
    form_params =  {"form_type": "normal"}
    title_field = 'title'

    fields = [
        input('title', data_type = 'Text'),
        input('accepted', data_type = 'Boolean' , control = dropdown(["true", "false"])),
        input('complete_by', data_type = 'Date'),
        input('summary', data_type = 'Text' , control = textarea(css = "large")),
        input('severity', data_type = 'Text' , control = dropdown(True)),
        input('priority_id', data_type = 'Integer' , control = dropdown(True)),
        subform('old_comments'),
        subform('comment'),
    ]

    subforms = {
        'old_comments':{
            'fields': [
                input('created_date', data_type = 'DateTime'),
                input('note', data_type = 'Text' , control = textarea(css = "large")),
            ],
            "parent_id": "_core_entity_id",
            "child_id": "_core_entity_id",
            "table": "comment",
            "params":{
                "form_type": "continuous"
            }
        },

        'comment':{
            'fields': [
                input('note', data_type = 'Text' , control = textarea(css = "large")),
                input('moo', data_type = 'Boolean' , control = checkbox()),
                input(label = 'add comment', control = button(node = 'bug.ListTicket:_save:')),
            ],
            "parent_id": "_core_entity_id",
            "child_id": "_core_entity_id",
            "table": "comment",
            "params":{
                "form_type": "action"
            }
        }
    }

    list_title = 'ticket %s'

    def save(self):

        super(ListTicket, self).save()
        self.action = "redirect"
        print "-&"*5, self.data
        self.link = "bug.ListTicket:view:__id=%s" % self.data.get("_core_entity_id")

class User(TableNode):

    table = "user"
    form_params =  {"form_type": "action"}
    title_field = 'name'

    fields = [
        ['', '', '', dict(layout = 'text', text = 'user..........')],
        ['', '', '', dict(layout = 'column_start')],
        ['name', 'Text', 'name:'],
        ['login_name', 'Text', 'login name:'],
        ['active', 'Boolean', 'active:', {"control" : "checkbox"}],
        ['email', 'Text', 'email:'],
        ['', '', '', dict(layout = 'column_next')],
        ['', '', '', dict(layout = 'box_start')],
        ['password', 'Text', 'password:', {"control" : "password"}],
        ['password2', 'Text', 'confirm password:', {"control" : "password"}],
        ['', '', '', dict(layout = 'box_end')],
        ['', '', '', dict(layout = 'column_end')],
        ['', '', '', dict(layout = 'hr')],
        ['notes', 'Text', 'notes:', {"control" : "textarea", "css" : "large"}],
        ['', '', '', dict(layout = 'spacer')],
        ['', '', '', dict(layout = 'box_start')],
        ['usergroup', 'code_group', 'usergroup:', {'control' : 'codegroup'}],
        ['', '', '', dict(layout = 'box_end')],
        ['', '', '', dict(layout = 'spacer')],
    ]


    code_groups = {'usergroup':{
                                    'code_table': 'user_group',
                                    'code_field': 'id',
                                    'code_desc_field': 'notes',
                                    'code_title_field': 'groupname',
                                    'flag_table': 'user_group_user',
                                    'flag_child_field': 'user_id',
                                    'flag_code_field': 'user_group_id',
                                    'flag_parent_field': 'id'
                                  }
                }
    def finalise(self):
        if self.command == '_save' and self.saved:
            if self.data.get('id',0) == 0:
                self.out = self.create_form_data(self.fields, self.form_params)
                self.set_form_message("User %s saved!  Add more?" % self.data.get('name'))
                self.action = 'form'
                self.set_form_buttons([['add user', 'bug.User:_save:'], ['cancel', 'BACK']])
            else:
                self.action = 'redirect'
                self.link = 'BACK'
        if self.command == 'new':
            self.set_form_message("Add new user below")
            self.set_form_buttons([['add user', 'bug.User:_save:'], ['cancel', 'BACK']])
        if self.command == 'edit':
            self.set_form_message("Edit {name}")
            self.set_form_buttons([['add user', 'bug.User:_save:'], ['delete user', 'bug.User:_delete:'], ['cancel', 'BACK']])

class Permission(TableNode):

    table = "permission"
    form_params =  {"form_type": "action"}
    title_field = 'permission'
    fields = [
        ['', '', '', dict(layout = 'box_start')],
        ['permission', 'Text', 'permission:'],
        ['description', 'Text', 'description:'],
        ['long_description', 'Text', 'long description:', {"control" : "textarea", "css" : "large"}],
    ]

    def finalise(self):
        if self.command == '_save' and self.saved:
            if self.data.get('id',0) == 0:
                self.out = self.create_form_data(self.fields, self.form_params)
                self.set_form_message("Permission %s saved!  Add more?" % self.data.get('permission'))
                self.action = 'form'
                self.set_form_buttons([['add permission', 'bug.Permission:_save:'], ['cancel', 'BACK']])
            else:
                self.action = 'redirect'
                self.link = 'BACK'
        if self.command == 'new':
            self.set_form_message("Hello, add new permission")
            self.set_form_buttons([['add permission', 'bug.Permission:_save:'], ['cancel', 'BACK']])
        if self.command == 'edit':
            self.set_form_message("Hello, edit [b]{permission}[/b]")
            self.set_form_buttons([['save permission', 'bug.Permission:_save:'], ['delete permission', 'bug.Permission:_delete:'], ['cancel', 'BACK']])


class UserGroup(TableNode):

    table = "user_group"
    form_params =  {"form_type": "action"}
    title_field = 'user group'
    fields = [
        ['', '', '', dict(layout = 'box_start')],
        ['groupname', 'Text', 'groupname:', {'description' : 'The name of the user group'}],
        ['active', 'Boolean', 'active:', {'control' : 'checkbox', 'description' : 'Only active user groups give members permissions'}],
        ['description', 'Text', 'description:', {'description' : 'A brief description of the user group'}],
        ['notes', 'Text', 'notes:', {"control" : "textarea", "css" : "large", 'description' : 'A longer more detailed description'}],
        ['', '', '', dict(layout = 'spacer')],
        ['', '', '', dict(layout = 'box_start')],
        ['permission', 'code_group', 'permission:', {'control' : 'codegroup'}],
        ['', '', '', dict(layout = 'box_end')],
        ['', '', '', dict(layout = 'spacer')],
    ]

    code_groups = {'permission':{
                                    'code_table': 'permission',
                                    'code_field': 'id',
                                    'code_desc_field': 'description',
                                    'code_title_field': 'permission',
                                    'flag_table': 'user_group_permission',
                                    'flag_child_field': 'user_group_id',
                                    'flag_code_field': 'permission_id',
                                    'flag_parent_field': 'id'
                                  }
                    }

    def finalise(self):
        if self.command == '_save' and self.saved:
            if self.data.get('id',0) == 0:
                self.out = self.create_form_data(self.fields, self.form_params)
                self.set_form_message("User group %s saved!  Add more?" % self.data.get('groupname'))
                self.set_form_buttons([['save user group', 'bug.UserGroup:_save:'], ['cancel', 'BACK']])
                self.action = 'form'
            else:
                self.action = 'redirect'
                self.link = 'BACK'
        if self.command == 'new':
            self.set_form_message("Add new user group below")
            self.set_form_buttons([['save user group', 'bug.UserGroup:_save:'], ['cancel', 'BACK']])
        if self.command == 'edit':
            self.set_form_message("Edit {groupname}")
            self.set_form_buttons([['save user group', 'bug.UserGroup:_save:'], ['delete user group', 'bug.UserGroup:_delete:'], ['cancel', 'BACK']])
