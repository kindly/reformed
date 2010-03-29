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
from global_session import global_session
import reformed.util as util
r = global_session.database


class PageItem(object):

    def __init__(self, form, page_item_type, *arg, **kw):

        self.init_kw = kw.copy()

        self.name = None
        if arg:
            self.name = arg[0]

        self.validation = kw.pop("validation", True)

        self.page_item_type = page_item_type
        self.data_type = kw.pop("data_type", None)
        self.label = kw.pop("label", None)

        self.permissions = set(kw.pop("permissions", []))

        if self.name and self.label is None:
            self.label = self.name.replace("_", " ") + ":"

        self.invisible = kw.pop("invisible", False)

        self.control = kw.pop("control", None)

        self.layout = kw.pop("layout", None)

        self.extra_params = kw

        self.form = form

        if self.control:
            self.control.add_extra_params(self.extra_params)

        if not self.control and not self.layout:
            self.control = self.set_default_control(form)

    def check_permissions(self):

        user_perms = set(global_session.session.get('permissions'))
        if not self.permissions:
            return True
        if self.permissions.intersection(user_perms):
            return True


    def params(self, form, data):

        params = {}


        if self.control:
            params.update(self.control.convert(self, form, data))
        if self.layout:
            params.update(self.layout.convert(self, form, data))

        return params

    def convert(self, form, field_list, data):

        if self.invisible or not self.check_permissions():
            return

        row = self.set_params(form, data)
        row['name'] = self.name
        row['data_type'] = self.set_data_type(form)
        row['title'] = self.label

        return row

    def set_default_control(self, form):

        kw = self.extra_params

        default_controls = dict(Integer = Control("intbox", **kw),
                                Text = Control("textbox", **kw),
                                DateTime = Control("datebox", **kw),
                                Boolean = Control("checkbox", **kw),
                                LookupTextValidated = dropdown_control(True, **kw),
                                LookupId = dropdown_code_control(True, **kw))

        if not form.table:
            return

        rfield = r[form.table].fields.get(self.name)

        if not rfield:
            return

        column = rfield.column


        if column.defined_relation:
            relation_field = column.defined_relation.parent
            return default_controls.get(relation_field.__class__.__name__)

        control = default_controls.get(rfield.__class__.__name__)

        if not control:
            control = default_controls.get(rfield.type)


        return control

    def set_data_type(self, form):

        if self.data_type:
            return self.data_type
        if form.table:
            rfield = r[form.table].fields.get(self.name)
            if rfield:
                return rfield.type

    def set_params(self, form, data):

        params = self.params(form, data)

        if form.table and self.validation:
            rfield = r[form.table].fields.get(self.name)
            if rfield:
                if "validation" not in params:
                    params["validation"] = rfield.validation_info
                if rfield.default:
                    params["default"] = rfield.default

        return params

    def save(self, form, node, object, data, session):

        if not self.check_permissions():
            return

        if self.name in object._table.fields:
            value = data.get(self.name)
            setattr(object, self.name, value)

        if self.control and self.control.control_save:
            self.control.save(self, form, node, object, data, session)

    def load(self, form, node, object, data, session):

        if not self.check_permissions():
            return

        if self.name in object._table.fields:
            data[self.name] = util.convert_value(getattr(object, self.name))

        if self.control and self.control.control_load:
            self.control.load(self, form, node, object, data, session)

    def delete(self, form, node, object, data, session):

        if not self.check_permissions():
            return

        if self.control and self.control.control_delete:
            self.control.delete(self, form, node, object, data, session)

class SubForm(object):

    def __init__(self, form, name, **kw):

        self.form = form
        self.name = name
        self.page_item_type = "subform"
        self.data_type = "subform"
        self.label = kw.pop("label", None)

        if self.name and not self.label:
            self.label = self.name + ":"

    def convert(self, form, field_list, data):

        subform = form.node[self.name]

        data = subform.create_form_data(read_only = subform.read_only)

        data['form']['table_name'] =  subform.table

        data['form']['parent_id'] =  subform.parent_id
        data['form']['child_id'] =  subform.child_id

        row = data

        row['name'] = self.name
        row['control'] = 'subform'
        row['title'] = self.label

        return row

    def load(self, form, node, object, data, session):

        subform = node[self.name]
        data[self.name] = subform.load_subform(data)

    def save(self, form, node, object, data, session):

        subform = form.node[self.name]

        subform_rtable = r[subform.table]

        path, self.relation = subform_rtable.table_path[form.table]

        relation_attr = path[0]

        subform_data = data.get(self.name)

        for row in subform_data:
            form.save_row(row, session, object, relation_attr)

