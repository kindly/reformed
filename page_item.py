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
r = global_session.database


class PageItem(object):

    def __init__(self, page_item_type, *arg, **kw):

        self.init_kw = kw.copy()

        self.name = None
        if arg:
            self.name = arg[0]

        self.validation = kw.pop("validation", True)

        self.page_item_type = page_item_type
        self.data_type = kw.pop("data_type", None)
        self.label = kw.pop("label", None)

        if self.name and not self.label:
            self.label = self.name + ":"

        self.control = kw.pop("control", None)
        self.layout = kw.pop("layout", None)

        self.extra_params = kw

        self.codegroup = None

        #self.css = kw.pop("css", None)
        #self.description = kw.pop("description", None)

    def params(self, node):

        params = self.extra_params.copy()

        if self.control:
            params.update(self.control.convert(self, node))

        if self.layout:
            params.update(self.layout.convert(self, node))

        if self.codegroup:
            params.update(dict(codes = self.codegroup))

        return params

    def convert(self, node, field_list):

        row = {}
        row['name'] = self.name
        row['type'] = self.set_data_type(node)
        row['title'] = self.label
        row['params'] = self.set_params(node)

        return row

    def set_data_type(self, node):

        if self.data_type:
            return self.data_type
        if node.table:
            rfield = r[node.table].fields.get(self.name)
            if rfield:
                return rfield.type

    def set_params(self, node):

        params = self.params(node)

        if node.table and self.validation:
            rfield = r[node.table].fields.get(self.name)
            if rfield:
                if "validation" not in params:
                    params["validation"] = rfield.validation_info
                if rfield.default:
                    params["default"] = rfield.default

        return params


class SubForm(object):

    def __init__(self, name, **kw):

        self.name = name
        self.page_item_type = "subform"
        self.data_type = "subform"
        self.label = kw.pop("label", None)

        if self.name and not self.label:
            self.label = self.name + ":"

        self.subform = {}


    def convert(self, node, field_list):

        row = {}
        row['name'] = self.name
        row['type'] = self.data_type
        row['title'] = self.label
        row['params'] = self.params()

        return row

    def params(self):

        return self.subform or {}


class Layout(object):

    def __init__(self, layout_type, params):

        self.layout_type = layout_type
        self.params = params

    def convert(self, field, node):

        params = dict(layout = self.layout_type)
        params.update(self.params)

        return params


class Control(object):

    def __init__(self, control_type, params = None, extra_params = None):

        self.control_type = control_type
        self.params = params or {}
        self.extra_params = extra_params or {}

    def convert(self, field, node):

        params = dict(control = self.control_type)

        if self.params:
            params.update(self.params)

        if self.extra_params:
            params.update(self.extra_params)

        return params

class Dropdown(Control):

    def convert(self, field, node):

        params = dict(control = self.control_type)

        if self.params:
            params.update(self.params)

        if self.extra_params:
            params.update(self.extra_params)

        autocomplete_options = params["autocomplete"]

        database = r

        if isinstance(autocomplete_options, list):
            return params

        if isinstance(autocomplete_options, dict):
            table = autocomplete_options["table"]
            target_field = autocomplete_options["field"]

            filter_field = autocomplete_options.get("filter_field")
            filter_value = autocomplete_options.get("filter_value")

        if autocomplete_options == True:
            rfield = database[node.table].fields[field.name]

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
            results = session.query(id_field, target_field).filter(filter_field == u"%s" % filter_value).all()
        else:
            results = session.query(id_field, target_field).all()

        session.close()

        if "control" in params and params["control"] == 'dropdown_code':
            params["autocomplete"] = dict(keys = [item[0] for item in results],
                                          descriptions = [item[1] for item in results])
        else:
            params["autocomplete"] = [item[1] for item in results]

        return params

##Form fields

def input(*arg, **kw):
    form_field = PageItem("input", *arg, **kw)
    return form_field

def layout(layout_type, **kw):
    form_field = PageItem("layout", layout = Layout(layout_type, kw))
    return form_field

def subform(name, **kw):
    form_field = SubForm(name)
    return form_field

##Controls

def dropdown(arg, **kw):

    return Dropdown("dropdown", dict(autocomplete = arg), kw)

def dropdown_code(arg, **kw):

    return Control("dropdown_code", dict(autocomplete = arg), kw)

def textarea(**kw):

    return Control("textarea", kw)

def button(node, **kw):

    return Control("button", dict(node = node), kw)

def checkbox(**kw):

    return Control("checkbox", kw)

def password(**kw):

    return Control("password", kw)

def button_box(button_list, **kw):

    return Control("button_box", dict(buttons = button_list), kw)

def button_link(node, **kw):

    return Control("button_link", dict(node = node), kw)

def link(**kw):

    return Control("link", kw)

def link_list(**kw):

    return Control("link_list", kw)

def info(**kw):

    return Control("info", kw)

def codegroup(**kw):

    return Control("codegroup", kw)
