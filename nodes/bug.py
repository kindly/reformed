from node import TableNode
from formencode import validators
from page_item import *
import reformed.search
from form import form
from global_session import global_session
r = global_session.database

class Ticket(TableNode):

    main = form(
        input('title'),
        layout('hr'),
        layout('column_start'),
        input('accepted', control = dropdown(["true", "false"])),
        input('complete_by'),
        layout('column_next'),
        input('severity', control = dropdown(True)),
        input('priority_id', control = dropdown(True)),
        layout('column_end'),
        layout('hr'),
        input('summary', control = textarea(css = "large")),

        table = "ticket",
        params =  {"form_type": "action"},
        title_field = 'title'
    )

    list_title = 'ticket %s'

    def view(self, read_only = False):

        self.next_node = "bug.ListTicket"
        self.next_data = dict(data = self.data,
                              command = "view")

    def finalise(self):
        self.set_form_buttons([['add', 'bug.Ticket:_save:'], ['cancel', 'BACK']])

class ListTicket(TableNode):

    main = form(
        input('title'),
        input('accepted', control = dropdown(["true", "false"])),
        input('complete_by' ),
        input('summary', control = textarea(css = "large")),
        input('severity', control = dropdown(True)),
        input('priority_id', control = dropdown(True)),
        subform('old_comments'),
        subform('comment'),

        table = "ticket",
        params =  {"form_type": "normal"},
        title_field = 'title',
    )

    old_comments = form(
        input('created_date'),
        input('note', control = textarea(css = "large")),

        parent_id = "_core_entity_id",
        child_id = "_core_entity_id",
        table = "comment",
        params = {"form_type": "continuous"}
    )

    comment = form(

        input('note', control = textarea(css = "large")),
        input('moo', control = checkbox()),
        input(label = 'add comment', control = button(node = 'bug.ListTicket:_save:')),

        parent_id = "_core_entity_id",
        child_id = "_core_entity_id",
        table = "comment",
        params ={"form_type": "action"}
    )

    list_title = 'ticket %s'

    def save(self):

        super(ListTicket, self).save()
        self.action = "redirect"
        self.link = "bug.ListTicket:view:__id=%s" % self.data.get("_core_entity_id")

