import reformed.search
from reformed.custom_exceptions import SingleResultError

from node import TableNode
from form import form
from page_item import *
from formencode import validators
import authenticate

from global_session import global_session
r = global_session.database

def initialise():
    predefine = global_session.application.predefine
    # permission
    predefine.permission("Login", u'User login', u'Login to system.')
    predefine.permission("UserAdmin", u'User Administration', u'Administer user accounts.', 2)
    # user group
    predefine.user_group(u'UserAdmins', u'User Administrators', u'Administer user accounts', permissions = ['UserAdmin', 'Login'])
    predefine.user_group(u'Users', u'User', u'General user accounts', permissions = ['Login'])


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
        codegroup('user_group', code_desc_field = 'description', label = 'User Groups', filter = 'access_level = 0'),
        codegroup('user_group', code_desc_field = 'description', label = 'Restricted User Groups', filter = 'access_level > 0', permissions = ['SysAdmin']),
        layout('box_end'),
        layout('spacer'),

        table = "user",
        params =  {"form_type": "action"},
        title_field = 'name'
    )

    user = form(
        layout('column_start'),
        input('name'),
        input('login_name', label = 'login name:'),
        checkbox('active'),
        input('email'),
        layout('column_next'),

        layout('column_end'),
        layout('hr'),
        textarea('notes', css = "large"),
        layout('spacer'),
        layout('box_start'),
        codegroup('user_group', code_desc_field = 'description', label = 'User Groups', filter = 'access_level = 0'),
        codegroup('user_group', code_desc_field = 'description', label = 'Restricted User Groups', filter = 'access_level > 0', permissions = ['SysAdmin']),
        layout('box_end'),
        layout('spacer'),

        table = "user",
        params =  {"form_type": "action"},
        title_field = 'name'
    )
    change_my_password = form(
        layout('box_start'),
        password('oldpassword'),
        password('newpassword'),
        password('newpassword2'),
        buttons('about_me',
               [['Save Changes', 'user.User:_save_password_change:'],
               ['cancel', 'BACK']]),
        layout('box_end'),
        params = {"form_type": "action"}
    )

    change_other_password_form = form(
        layout('box_start'),
        password('newpassword'),
        password('newpassword2'),
        buttons('about_me',
               [['Save Changes', 'user.User:_save_password_change:'],
               ['cancel', 'BACK']]),
        layout('box_end'),
        params = {"form_type": "action"}
    )

    login_form = form(
        layout('box_start'),
        input('login_name', label = 'username:'),
        password('password'),
        checkbox('remember_me', label = 'remember me'),
        button('user.User:login:', label = 'Log in'),
        layout('box_end'),

        params = {"form_type": "action"}
    )

    login_validations = [
        ['login_name', validators.UnicodeString],
        ['password', validators.UnicodeString]
    ]

    change_password_validators = [

        ['oldpassword', validators.UnicodeString],
        ['newpassword', validators.UnicodeString],
        ['newpassword2', validators.UnicodeString]
    ]

    about_me_form = form(
        layout('box_start'),
        input('login_name', label = 'username:'),
        textarea('about_me', css = "large"),
        layout('box_end'),

        buttons('about_me',
               [['Save Changes', 'user.User:_save_about_me:'],
               ['cancel', 'BACK']]),

        message('about_me', 'About Me'),

        table = "user",
        params = {"form_type": "action"}
    )

    def edit(self):
        self["user"].view(read_only = False)

    def view(self, read_only=True):
        self["user"].view(read_only)

    def setup_extra_commands(self):
        commands = self.__class__.commands
        commands['login'] = dict(command = 'check_login')
        commands['logout'] = dict(command = 'logout')
        commands['about_me'] = dict(command = 'about_me', permissions = ['LoggedIn'])
        commands['_save_about_me'] = dict(command = 'save_about_me', permissions = ['LoggedIn'])
        commands['change_password'] = dict(command = 'change_password', permissions = ['LoggedIn'])
        commands['_save_change_password'] = dict(command = 'save_change_password', permissions = ['LoggedIn'])
        commands['change_other_password'] = dict(command = 'change_other_password', permissions = ['UserAdmin'])
        commands['_save_change_other_password'] = dict(command = 'save_change_other_password', permissions = ['UserAdmin'])

    def check_login(self):
        message = None
        fail_message = '# Login failed\n\nuser name or password incorrect, try again.'
        vdata = self.validate_data_full(self.data, self.login_validations)
        if vdata['login_name'] and vdata['password']:
            (message, data) = authenticate.check_login(vdata['login_name'], vdata['password'])
            # if data is returned then the login was a success
            if data:
                self.login(data)
                return
        if not message:
            message = '# Login.\n\nWelcome to %s enter your login details to continue' % global_session.sys_info['name']
        self.show_login_form(message)

    def show_login_form(self, message = None):
        if message:
            data = dict(__message = message)
        else:
            data = {}
        self["login_form"].show(data)

    def about_me(self):
        where = 'id = %s' % global_session.session['user_id']
        self["about_me_form"].view(read_only = False, where = where)

    def save_about_me(self):
        self["about_me_form"].save()

    def change_password(self, message = None):
        if not message:
            message = "Change your password"
        data = dict(__buttons = [['change password', 'user.User:_save_change_password:'],
                                 ['cancel', 'BACK']],
                    __message = message)

        self["change_my_password"].show(data)

    def save_change_password(self):
        vdata = self.validate_data_full(self.data, self.change_password_validators)
        if vdata['newpassword'] != vdata['newpassword2']:
            # new password not confirmed
            self.change_password('new password does not match')
        else:
            where = 'id=%s' % global_session.session['user_id']
            current_password = r.search_single_data("user", where = where, fields = ['password'])['password']

            if not reformed.fshp.check(vdata['oldpassword'], current_password):
                # old password incorrect
                self.change_password('old password does not match')
            else:
                # all good update password
                # FIXME actually update the database
                self.action = 'html'
                data = "<p>Your password has been updated (this is a lie)</p>"
                self.out = {'html': data}


    def change_other_password(self, message = None):
        where = 'id=%s' % self.data.get('id') #FIXME insecure
        user = r.search_single_data("user", where = where, fields = ['login_name'])['login_name']
        if not message:
            message = "Change password for user `%s`" % user
        data = dict(__buttons = [['change password', 'user.User:_save_change_other_password:'],
                                 ['cancel', 'BACK']],
                    __message = message,
                   id = self.data['id'])

        self["change_other_password_form"].show(data)

    def save_change_other_password(self):
        vdata = self.validate_data_full(self.data, self.change_password_validators)
        if vdata['newpassword'] != vdata['newpassword2']:
            # new password not confirmed
            self.change_other_password('new password does not match')
        else:
            where = 'id=%s' % self.data.get('id') #FIXME insecure
            user = r.search_single_data("user", where = where, fields = ['login_name'])['login_name']

            # FIXME actually update the database
            self.action = 'html'
            data = "<p>Password for user `%s` has been updated (this is a lie)</p>" % user
            self.out = {'html': data}



    def login(self, data):

        user_name = data.get('name')
        user_id = data.get('id')
        auto_loggin = data.get('auto_loggin')

        self.user = dict(name = user_name, id = user_id)

        # auto loggin cookie
        if self.data.get('remember_me') and auto_loggin:
            self.auto_loggin_cookie = '%s:%s' % (user_id, auto_loggin)

        self.action = 'html'
        data = "<p>Hello %s you are now logged in, what fun!</p>" % data['name']
        self.out = {'html': data}



    def logout(self):
        authenticate.clear_user_session()

        self.user = dict(name = None, id = 0)
        message = dict(title = "You are now logged out", body = '')
        self.show_login_form(message)
        # clear bookmarks
        self.bookmark = 'CLEAR'

        # auto loggin cookie
        self.auto_loggin_cookie = 'CLEAR'


