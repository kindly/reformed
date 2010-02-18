from node import TableNode
from formencode import validators
from page_item import *
import reformed.search
from global_session import global_session
r = global_session.database

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
                                    'code_desc_field': 'description',
                                    'code_title_field': 'groupname',
                                    'flag_table': 'user_group_user',
                                    'flag_child_field': 'user_id',
                                    'flag_code_field': 'user_group_id',
                                    'flag_parent_field': 'id'
                                  }
                }



    login_fields = [
        ['', '', '', dict(layout = 'box_start')],
        ['login_name', 'Text', 'username:'],
        ['password', 'password', 'password:', dict(control = 'password')],
        ['button', 'submit', 'Log in', {'control' : 'button', 'node': 'bug.User:login:'}],
        ['', '', '', dict(layout = 'box_end')],
    ]
    login_form_params =  {"form_type": "action"}
    login_validations = [
        ['login_name', validators.UnicodeString],
        ['password', validators.UnicodeString]
    ]

    about_me_fields = [
        ['', '', '', dict(layout = 'box_start')],
        ['login_name', 'Text', 'username:'],
        ['about_me', 'Text', 'notes:', {"control" : "textarea", "css" : "large"}],
        ['', '', '', dict(layout = 'box_end')],
    ]
    about_me_form_params =  {"form_type": "action"}

    about_me_form_fields = ['login_name', 'about_me']

    def setup_extra_commands(self):
        commands = self.__class__.commands
        commands['login'] = dict(command = 'check_login')
        commands['logout'] = dict(command = 'logout')
        commands['about_me'] = dict(command = 'about_me', permissions = ['logged_in'])
        commands['_save_about_me'] = dict(command = 'save_about_me')

    def check_login(self):
        message = None
        vdata = self.validate_data_full(self.data, self.login_validations)
        if vdata['login_name'] and vdata['password']:
            where = "login_name='%s' and password='%s'" % (vdata['login_name'], vdata['password'])
            try:
                data_out = r.search_single('user', where)
                if data_out.get('active') != True:
                    message = dict(title = 'Login failed', body ='This account is disabled.')
                    self.show_login_form(message)
                else:

                    result = r.search('permission', 'user_group_user.user_id = %s and permission="Login"' % data_out.get('id'), fields=['permission'])['data']
                    if not result:
                        message = dict(title = 'Login failed', body ='This account is not allowed to log into the system.')
                        self.show_login_form(message)
                    else:
                        self.login(data_out)

            except:
                message = dict(title = 'Login failed', body ='user name or password incorrect, try again.', type = 'error')
                self.show_login_form(message)
        else:
            message = dict(title = 'Login.', body ='Welcome to %s enter your login details to continue' % global_session.application['name'])
            self.show_login_form(message)

    def show_login_form(self, message = None):
        if message:
            data = dict(__message = message)
        else:
            data = {}
        out = self.create_form_data(self.login_fields, self.login_form_params, data)
        self.action = 'form'
        self.out = out

    def about_me(self):
        where = 'id = %s' % global_session.session['user_id']
        data = r.search_single('user', where, fields = self.about_me_form_fields, keep_all = True)
        out = self.create_form_data(self.about_me_fields, self.about_me_form_params, data)
        self.action = 'form'
        self.out = out

    def save_about_me(self):
        self.saved = []
        self.errors = {}
        session = r.Session()
        filter = dict(id =  global_session.session['user_id'])
        data = self.data
        self.save_record(session, 'user', self.about_me_fields, data, filter, None)
        session.close()
        # output data
        out = {}
        if self.errors:
            out['errors'] = self.errors
            self.out = out
            self.action = 'save'
        else:
            self.action = 'redirect'
            self.link = 'BACK'

    def login(self, data):
        user_id = data.get('id')
        username = data.get('login_name')
        global_session.session['user_id'] = user_id
        global_session.session['username'] = username

        global_session.session['permissions'] = self.get_permissions(user_id)#['logged_in']

        user_name = data.get('name')
        user_id = data.get('id')
        self.user = dict(name = user_name, id = user_id)

        self.action = 'html'
        data = "<p>Hello %s you are now logged in, what fun!</p>" % data['name']
        self.out = {'html': data}

    def get_permissions(self, user_id):

        result = r.search('permission', 'user_group_user.user_id = %s' % user_id, fields=['permission'])['data']
        permissions = ['logged_in']
        for row in result:
            print row
            permissions.append(row.get('permission'))
        print permissions
        return permissions

    def logout(self):
        global_session.session['user_id'] = 0
        global_session.session['username'] = ''
        global_session.session['permissions'] = []

        self.user = dict(name = None, id = 0)
        message = dict(title = "You are now logged out", body = '')
        self.show_login_form(message)
        # clear bookmarks
        self.bookmark = 'CLEAR'

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
        if self.command == 'list':
            self.set_form_message("These are the current users.")
            self.set_form_buttons([['add new user', 'bug.User:new:'], ['cancel', 'BACK']])
        if self.command == 'about_me':
            self.set_form_message("About Me")
            self.set_form_buttons([['Save Changes', 'bug.User:_save_about_me:'], ['cancel', 'BACK']])
        if self.command == 'new':
            self.set_form_message("Add new user below")
            self.set_form_buttons([['add user', 'bug.User:_save:'], ['cancel', 'BACK']])
        if self.command == 'edit':
            self.set_form_message("Edit {name}")
            self.set_form_buttons([['Save Changes', 'bug.User:_save:'], ['delete user', 'bug.User:_delete:'], ['cancel', 'BACK']])