class Layout(object):

    def __init__(self, layout_type, params):

        self.layout_type = layout_type
        self.params = params

    def convert(self, field, form, data):

        params = dict(layout = self.layout_type)
        params.update(self.params)

        return params


class Control(object):

    def __init__(self, control_type, params = None, extra_params = None, **kw):

        self.control_type = control_type
        self.params = params or {}
        self.extra_params = extra_params or {}

        self.control_save = False
        self.control_load = False

    def convert(self, field, form, data):

        params = dict(control = self.control_type)

        if self.params:
            params.update(self.params)

        if self.extra_params:
            params.update(self.extra_params)

        return params

    def add_extra_params(self, params):

        self.params.update(params)


class ExtraData(Control):

    def __init__(self, control_type, params = None, extra_params = None, **kw):

        Control.__init__(self, control_type, params, extra_params)
        self.control_load = True

        self.extra_fields = kw.pop("extra_fields")

    def convert(self, field, form, data):
        return {}

    def load(self, field, form, node, object, data, session):
        for field in self.extra_fields:
            data[field] = util.convert_value(getattr(object, field))


class Dropdown(Control):

    def __init__(self, control_type, params = None, extra_params = None, **kw):

        Control.__init__(self, control_type, params, extra_params)
        self.control_load = True
        self.default = kw.get("default")

        self.out_params = {}

    def populate(self, field, form, data, object = None):

        params = dict(control = self.control_type)

        if self.params:
            params.update(self.params)

        if self.extra_params:
            params.update(self.extra_params)

        autocomplete_options = params["autocomplete"]

        database = r

        if isinstance(autocomplete_options, list):
            self.out_params = params
            return

        if isinstance(autocomplete_options, dict):
            params["autocomplete"] = autocomplete_options
            self.out_params = params
            return

        if autocomplete_options == True:
            rfield = database[form.table].fields[field.name]

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

        if object:
            current_key = getattr(object, field.name)
        if not object and self.default:
            current_value = self.default

        keys = []
        values = []

        for key, value in self.results:
            keys.append(key)
            values.append(value)
            if object and key == current_key:
                current_value = value
            if not object and current_value == value:
                current_key = key

        if self.control_type == 'dropdown_code':
            params["autocomplete"] = dict(keys = keys,
                                          descriptions = values)
            if current_key:
                data[field.name] = [current_key, current_value]
        else:
            params["autocomplete"] = values
            if object:
                data[field.name] = getattr(object, field.name)

        self.out_params = params

    def load(self, field, form, node, object, data, session):

        out_params = self.populate(field, form, data, object)

    def convert(self, field, form, data):

        if self.out_params:
            return self.out_params
        else:
            self.populate(field, form, data)
            return self.out_params


class Buttons(Control):

    def __init__(self, control_type, params = None, extra_params = None, **kw):

        Control.__init__(self, control_type, params, extra_params)

        self.control_load = True

        self.command = kw.get("command")

        self.buttons = kw.get("buttons")

    def load(self, field, form, node, object, data, session):

        if node.command == self.command:
            data["__buttons"] = self.buttons

class Message(Control):

    def __init__(self, control_type, params = None, extra_params = None, **kw):

        Control.__init__(self, control_type, params, extra_params)

        self.control_load = True

        self.command = kw.get("command")

        self.buttons = kw.get("message")

    def load(self, field, form, node, object, data, session):

        if node.command == self.command:
            data["__message"] = self.buttons



