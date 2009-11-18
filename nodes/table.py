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
##   Copyright (c) 2008-2009 Toby Dacre & David Raznick
##


from node import TableNode, Node, AutoForm
from .reformed.reformed import reformed as r
import node
from .reformed import reformed as table_functions


class Table(TableNode):

    allowed_types = ['Text', 'Email', 'Integer', 'Money', 'DateTime', 'Boolean']
    list_fields = [
        ['title', 'link', 'title'],
        ['summary', 'info', 'summary'],
        ['table_type', 'info', 'table_type'],
        ['edit', 'link_list', '']
    ]
    list_params = {"form_type": "results"}

    fields = [
        ['table_name', 'textbox', 'table name:'],
        ['table_type', 'info', 'type:'],
        ['summary', 'textbox', 'Summary:'],
        ['entity', 'checkbox', 'entity:'],
        ['logged', 'checkbox', 'logged:'],
        ['fields', 'subform', 'fields']
    ]
    subforms = {
        'fields':{
            'fields': [
                ['field_name', 'textbox', 'field name'],
                ['field_type', 'textbox', 'type', {'autocomplete' : allowed_types, 'auto_options':{'mustMatch':True, 'minChars': 0, 'autoFill':True}}],
                ['length', 'textbox', 'length'],
                ['mandatory', 'checkbox', 'mandatory'],
                ['default', 'textbox', 'default']
       #         ['unique', 'checkbox', 'unique'],

            ],
            "params":{
                "form_type": "grid"
            }
        }
    }

    def call(self):
        if self.command == 'list':
            self.list()
        elif self.command == 'edit':
            self.edit()
        elif self.command == 'new':
            self.new()
        elif self.command == '_save':
            self.save()

    def save(self):
        try:
            table_id = int(self.data.get('table_id'))
        except:
            table_id = None
        table_name = str(self.data.get('table_name'))
        entity = self.data.get('entity', False)
        logged = self.data.get('logged', False)
        summary = self.data.get('summary')
        if summary == '':
            summary = None
        fields = self.data.get('fields')
        if table_id:
            self.edit_existing_table(table_id, table_name, entity, logged, fields, summary)
        else:
            self.create_new_table(table_name, entity, logged, fields, summary)


    def edit_existing_table(self, table_id, table_name, entity, logged, fields, summary):

        # update the table summary
        session = r.Session()
        obj = r.get_class('__table')
        table = session.query(obj).filter_by(id = table_id).one()
        table.summary = summary
        session.save_or_update(table)
        session.commit()
        session.close()

        # edit the table fields
        for field in fields:
            field_id = field.get('field_id')
            table = r[table_id]
            type = field.get('field_type')
            name = field.get('field_name')
            if type == 'Text':
                length = field.get('length')
            else:
                length = None
            mandatory = field.get('mandatory', False)
            default = field.get('default')

            field_info = dict(length=length, mandatory=mandatory, default=default)

            if field_id:
                # the field exists so edit it
                # FIXME make this do something
                pass
            else:
                # add a new field
                field_class = getattr(table_functions, type)
                table.add_field(field_class(name, **field_info))


    def create_new_table(self, table_name, entity, logged, fields, summary):

        table = table_functions.Table(table_name, logged=logged, summary = summary)

        for field in fields:
            type = field.get('field_type')
            name = field.get('field_name')
            if type == 'Text':
                length = field.get('length')
            else:
                length = None
            mandatory = field.get('mandatory', False)
            default = field.get('default')

            field_info = dict(length=length, mandatory=mandatory, default=default)

            field_class = getattr(table_functions, type)
            table.add_field(field_class(name, **field_info))

        if entity:
            r.add_entity(table)
        else:
            r.add_table(table)
        r.persist()


    def list(self):
        data = []
        for table_name in r.tables.keys():
            # only show editable tables
            if r[table_name].table_type != 'internal':
                data.append({'title': "n:%s:edit:t=%s|%s" % (self.name, r[table_name].table_id, table_name),
                             'table_type' : r[table_name].table_type})
        data = node.create_form_data(self.list_fields, self.list_params, data)
        self.action = 'form'
        self.out = data

    def edit(self):
        table_id = int(self.data.get('t'))

        session = r.Session()
        obj = r.get_class('__table')
        table = session.query(obj).filter_by(id = table_id).one()
        summary = table.summary
        session.close()

        table_info = r[table_id]

        field_data = []
        for (name, value) in table_info.fields.iteritems():
            if value.__class__.__name__ in self.allowed_types:
                field_data.append({'field_name': name,
                                   'field_type': value.__class__.__name__,
                                   'mandatory': value.mandatory,
                                   'length': value.length,
                                   'default': value.default,
                                   'field_id': value.field_id })

        table_data = {'table_name': table_info.name,
                      'table_type' : table_info.table_type,
                      'summary' : summary,
                      'table_id': table_info.table_id,
                      'entity': table_info.entity,
                      'logged': table_info.logged,
                      'fields': field_data}

        data = node.create_form_data(self.fields, None, table_data)
        self.action = 'form'
        self.out = data

