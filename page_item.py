##   This file is part of Reformed.
##
##   Reformed is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License version 2 as
##   published by the Free Software Foundation.
##
##   Reformed is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with Reformed.  If not, see <http://www.gnu.org/licenses/>.
##
##   -----------------------------------------------------------------
##
##   Reformed
##   Copyright (c) 2008-2010 Toby Dacre & David Raznick
##

import authenticate
from global_session import global_session
import reformed.util as util
r = global_session.database

class FormItem(object):

    static = True # If True form item is thread safe

    def __init__(self, factory, form):

        self.factory = factory # the containing FormItemFactory

        # pull some usefull info out of factory
        # into local object
        self.name = factory.name
        self.validation = factory.validation
        self.default = factory.default
        self.data_type = factory.data_type
        self.label = factory.label
        self.permissions = factory.permissions
        self.control_type = factory.control_type
        self.kw = factory.kw

        self.form = form # the containing form

        # get out the database field if there is one
        try:
            self.database_field = r[self.form.table].fields[self.name]
            # if no data_type get it from the database
            if not self.data_type:
                self.data_type = self.database_field.type
        except KeyError:
            self.database_field = None



        # store any unused keywords
        self.extra_params = self.kw
        self.params = self.kw.get("params", {})
        # WTF FIXME
        # why do we over write the extra_param?
        self.extra_params = self.kw.get("extra_params", {})




    def add_extra_params(self, params):
        # FIXME what's this doing?
        self.params.update(params)


    def save_page_item(self, node_token, object, data, session):
        # TD doc string

        # check we are allowed to save this item
        # TD what about invisibles?
        if authenticate.check_permission(self.permissions):
            self.custom_control_save(node_token, object, data, session)


    def display_page_item(self, node_token, result, data, session):
        # TD doc string

        # check permissions etc
        if authenticate.check_permission(self.permissions):
            # FIXME result.results[0] is horrible
            self.custom_control_display(node_token, result, data, session)


    def delete_page_item(self, node_token, object, data, session):
        # TD doc string
        # FIXME Not called from anywhere AFAIK
        # check permissions etc
        if authenticate.check_permission(self.permissions):
            self.custom_control_delete(self, node_token, object, data, session)

    def get_page_item_structure(self, node_token, data):

        if authenticate.check_permission(self.permissions):
            return self.custom_page_item_structure(node_token, data)


    def custom_control_save(self, node_token, object, data, session):
        """save the data to the database object.
        override for custom behaviour"""
        pass

    def custom_control_display(self, node_token, result, data, session):
        pass

    def custom_control_delete(self, node_token, object, data, session):
        pass

    def custom_page_item_structure(self, node_token, data):
        pass


class FormControl(FormItem):

    """This is a control that gets shown on a form"""

    def custom_page_item_structure(self, node_token, data):

        params = self.get_control_params(data)
        params['name'] = self.name
        params['data_type'] = self.data_type
        params['title'] = self.label

        # get any validation/defaults defined in the database
        try:
            if self.database_field.validation_info:
                params["validation"] = self.database_field.validation_info
            if self.database_field.default:
                params["default"] = self.database_field.default
        except AttributeError:
            # no database field
            pass

        if self.validation:
            if 'validation' in params:
                 params["validation"].append(self.validation)
            else:
                params["validation"] = [self.validation]

        if self.default:
            params["default"] = self.default

        return params

    def get_control_params(self, data):

        params = dict(control = self.control_type)

        if self.params:
            params.update(self.params)

        if self.extra_params:
            params.update(self.extra_params)

        if self.kw:
            params.update(self.kw)

        return params

    def add_extra_params(self, params):
        # FIXME what's this doing?
        self.params.update(params)


    def custom_control_display(self, node_token, result, data, session):
        try:
            data[self.name] = result.get(self.name)
        except AttributeError:
            # control is anonymous
            pass


    def custom_control_save(self, node_token, object, data, session):
        """save the data to the database object.
        override for custom behaviour"""
        if self.name in object._table.fields:
            value = data.get(self.name)
            setattr(object, self.name, value)