class CodeGroup(Control):

    def __init__(self, control_type, params = None, extra_params = None, **kw):

        Control.__init__(self, control_type, params, extra_params)

        self.control_save = True
        self.control_load = True

        self.code_table = kw.get('code_table')
        self.code_title = kw.get('code_title_field')
        self.code_desc = kw.get('code_desc_field')

    def configure(self, form):

        table = form.table
        self.rtable = r[table]

        self.code_id = "id"

        if not self.code_title:
            self.code_title = r[self.code_table].title_field

        if not self.code_desc:
            self.code_desc = r[self.code_table].description_field

        path, self.relation = self.rtable.table_path[self.code_table]

        path_node = self.rtable.paths[(path[0],)]

        self.relation_attr = path[0]
        self.flag_table = path_node.table

        self.join_key = self.relation.join_keys_from_table(self.flag_table)[0][0]

    def save(self, field, form, node, object, data, session):

        self.configure(form)

        code_groups = getattr(object, self.relation_attr)

        code_group_data = data.get(field.name, [])

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

    def load(self, field, form, node, object, data, session):

        self.configure(form)

        code_groups = getattr(object, self.relation_attr)

        out = []
        for row in code_groups:
            out.append(getattr(row, self.join_key))

        data[field.name] = out

    def delete(self, field, form, node, object, data, session):

        self.configure(form)
        code_groups = getattr(object, self.relation_attr)
        for code in code_groups:
            session.delete(code)


    def convert(self, field, form, data):

        self.configure(form)
        params = dict(control = self.control_type)
        name = field.name

        fields = ["id", self.code_title]
        if self.code_desc:
            fields.append(self.code_desc)

        codes = r.search(self.code_table, fields = fields)['data']

        code_array = []
        for row in codes:
            code_row = [row["id"], row.get(self.code_title)]
            if self.code_desc:
                code_row.append(row.get(self.code_desc))
            code_array.append(code_row)

        params.update(dict(codes = code_array))

        return params


class PageItemWrapper(object):

    def __init__(self, *arg, **kw):
        self.arg = arg
        self.kw = kw

    def __call__(self, form):
        return PageItem(form, *self.arg, **self.kw)

def page_item(*args, **kw):

    return PageItemWrapper(*args, **kw)

class SubFormWrapper(PageItemWrapper):

    def __call__(self, form):
        return SubForm(form, *self.arg, **self.kw)



##Form fields

def input(*arg, **kw):
    form_field = page_item("input", *arg, **kw)
    return form_field

def layout(layout_type, **kw):
    form_field = page_item("layout", layout = Layout(layout_type, kw))
    return form_field

def buttons(command, buttons, **kw):
    form_field = page_item("buttons",
                          invisible = True,
                          control = Buttons("buttons",
                                            kw,
                                            command = command,
                                            buttons = buttons))
    return form_field

def message(command, message, **kw):
    form_field = page_item("message",
                          invisible = True,
                          control = Message("buttons",
                                            kw,
                                            command = command,
                                            message = message))
    return form_field

def subform(name, **kw):
    form_field = SubFormWrapper(name)
    return form_field

def extra_data(extra_fields, **kw):
    form_field = page_item("extra_data",
                          invisible = True,
                          control = ExtraData("extra_fields",
                                              kw,
                                              extra_fields = extra_fields)
                         )
    return form_field

def text(text, **kw):

    form_field = page_item("text",
                          control = Control("text",
                                            dict(text = text), kw)
                         )
    return form_field

def dropdown(name, arg, default = None, **kw):

    return page_item("input", name,
                    control = dropdown_control(arg, default = default),
                    **kw)

def dropdown_code(name, arg, default = None, **kw):

    return page_item("input", name,
                    control = dropdown_control(arg, default = default),
                    **kw)

def codegroup(code_table, **kw):

    code_title = kw.pop('code_title_field', None)
    code_desc = kw.pop('code_desc_field', None)

    return page_item("input",
                    control = CodeGroup("codegroup",
                                        code_table = code_table,
                                        code_title = code_title,
                                        code_desc_field = code_desc,
                                        ),
                    **kw)


def wmd(name, **kw):

    return page_item("input", name, control = Control("wmd"), **kw)

def textarea(name, **kw):

    return page_item("input", name, control = Control("textarea"), **kw)

def button(node, **kw):

    return page_item("input", control = Control("button"),
                    node = node, **kw)

def checkbox(name, **kw):

    return page_item("input", name, control = Control("checkbox"), **kw)

def password(name = None, **kw):

    return page_item("input", name, control = Control("password"), **kw)

def button_box(button_list, **kw):

    return page_item("input", control = Control("button_box"),
                    buttons = button_list,
                    **kw)

def button_link(node, **kw):

    return page_item("input", control = Control("button_link"),
                    node = node, **kw)

def link(name = None, **kw):

    return page_item("input", name, control = Control("link"), **kw)

def link_list(name = None, **kw):

    return page_item("input", name, control = Control("link_list"), **kw)

def info(name, **kw):

    return page_item("input", name,  control = Control("info"), **kw)



##Controls


def dropdown_control(arg, default = None, **kw):

    return Dropdown("dropdown",
                    dict(autocomplete = arg),
                    kw,
                    default = default,
                    )


def dropdown_code_control(arg, default = None, **kw):

    return Dropdown("dropdown_code",
                    dict(autocomplete = arg),
                    kw,
                    default = default,
                    )

