from node import TableNode

class Ticket(TableNode):

    table = "ticket"
    form_params =  {"form_type": "action"}
    title_field = 'title'

    fields = [
        ['title', 'Text', 'title:'],
        ['', '', '', dict(layout = 'hr')],
        ['', '', '', dict(layout = 'column_start')],
        ['accepted', 'Boolean', 'accepted:', {"control" : "dropdown", "autocomplete" : ["true", "false"]}],
        ['complete_by', 'Date', 'complete by:'],
        ['', '', '', dict(layout = 'column_next')],
        ['severity', 'Text', 'severity:', {"control" : "dropdown", "autocomplete" : True}],
        ['priority_id', 'Integer', 'priority:', {"control" : "dropdown_code", "autocomplete" : True}],
        ['', '', '', dict(layout = 'column_end')],
        ['', '', '', dict(layout = 'hr')],
        ['summary', 'Text', 'summary:', {"control" : "textarea", "css" : "large"}],
        ['', '', 'add ticket', {'control' : 'button', 'node': 'bug.Ticket:_save:'}]
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
        ['title', 'Text', 'title:'],
        ['accepted', 'Boolean', 'accepted:', {"control" : "dropdown", "autocomplete" : ["true", "false"]}],
        ['complete_by', 'Date', 'complete by:'],
        ['summary', 'Text', 'summary:', {"control" : "textarea", "css" : "large"}],
        ['severity', 'Text', 'severity:', {"control" : "dropdown", "autocomplete" : True}],
        ['priority_id', 'Integer', 'priority:', {"control" : "dropdown_code", "autocomplete" : True}],
        ['old_comments', 'subform', 'old_comments'],
        ['comment', 'subform', 'comment']
    ]

    subforms = {
        'old_comments':{
            'fields': [
                ['created_date', 'DateTime', 'Date Created: '],
                ['note', 'Text', '', {"control" : "textarea", "css" : "large"}],
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
                ['note', 'Text', 'note:', {"control" : "textarea", "css" : "large"}],
                ['moo', 'Boolean', 'moo:', {"control" : "checkbox"}],
                ['', '', 'add comment', {'control' : 'button', 'node': 'bug.ListTicket:_save:'}]
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
        ['name', 'Text', 'name:'],
        ['login_name', 'Text', 'login name:'],
        ['active', 'Boolean', 'active:', {"control" : "checkbox"}],
        ['password', 'Text', 'password:', {"control" : "password"}],
        ['password2', 'Text', 'confirm password:', {"control" : "password"}],
        ['email', 'Text', 'email:'],
        ['notes', 'Text', 'notes:', {"control" : "textarea", "css" : "large"}],
        ['', '', 'add user', {'control' : 'button', 'node': 'bug.User:_save:'}],
    ]


class Permission(TableNode):

    table = "permission"
    form_params =  {"form_type": "action"}
    title_field = 'permission'
    fields = [
        ['message', '', '', {'control' : 'html'}],
        ['', '', '', dict(layout = 'box_start')],
        ['permission', 'Text', 'permission:'],
        ['description', 'Text', 'description:', {"control" : "textarea", "css" : "large"}],
        ['', '', '', {'control' : 'button_box',
             'buttons' : [['add permission', 'bug.Permission:_save:'], ['cancel', 'BACK']]}],
    ]

    def finalise(self):
        if self.command == '_save' and self.saved:
            message = "Permission <b>%s</b> saved!  Add more?" % self.data['permission']
            self.out = self.create_form_data(self.fields, self.form_params)
            self.action = 'form'
        if self.command == 'new':
            message = "Hello, add new permissions below"
        if message:
            self.out['data']['message'] = message
        print self.out

class UserGroup(TableNode):

    table = "user_group"
    form_params =  {"form_type": "action"}
    title_field = 'user group'
    fields = [
        ['message', '', '', {'control' : 'html'}],
        ['', '', '', dict(layout = 'box_start')],
        ['groupname', 'Text', 'groupname:'],
        ['active', 'Boolean', 'active:', {'control' : 'checkbox'}],
        ['notes', 'Text', 'notes:', {"control" : "textarea", "css" : "large"}],
        ['', '', '', dict(layout = 'box_start')],
        ['permission', 'code_group', 'permission:', {'control' : 'codegroup'}],
        ['', '', '', dict(layout = 'box_end')],
        ['', '', '', {'control' : 'button_box',
             'buttons' : [['add user group', 'bug.UserGroup:_save:'], ['cancel', 'BACK']]}],
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
        message = None
        if self.command == '_save' and self.saved:
            message = "user group <b>%s</b> saved!  Add more?" % self.data['groupname']
            self.out = self.create_form_data(self.fields, self.form_params)
            self.action = 'form'
        if self.command == 'new':
            message = "Hello, add new user group below"
        if self.command == 'edit':
            message = "Hello, edit %s new user group below" % self.out['data']['groupname']
            self.out['form']['fields'][8]['params']['buttons'][0][0] = 'save changes'
        if message:
            self.out['data']['message'] = message