class Password(FormControl):
    """Password fields do not display data to the front end
    nor do they overwrite data when empty/null"""

    def custom_control_display(self, node_token, result, data, session):
        pass

    def custom_control_save(self, node_token, object, data, session):
        if self.name in object._table.fields:
            value = data.get(self.name)
            if value:
                setattr(object, self.name, value)



class ActionItem(FormControl):

    """These are buttons, links etc"""

    def custom_page_item_structure(self, node_token, data):

        params = self.get_control_params(data)
        params['node'] = self.kw.get('link')
        if self.label:
            params['title'] = self.label

        return params

    def custom_control_display(self, node_token, result, data, session):
        # has no special data
        pass

    def custom_control_save(self, node_token, object, data, session):
        # do not save
        pass

class SubForm(FormItem):


    def custom_page_item_structure(self, node_token, data):

        subform = self.form.node[self.name]

        params = subform.create_form_data(node_token, read_only = subform.read_only)

        params['form']['table_name'] =  subform.table
        params['form']['parent_id'] =  subform.parent_id
        params['form']['child_id'] =  subform.child_id

        params['name'] = self.name
        params['control'] = 'subform'
        params['title'] = self.label

        return params

    def custom_control_display(self, node_token, result, data, session):

        subform = self.form.node[self.name]
        data[self.name] = subform.load_subform(node_token, result, data, session)

    def custom_control_save(self, node_token, object, data, session):

        subform = self.form.node[self.name]

        subform_rtable = r[subform.table]

        path = subform_rtable.table_path[self.form.table].path
        self.relation = subform_rtable.table_path[self.form.table].relation

        relation_attr = path[0]

        subform_data = data.get(self.name)

        for row in subform_data:
            form.save_row(row, session, object, relation_attr)



class Layout(FormItem):

    """Layouts are items that are used for arranging items
    eg boxes, columns, spacers
    they do not update data"""

    def custom_page_item_structure(self, node_token, data):

        params = {}
        # layouts are funny and send all their keywords through
        # to the front end.
        # FIXME is this all needed?
        params.update(self.kw)
        params.update(self.params)

        return params


class ExtraData(FormItem):

    """This item allows extra data fields to be included in what
    is sent to the front end.  They cannot change values in the database"""

    def __init__(self, factory, form):
        super(ExtraData, self).__init__(factory, form)

        self.extra_fields = factory.kw.get("extra_fields")


    def custom_control_display(self, node_token, result, data, session):
        for field in self.extra_fields:
            # FIXME does this need a try except?
            data[field] = result.get(field)



class Buttons(FormItem):

    def __init__(self, factory, form):
        super(Buttons, self).__init__(factory, form)

        self.command = factory.kw.get("command")
        self.buttons = factory.kw.get("buttons")

    def custom_control_display(self, node_token, result, data, session):
        if node_token.command == self.command:
            data["__buttons"] = self.buttons


class Message(FormItem):

    def __init__(self, factory, form):
        super(Message, self).__init__(factory, form)

        self.command = factory.kw.get("command")
        self.buttons = factory.kw.get("message")

    def custom_control_display(self, node_token, result, data, session):
        if self.form.node.command == self.command:
            data["__message"] = self.buttons


