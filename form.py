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

class Form(object):

    def __init__(self, *args, **kw):

        self.fields = args

        self.table = kw.get("table")
        self.params = kw.get("params")
        self.title_field = kw.get("title_field")

        self.child_id = kw.get("child_id")
        self.parent_id = kw.get("parent_id")

    def set_name(self, name):
        self.name = name

    def set_node(self, node):
        self.node = node

    def load_subform(self, data):

        parent_value = data.get(self.parent_id)

        where = "%s=%s" % (self.child_id, parent_value)
        out = r.search(self.table, where)["data"]

        return out

    def create_form_data(self, data=None, read_only=False):

        out = {
            "form": {
                "fields":self.create_fields()
            },
            "type": "form",
        }

        if data:
            out['data'] = data
        else:
            out['data'] = {}
        if self.params:
            out['form']['params'] = self.params.copy()
        if read_only:
            if not out['form']['params']:
                out['form']['params'] = {}
            out['form']['params']['read_only'] = True


        return out

    def create_fields(self):

        fields = []
        for field in self.fields:
            row = field.convert(self, self.fields)
            fields.append(row)
        return fields

def form(self, *args, **kw):
    return Form(self, *args, **kw)