class Permission(TableNode):

    table = "permission"
    form_params =  {"form_type": "action"}
    title_field = 'permission'
    fields = [
        ['', '', '', dict(layout = 'box_start')],
        ['permission', 'Text', 'permission:'],
        ['description', 'Text', 'description:', {"css" : "large"}],
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
        if self.command == 'list':
            self.set_form_message("These are the current permissions.")
            self.set_form_buttons([['add new permission', 'bug.Permission:new'], ['cancel', 'BACK']])
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
        ['description', 'Text', 'description:', {'description' : 'A brief description of the user group', "css" : "large"}],
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
        if self.command == 'list':
            self.set_form_message("These are the current user groups.")
            self.set_form_buttons([['add new permission', 'bug.UserGroup:new'], ['cancel', 'BACK']])
        if self.command == 'new':
            self.set_form_message("Add new user group below")
            self.set_form_buttons([['save user group', 'bug.UserGroup:_save:'], ['cancel', 'BACK']])
        if self.command == 'edit':
            self.set_form_message("Edit {groupname}")
            self.set_form_buttons([['save user group', 'bug.UserGroup:_save:'], ['delete user group', 'bug.UserGroup:_delete:'], ['cancel', 'BACK']])


class UserAdmin(TableNode):

    permissions = ['logged_in']

    form_params =  {"form_type": "action"}
    fields = [
        ['', '', '', dict(layout = 'text', text = 'Users {users}')],
        ['', '', 'add user', dict(control = 'button_link', node = 'bug.User:new')],
        ['', '', 'list users', dict(control = 'button_link', node = 'bug.User:list')],
        ['', '', '', dict(layout = 'spacer')],
        ['', '', '', dict(layout = 'text', text = 'User Groups {user_groups}')],
        ['', '', 'add user group', dict(control = 'button_link', node = 'bug.UserGroup:new')],
        ['', '', 'list user groups', dict(control = 'button_link', node = 'bug.UserGroup:list')],
        ['', '', '', dict(layout = 'spacer')],
        ['', '', '', dict(layout = 'text', text = 'Permissions {permissions}')],
        ['', '', 'add permission', dict(control = 'button_link', node = 'bug.Permission:new')],
        ['', '', 'list permissions', dict(control = 'button_link', node = 'bug.Permission:list')],
        ['', '', '', dict(layout = 'spacer')],
    ]

    def call(self):
        session = r.Session()
        users = reformed.search.Search(r, 'user', session).search().count()
        user_groups = reformed.search.Search(r, 'user_group', session).search().count()
        permissions = reformed.search.Search(r, 'permission', session).search().count()
        data = {'users' : users, "user_groups" : user_groups , "permissions" : permissions }
        out = self.create_form_data(self.fields, params = self.form_params, data = data)
        self.out = out
        self.action = 'form'
        self.title = 'listing'

        self.set_form_message("User Admin")
        self.set_form_buttons([['cancel', 'BACK']])


class SysInfo(TableNode):

    table = "_system_info"
    form_params =  {"form_type": "action"}
    title_field = 'key'

    fields = [
        ['key', 'Text', 'key:'],
        ['value', 'Text', 'value:'],
        ['type', 'Integer', 'type:', {"control" : "dropdown_code", "autocomplete" : dict(keys = [1, 2, 3], descriptions = ['String', 'Integer', 'Boolean']) }],
        ['button', 'submit', 'Save', {'control' : 'button', 'node': 'bug.SysInfo:_save:'}],
    ]