class Dropdown(FormControl):

    static = False

    def __init__(self, factory, form):

        super(Dropdown, self).__init__(factory, form)
        self.autocomplete = self.kw.get("autocomplete", True)
        self.out_params = {}


    def populate(self, data, result = None):

        params = dict(control = self.control_type)
        params.update(self.kw)

        autocomplete_options = self.autocomplete

        if autocomplete_options == 'DATA':
            params['autocomplete'] = 'DATA'
            self.out_params = params
            return


        database = r

        if isinstance(autocomplete_options, list):
            self.out_params = params
            return

        if isinstance(autocomplete_options, dict):
            params["autocomplete"] = autocomplete_options
            self.out_params = params
            return

        if autocomplete_options == True:
            rfield = self.database_field

            if rfield.column.defined_relation:
                rfield = rfield.column.defined_relation.parent

            if rfield.data_type == "Integer":
                table = rfield.other
                target_field = database[table].title_field
                filter_field = rfield.filter_field
                filter_value = rfield.name
            else:
                table, target_field = rfield.other.split(".")
                filter_field = rfield.kw.get("filter_field")
                filter_value = rfield.kw.get("filter_value")

        session = r.Session()

        target_class = database.tables[table].sa_class

        id_field = getattr(target_class, "id")
        target_field = getattr(target_class, target_field)

        if filter_field:
            filter_field = getattr(target_class, filter_field)
            self.results = session.query(id_field, target_field).filter(filter_field == u"%s" % filter_value).all()
        else:
            self.results = session.query(id_field, target_field).all()

        session.close()

        current_key = None
        current_value = None

        if result:
            current_key = result.get(self.name)
        if not result and self.default:
            current_value = self.default

        keys = []
        values = []

        for key, value in self.results:
            keys.append(key)
            values.append(value)
            if result and key == current_key:
                current_value = value
            if not result and current_value == value:
                current_key = key

        if self.control_type == 'dropdown_code':
            params["autocomplete"] = dict(keys = keys,
                                          descriptions = values)
            if current_key:
                data[self.name] = [current_key, current_value]
        else:
            params["autocomplete"] = values
            if result:
                data[self.name] = result.get(self.name)

        self.out_params = params

    def custom_control_display(self, node_token, result, data, session):

        # FIXME this always returns None?
        out_params = self.populate(data, result)

    def get_control_params(self, data):

        # FIXME needs rewrite
        if self.out_params:
            params = self.out_params
        else:
            self.populate(data)
            params = self.out_params

        if self.kw:
            params.update(self.kw)

        # get any validation/defaults defined in the database
        try:
            if self.database_field.validation_info:
                params["validation"] = self.database_field.validation_info
            if self.database_field.default:
                params["default"] = self.database_field.default
        except AttributeError:
            # no database field
            pass

        if self.validation:
            if 'validation' in params:
                 params["validation"].append(self.validation)
            else:
                params["validation"] = [self.validation]

        if self.default:
            params["default"] = self.default


        return params

class CodeGroup(FormControl):

    static = False

    def __init__(self, factory, form):
        super(CodeGroup, self).__init__(factory, form)

        self.code_table = self.kw.get('code_table', None)
        self.code_title = self.kw.get('code_title_field', None)
        self.code_desc = self.kw.get('code_desc_field', None)
        self.filter = self.kw.get('filter', None)

        table = form.table
        self.rtable = r[table]
        self.code_id = "id"

        if not self.code_title:
            self.code_title = r[self.code_table].title_field

        if not self.code_desc:
            self.code_desc = r[self.code_table].description_field

        path = self.rtable.table_path[self.code_table].path
        self.relation = self.rtable.table_path[self.code_table].relation
        path_node = self.rtable.paths[(path[0],)]

        self.relation_attr = path[0]
        self.flag_table = path_node.table

        self.join_key = self.relation.join_keys_from_table(self.flag_table)[0][0]

    def custom_control_save(self, node_token, object, data, session):
        # FIXME this is broken

        import pprint
        pprint.pprint(data)

        print node_token
        pprint.pprint(node_token.data)

        code_groups = getattr(object, self.relation_attr)
        code_group_data = data.get(self.name, [])
        print "<<~~~~page_item~~~~  %s" % code_group_data
        yes_codes = set()
        no_codes = set()

        for code in code_group_data.keys():
            if code_group_data[code]:
                yes_codes.add(int(code))
            else:
                no_codes.add(int(code))

        current_codes = set()

        for obj in code_groups:
            if getattr(obj, self.join_key) in no_codes:
                session.delete(obj)
            else:
                current_codes.add(getattr(obj, self.join_key))

        for code in yes_codes - current_codes:
            new = r.get_instance(self.flag_table)
            setattr(new, self.join_key, code)
            code_groups.append(new)
            session.save_or_update(new)

    def custom_control_display(self, node_token, result, data, session):

        code_groups = result.get(self.relation_attr)

        out = []
        for row in code_groups:
            out.append(getattr(row, self.join_key))

        data[self.name] = out

    def custom_control_delete(self, node_token, object, data, session):

        code_groups = getattr(object, self.relation_attr)
        for code in code_groups:
            session.delete(code)


    def get_control_params(self, data):

        params = dict(control = self.control_type)

        fields = ["id", self.code_title]
        if self.code_desc:
            fields.append(self.code_desc)

        codes = r.search(self.code_table, fields = fields, where = self.filter).data

        code_array = []
        for row in codes:
            code_row = [row["id"], row.get(self.code_title)]
            if self.code_desc:
                code_row.append(row.get(self.code_desc))
            code_array.append(code_row)

        params.update(dict(codes = code_array))


        return params


