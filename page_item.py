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


class PageItem(object):

    def __init__(self, page_item_type, *arg, **kw):

        self.name = None
        if arg:
            self.name = arg[0]

        self.page_item_type = page_item_type
        self.data_type = kw.pop("data_type", None)
        self.label = kw.pop("label", None)

        if self.name and not self.label:
            self.label = self.name + ":"

        self.control = kw.pop("control", None)
        self.layout = kw.pop("layout", None)

    def params(self):

        if self.control:
            return self.control.convert()

        if self.layout:
            return self.layout.convert()

        return {}

    def convert(self):

        form_field = [self.name or '',
                     self.data_type or '',
                     self.label or '']

        if self.control:
            form_field.append(self.control.convert())

        if self.layout:
            form_field.append(self.layout.convert())

        return form_field


class SubForm(object):

    def __init__(self, name, **kw):

        self.name = name
        self.page_item_type = "subform"
        self.label = kw.pop("label", None)

        if self.name and not self.label:
            self.label = self.name + ":"

        self.subform = {}


    def convert(self):

        form_field = [self.name or '',
                     'subform',
                     self.label or '']

        return form_field

    def params(self):

        return self.subform or {}


class Layout(object):

    def __init__(self, layout_type, params):

        self.layout_type = layout_type
        self.params = params

    def convert(self):

        params = dict(layout = self.layout_type)
        params.update(self.params)

        return params


class Control(object):

    def __init__(self, control_type, params = None, extra_params = None):

        self.control_type = control_type
        self.params = params or {}
        self.extra_params = extra_params or {}

    def convert(self):

        params = dict(control = self.control_type)

        if self.params:
            params.update(self.params)

        if self.extra_params:
            params.update(self.extra_params)

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

    return Control("dropdown", dict(autocomplete = arg), kw)

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

def link(**kw):

    return Control("link", kw)

def link_list(**kw):

    return Control("link_list", kw)

def info(**kw):

    return Control("info", kw)

