from node import TableNode
from formencode import validators
from page_item import *
import reformed.search
from form import form
from reformed.custom_exceptions import SingleResultError
from global_session import global_session
import reformed.fshp
r = global_session.database

from predefine import permission

permission("Login", u'User login', u'Login to system.')

class Ticket(TableNode):

    main = form(
        input('title'),
        layout('hr'),
        layout('column_start'),
        input('accepted'),
        input('complete_by'),
        layout('column_next'),
        input('code_severity_id', default = 'low', label = "severity:"),
        input('code_priority_id', default = 'low', label = "priority:"),
        layout('column_end'),
        layout('hr'),
        wmd('summary', css = 'large'),
        file_upload('attachment'),
        extra_data(["created_by"]),
        table = "ticket",
        params =  {"form_type": "action"},
        title_field = 'title',

        save_redirect = "bug.ListTicket:view"
    )

    list_title = 'ticket %s'


class ListTicket(TableNode):

    main = form(
        input('title'),
        textarea('summary',css = "large"),
        layout('box_start'),
        layout('column_start'),
        input('accepted'),
        input('complete_by' ),
        layout('column_next'),
        dropdown_code('code_severity_id', True, label = "severity:"),
        input('code_priority_id', label = "priority:"),
        layout('column_end'),
        layout('box_end'),
        button('bug.Ticket:edit:{id}' ,label = 'edit', permissions = ['logged_in']), 
        layout('hr'),
        subform('old_comments'),
        subform('comment'),
        buttons("view", False),

        table = "ticket",
        params =  {"form_type": "normal"},
        title_field = 'title',
    )

    old_comments = form(
        wmd('note', label = "", css = "large"),
        layout('area_start', css = 'record_info'),
        layout('area_end'),
        text('Created {created_date:ds} by user #{created_by}', css = 'record_info'),

        extra_data(["created_by", "created_date"]),

        parent_id = "_core_entity_id",
        child_id = "_core_entity_id",
        table = "comment",
        params = {"form_type": "continuous"},
        read_only = True
    )

    comment = form(

        wmd('note', label = "", css = "large"),
        button('bug.ListTicket:_save:', label = 'add comment'),

        parent_id = "_core_entity_id",
        child_id = "_core_entity_id",
        table = "comment",
        params ={"form_type": "action"}
    )

    list_title = 'ticket %s'

    def save(self):
        self["comment"].save()
        self.action = "redirect"
        self.link = "bug.ListTicket:view:__id=%s" % self.data.get("_core_entity_id")
        # FIXME this is stupid
        self.next_node = None