class User(TableNode):


    main = form(
        layout('text', text = 'user..........'),
        layout('column_start'),
        input('name'),
        input('login_name', label = 'login name:'),
        input('active', control = checkbox()),
        input('email'),
        layout('column_next'),
        layout('box_start'),
        input('password', control = password()),
        input('password2', control = password()),
        layout('box_end'),
        layout('column_end'),
        layout('hr'),
        input('notes', control = textarea(css = "large")),
        layout('spacer'),
        layout('box_start'),
        input('usergroup', control = codegroup(code_table = 'user_group', code_desc_field = 'description')),
        layout('box_end'),
        layout('spacer'),

        table = "user",
        params =  {"form_type": "action"},
        title_field = 'name'
    )

    login_form = form(
        layout('box_start'),
        input('login_name', label = 'username:'),
        input('password', control = password()),
        input(label = 'Log in', control = button(node = 'bug.User:login:')),
        layout('box_end'),

        params = {"form_type": "action"}
    )

    login_validations = [
        ['login_name', validators.UnicodeString],
        ['password', validators.UnicodeString]
    ]

    about_me_form = form(
        layout('box_start'),
        input('login_name', label = 'username:'),
        input('about_me', label = 'about me:', control = textarea(css = "large")),
        layout('box_end'),

        params = {"form_type": "action"}
    )

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
                    message = '# Login failed\n\nThis account is disabled.'
                    self.show_login_form(message)
                else:

                    result = r.search('permission', 'user_group_user.user_id = %s and permission="Login"' % data_out.get('id'), fields=['permission'])['data']
                    if not result:
                        message = '# Login failed\n\nThis account is not allowed to log into the system.'
                        self.show_login_form(message)
                    else:
                        self.login(data_out)

            except:
                message = '# Login failed\n\nuser name or password incorrect, try again.'
                self.show_login_form(message)
        else:
            message = '# Login.\n\nWelcome to %s enter your login details to continue' % global_session.application['name']
            self.show_login_form(message)

    def show_login_form(self, message = None):
        if message:
            data = dict(__message = message)
        else:
            data = {}
        out = self["login_form"].create_form_data(data)
        self.action = 'form'
        self.out = out

    def about_me(self):
        where = 'id = %s' % global_session.session['user_id']
        data = r.search_single('user', where, fields = self.about_me_form_fields, keep_all = True)
        out = self["about_me_form"].create_form_data(data)
        self.action = 'form'
        self.out = out

    def save_about_me(self):
        self.saved = []
        self.errors = {}
        session = r.Session()
        filter = dict(id =  global_session.session['user_id'])
        data = self.data
        self.save_record(session, 'user', self["about_me_form"].fields, data, filter, None)
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
            permissions.append(row.get('permission'))
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
                self.out = self["main"].create_form_data()
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
    main = form(
        layout("box_start"),
        input("permission"),
        input("description", css = 'large'),
        input("long_description", label = 'long description:', control = textarea(css = 'large')),

        table = "permission",
        params =  {"form_type": "action"},
        title_field = 'permission'
    )

    def finalise(self):
        if self.command == '_save' and self.saved:
            if self.data.get('id',0) == 0:
                self.out = self["main"].create_form_data()
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
            self.set_form_message("Hello, edit {permission}")
            self.set_form_buttons([['save permission', 'bug.Permission:_save:'], ['delete permission', 'bug.Permission:_delete:'], ['cancel', 'BACK']])


class UserGroup(TableNode):

    table = "user_group"
    form_params =  {"form_type": "action"}
    title_field = 'user group'
    main = form(
        layout("box_start"),
        input('groupname', description = 'The name of the user group'),
        input('active', control = checkbox(description = 'Only active user groups give members permissions')),
        input('description', description = 'A brief description of the user group', css = 'large'),
        input('notes', control = textarea(css = "large", description = 'A longer more detailed description')),
        layout("spacer"),
        layout("box_start"),
        input('permission', control = codegroup(code_table = 'permission', code_desc_field = 'description')),
        layout("box_end"),
        layout("spacer"),

        table = "user_group",
        params =  {"form_type": "action"},
        title_field = 'user group'
    )


    def finalise(self):
        if self.command == '_save' and self.saved:
            if self.data.get('id',0) == 0:
                self.out = self["main"].create_form_data()
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
    main = form(
        layout('text', text = 'Users {users}'),
        input(control = button_link('bug.User:new'), label = 'add user'),
        input(control = button_link('bug.User:list'), label = 'list users'),
        layout('spacer'),
        layout('text', text = 'User Groups {user_groups}'),
        input(control = button_link('bug.UserGroup:new'), label = 'add user group'),
        input(control = button_link('bug.UserGroup:list'), label = 'list user groups'),
        layout('spacer'),
        layout('text', text = 'Permissions {permissions}'),
        input(control = button_link('bug.Permission:new'), label = 'add permission'),
        input(control = button_link('bug.Permission:list'), label = 'list permissions'),
        layout('spacer'),

        params =  {"form_type": "action"},
    )

    def call(self):
        session = r.Session()
        users = reformed.search.Search(r, 'user', session).search().count()
        user_groups = reformed.search.Search(r, 'user_group', session).search().count()
        permissions = reformed.search.Search(r, 'permission', session).search().count()
        data = {'users' : users, "user_groups" : user_groups , "permissions" : permissions }
        out = self["main"].create_form_data(data)
        self.out = out
        self.action = 'form'
        self.title = 'listing'

        self.set_form_message("User Admin")
        self.set_form_buttons([['cancel', 'BACK']])