class FormItemFactory(object):

    """There is one FormItemFactory for each item on a form.
    When a form is created an instance of the form item
    is created by the factory and returned to that form when
    the Factory is called."""

    # default controls for unspecified inputs
    default_controls = dict(Integer = [FormControl, "intbox"],
                            Text = [FormControl, "textbox"],
                            DateTime = [FormControl, "datebox"],
                            #FIXME no date control
                            Date = [FormControl, "datebox"],
                            Email = [FormControl, "textbox"], # FIXME should we have email control?
                            Boolean = [FormControl, "checkbox"],

                            Password = [Password, 'password'],
                            Image = [FormControl, 'image'],
                            #FIXME
                            Money = [FormControl, 'textbox'],

                            LookupTextValidated = [Dropdown, 'dropdown'],
                            LookupId = [Dropdown, 'dropdown_code'])

    def __init__(self, control_type, form_item_class, **kw):

        self.control_type = control_type
        # This is the class used to create the form item
        self.form_item_class = form_item_class

        # process basic keywords
        self.name = kw.pop("name", None)
        # additional validation rules database level ones will be
        # automatically added
        self.validation = kw.pop("validation", None)
        self.default = kw.pop("default", None)
        self.data_type = kw.pop("data_type", None)
        # label for the item
        self.label = kw.pop("label", None)
        # permission(s) needed to access
        self.permissions = set(kw.pop("permissions", []))
        # if no label supplied auto generate one
        if self.name and self.label is None:
            # TD do we want to have different formats eg no : at the end?
            self.label = self.name.replace("_", " ") + ":"

        # store all other keywords
        # these will end up getting sent to the front end
        self.kw = kw

        self.instance = None
        self.volatile = False

    def __call__(self, form):

        if self.instance:
            return self.instance

        # see if we have a form item class or if not create one
        if not self.form_item_class:
            self.set_default_page_item_class(form)
        if self.volatile:
            # return a new instance of the FormItem
            print 'creating volatile form item %s (%s)' % (self.name, self.form_item_class)
            return self.form_item_class(self, form)
        else:
            print 'creating form item %s (%s)' % (self.name, self.form_item_class)
            instance = self.form_item_class(self, form)
            if instance.static:
                self.instance = instance
            else:
                self.volatile = True
            return instance



    def set_default_page_item_class(self, form):

        """set class for a form item which has none specified
        using the database schema if possible"""

        # check that the form_item refers to an actual field
        try:
            page_item_field = r[form.table].fields[self.name]
        except KeyError:
            page_item_field = None

        if not page_item_field:
            # anonymous field
            self.form_item_class = FormControl
            self.control_type = "textbox"
            return

        column = page_item_field.column

        # if this field refers to a different field
        # via a relationship then use that field to
        # decide what control to use
        if column.defined_relation:
            relation_field = column.defined_relation.parent
            # FIXME field_type = relation_field.type or something
            # or collapse even more
            field_type = relation_field.__class__.__name__
        else:
            field_type = page_item_field.type

        try:
            data = self.default_controls[field_type]
            self.form_item_class = data[0]
            self.control_type = data[1]
        except KeyError:
            # unknown form item
            print 'UNKNOWN form_item', field_type, self.name
            raise