class User(TableNode):


    main = form(
        layout('column_start'),
        input('name'),
        input('login_name', label = 'login name:'),
        checkbox('active'),
        input('email'),
        layout('column_next'),
        layout('box_start'),
        password('password'),
        password('password2'),
        layout('box_end'),
        layout('column_end'),
        layout('hr'),
        textarea('notes', css = "large"),
        layout('spacer'),
        layout('box_start'),
        codegroup('user_group', code_desc_field = 'description'),
        layout('box_end'),
        layout('spacer'),

        table = "user",
        params =  {"form_type": "action"},
        title_field = 'name'
    )

    login_form = form(
        layout('box_start'),
        input('login_name', label = 'username:'),
        password('password'),
        button('bug.User:login:', label = 'Log in'),
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
        textarea('about_me', css = "large"),
        layout('box_end'),

        buttons('about_me',
               [['Save Changes', 'bug.User:_save_about_me:'],
               ['cancel', 'BACK']]),

        message('about_me', 'About Me'),

        table = "user",
        params = {"form_type": "action"}
    )

    def setup_extra_commands(self):
        commands = self.__class__.commands
        commands['login'] = dict(command = 'check_login')
        commands['logout'] = dict(command = 'logout')
        commands['about_me'] = dict(command = 'about_me', permissions = ['logged_in'])
        commands['_save_about_me'] = dict(command = 'save_about_me')

    def check_login(self):
        message = None
        fail_message = '# Login failed\n\nuser name or password incorrect, try again.'
        vdata = self.validate_data_full(self.data, self.login_validations)
        if vdata['login_name'] and vdata['password']:
            where = "login_name='%s'" % vdata['login_name']
            #where = "login_name='%s' and password='%s'" % (vdata['login_name'], vdata['password'])
            try:
                data_out = r.search_single_data('user', where)
                if not reformed.fshp.check(vdata['password'], data_out.get("password")):
                    message = fail_message
                    self.show_login_form(message)
                else:
                    if data_out.get('active') != True:
                        message = '# Login failed\n\nThis account is disabled.'
                        self.show_login_form(message)
                    else:
                        result = r.search('permission', 'user_group_user.user_id = %s and permission="Login"' % data_out.get('id')).data
                        if not result:
                            ## see if you are in sysadmin group
                            result = r.search('user_group_user', 'user_id = %s and user_group_id = 1' % data_out.get('id')).data
                            if not result:
                                message = '# Login failed\n\nThis account is not allowed to log into the system.'
                                self.show_login_form(message)
                            else:
                                self.login(data_out)
                        else:
                            self.login(data_out)

            except SingleResultError:
                message = fail_message
                self.show_login_form(message)
        else:
            message = '# Login.\n\nWelcome to %s enter your login details to continue' % global_session.sys_info['name']
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
        self["about_me_form"].view(read_only = False, where = where)

    def save_about_me(self):
        self["about_me_form"].save()

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

        result = r.search('permission', 'user_group_user.user_id = %s' % user_id, fields=['permission']).data
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

class Permission(TableNode):

    main = form(
        layout("box_start"),
        input("permission"),
        input("description", css = 'large'),
        textarea("long_description", css = 'large'),

        table = "permission",
        params =  {"form_type": "action"},
        title_field = 'permission'
    )


class UserGroup(TableNode):

    main = form(
        layout("box_start"),
        input('groupname', description = 'The name of the user group'),
        checkbox('active', description = 'Only active user groups give members permissions'),
        input('description', description = 'A brief description of the user group', css = 'large'),
        textarea('notes', css = "large", description = 'A longer more detailed description'),
        layout("spacer"),
        layout("box_start"),
        codegroup('permission', code_desc_field = 'description'),
        layout("box_end"),
        layout("spacer"),

        table = "user_group",
        params =  {"form_type": "action"},
        title_field = 'groupname'
    )


class UserAdmin(TableNode):

    #permissions = ['logged_in']

    form_params =  {"form_type": "action"}
    main = form(
        layout('text', text = 'Users {users}'),
        button_link('bug.User:new', label = 'add user'),
        button_link('bug.User:list', label = 'list users'),
        layout('spacer'),
        layout('text', text = 'User Groups {user_groups}'),
        button_link('bug.UserGroup:new', label = 'add user group'),
        button_link('bug.UserGroup:list', label = 'list user groups'),
        layout('spacer'),
        layout('text', text = 'Permissions {permissions}'),
        button_link('bug.Permission:new', label = 'add permission'),
        button_link('bug.Permission:list', label = 'list permissions'),
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

    main = form(
        input('key'),
        input('value'),
        dropdown_code('type', dict(keys = [1, 2, 3], descriptions = ['String', 'Integer', 'Boolean'])),

        table = "_system_info",
        params =  {"form_type": "action"},
        title_field = 'key',

    )

class Page(TableNode):

    main = form(
        input("page", css = "large", description = "A reference for the page used for links etc."),
        input("title", css = "large", description = "The displayed title for the page."),
        wmd("body", css = "large long", description = "A longer more detailed description"),

        table = "page",
        params =  {"form_type": "action"},
        title_field = 'title'
    )

    view_form = form( 
        info('title'),
        info('body'),

        buttons('view', False),

        table = "page",
        params =  {"form_type": "action"},
        title_field = 'title'
    )

    def view(self):
        where = 'page = %s' % self.data.get("page")
        self["view_form"].view(where = where)