class SysInfo(TableNode):

    table = "_system_info"
    form_params =  {"form_type": "action"}
    title_field = 'key'

    main = form(
        input('key'),
        input('value'),
        input('type', control = dropdown_code(dict(keys = [1, 2, 3], descriptions = ['String', 'Integer', 'Boolean']))),

        table = "_system_info",
        params =  {"form_type": "action"},
        title_field = 'key',

    )

    def finalise(self):
        if self.command == '_save' and self.saved:
            if self.data.get('id',0) == 0:
                self.out = self["main"].create_form_data()
                self.set_form_message("Key %s saved!  Add more?" % self.data.get('key'))
                self.action = 'form'
                self.set_form_buttons([['add key', 'bug.SysInfo:_save:'], ['cancel', 'BACK']])
            else:
                self.action = 'redirect'
                self.link = 'BACK'
        if self.command == 'list':
            self.set_form_message("These are the current keys.")
            self.set_form_buttons([['add new key', 'bug.SysInfo:new'], ['cancel', 'BACK']])
        if self.command == 'new':
            self.set_form_message("Add new key")
            self.set_form_buttons([['add key', 'bug.SysInfo:_save:'], ['cancel', 'BACK']])
        if self.command == 'edit':
            self.set_form_message("Edit {key}")
            self.set_form_buttons([['save key', 'bug.SysInfo:_save:'], ['delete key', 'bug.SysInfo:_delete:'], ['cancel', 'BACK']])


class Page(TableNode):

    table = "page"
    form_params =  {"form_type": "action"}
    title_field = 'title'

    main = form(
        input("page", css = "large", description = "A reference for the page used for links etc."),
        input("title", css = "large", description = "The displayed title for the page."),
        input("body", control = textarea(css = "large long", description = "A longer more detailed description")),

        table = "page",
        params =  {"form_type": "action"},
        title_field = 'title'
    )

    view_fields = [
        input('title', control = info()),
        input('body', control = info()),
    ]

    def view(self, read_only = False):
        id = self.data.get('id')
        if id:
            where = 'id=%s' % id
        else:
            id = self.data.get('__id')
            where = '_core_entity_id=%s' % id
        page = self.data.get('page')
        if page:
            where = 'page = %s' % page


        data_out = r.search_single(self["main"].table, where)

        id = data_out.get('id')
        if self.title_field and data_out.has_key(self.title_field):
            self.title = data_out.get(self.title_field)
        else:
            self.title = '%s: %s' % (self.table, id)


        if self.command == 'edit':
            fields = self["main"].fields
        else:
            fields = self.view_fields

        data = self["main"].create_form_data(data_out, read_only)
        self.out = data
        self.action = 'form'

        self.bookmark = dict(
            table_name = r[data_out.get("__table")].name,
            bookmark_string = self.build_node('', 'view', 'id=%s' %  id),
            entity_id = id
        )


    def finalise(self):
        if self.command == '_save' and self.saved:
            if self.data.get('id',0) == 0:
                self.out = self["main"].create_form_data()
                self.set_form_message("Page %s saved!  Add more?" % self.data.get('title'))
                self.action = 'form'
                self.set_form_buttons([['add page', 'bug.Page:_save:'], ['cancel', 'BACK']])
            else:
                self.action = 'redirect'
                self.link = 'BACK'
        if self.command == 'list':
            self.set_form_message("These are the current page.")
            self.set_form_buttons([['add new page', 'bug.Page:new'], ['cancel', 'BACK']])
        if self.command == 'new':
            self.set_form_message("Add new page")
            self.set_form_buttons([['add page', 'bug.Page:_save:'], ['cancel', 'BACK']])
        if self.command == 'edit':
            self.set_form_message("Edit {title}")
            self.set_form_buttons([['save page', 'bug.Page:_save:'], ['delete page', 'bug.Page:_delete:'], ['cancel', 'BACK']])