## Form functions

def input(name, **kw):
    # input is a special case that does not know which
    # class will be used to create the form item
    # so we pass a class of None and we work it out later
    kw['name'] = name
    return FormItemFactory(None, None, **kw)


def textbox(name, **kw):
    kw['name'] = name
    return FormItemFactory('textbox', FormControl, **kw)


def intbox(name, **kw):
    kw['name'] = name
    return FormItemFactory('intbox', FormControl, **kw)


def datebox(name, **kw):
    kw['name'] = name
    return FormItemFactory('datebox', FormControl, **kw)


def layout(layout_type, **kw):
    kw['layout'] = layout_type
    return FormItemFactory('layout', Layout, **kw)


def wmd(name, **kw):
    kw['name'] = name
    return FormItemFactory('wmd', FormControl, **kw)


def textarea(name, **kw):
    kw['name'] = name
    return FormItemFactory('textarea', FormControl, **kw)


def button(link, **kw):
    kw['link'] = link
    return FormItemFactory('button', ActionItem, **kw)


def button_link(link, **kw):
    kw['link'] = link
    return FormItemFactory('button_link', ActionItem, **kw)


def checkbox(name, **kw):
    kw['name'] = name
    return FormItemFactory('checkbox', FormControl, **kw)


def password(name = None, **kw):
    kw['name'] = name
    return FormItemFactory('password', Password, **kw)


def button_box(button_list, **kw):
    kw['buttons'] = button_list
    return FormItemFactory('button_box', ActionItem, **kw)


def link(name = None, **kw):
    kw['name'] = name
    return FormItemFactory('link', FormControl, **kw)


def link_list(name = None, **kw):
    kw['name'] = name
    return FormItemFactory('link_list', FormControl, **kw)


def info(name, **kw):
    kw['name'] = name
    return FormItemFactory('info', FormControl, **kw)


def file_upload(name, **kw):
    kw['name'] = name
    return FormItemFactory('file_upload', FormControl, **kw)


def image(name, **kw):
    kw['name'] = name
    return FormItemFactory('image', FormControl, **kw)



# FIXME remove default
def dropdown(name, autocomplete, default = None, **kw):
    kw['name'] = name
    kw['autocomplete'] = autocomplete
    kw['default'] = default
    return FormItemFactory('dropdown', Dropdown, **kw)


# FIXME remove default
def dropdown_code(name, autocomplete, default = None, **kw):
    kw['name'] = name
    kw['autocomplete'] = autocomplete
    kw['default'] = default
    return FormItemFactory('dropdown_code', Dropdown, **kw)

def autocomplete(name, autocomplete, **kw):
    kw['name'] = name
    kw['autocomplete'] = autocomplete
    return FormItemFactory('autocomplete', FormControl, **kw)


def buttons(command, buttons, **kw):
    kw['command'] = command
    kw['buttons'] = buttons
    return FormItemFactory('buttons', Buttons, **kw)


def message(command, message, **kw):
    kw['command'] = command
    kw['message'] = message
    return FormItemFactory('message', Message, **kw)


def extra_data(extra_fields, **kw):
    kw['extra_fields'] = extra_fields
    return FormItemFactory('extra_data', ExtraData, **kw)


def text(text, **kw):
    """adds some text is shorthand for layout('text', text = text)"""

    kw['text'] = text
    kw['layout'] = 'text'
    return FormItemFactory('text', Layout, **kw)


def subform(name, **kw):
    kw['data_type'] = 'subform'
    kw['name'] = name
    return FormItemFactory('subform', SubForm, **kw)


def codegroup(name, **kw):
    kw['name'] = name
    return FormItemFactory('codegroup', CodeGroup, **kw)