class UserGroup(TableNode):

    main = form(
        layout("box_start"),
        info('groupname'),
        input('name', description = 'The name of the user group'),
        checkbox('active', description = 'Only active user groups give members permissions'),
        input('description', description = 'A brief description of the user group', css = 'large'),
        textarea('notes', css = "large", description = 'A longer more detailed description'),
        layout("spacer"),
        layout("box_start"),
        codegroup('permission', code_desc_field = 'description', label = 'General Permissions', filter = 'access_level = 0'),
        codegroup('permission', code_desc_field = 'description', label = 'Admin Permissions', filter = 'access_level > 0', permissions = ['SysAdmin']),
        layout("box_end"),
        layout("spacer"),

        table = "user_group",
        params =  {"form_type": "action"},
        title_field = 'name'
    )


class UserAdmin(TableNode):

    permissions = ['UserAdmin']

    form_params =  {"form_type": "action"}
    main = form(
        layout('text', text = 'Users {users}'),
        button_link('user.User:new', label = 'add user'),
        button_link('user.User:list', label = 'list users'),
        layout('spacer'),
        layout('text', text = 'User Groups {user_groups}'),
        button_link('user.UserGroup:new', label = 'add user group'),
        button_link('user.UserGroup:list', label = 'list user groups'),
        layout('spacer'),
##        layout('text', text = 'Permissions {permissions}'),
##        button_link('bug.Permission:new', label = 'add permission'),
##        button_link('bug.Permission:list', label = 'list permissions'),
##        layout('spacer'),

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

