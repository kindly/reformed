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


from .reformed.reformed import reformed as r
import node
from .reformed import reformed as table_functions


class Table(node.TableNode):

    allowed_field_types = ['Text', 'Email', 'Integer', 'Money', 'DateTime', 'Boolean']
    allowed_join_types = ['OneToMany','OneToOne','ManyToOne']

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
        ['summary', 'textarea', 'Summary:'],
        ['entity', 'checkbox', 'entity:'],
        ['logged', 'checkbox', 'logged:'],
        ['fields', 'subform', 'fields'],
        ['joins', 'subform', 'joins']
    ]
    form_params ={'title' : 'Table'}
    subforms = {
        'fields':{
            'fields': [
                ['field_name', 'textbox', 'field name'],
                ['field_type', 'dropdown', 'type', {'values': '|'.join(allowed_field_types), 'type':'list'}],
                ['length', 'intbox', 'length'],
                ['mandatory', 'checkbox', 'mandatory'],
                ['default', 'textbox', 'default']
       #         ['unique', 'checkbox', 'unique'],

            ],
            "params":{
                "form_type": "grid",
                "title": 'fields',
                "id_field": "field_id"
            }
        },

        'joins':{
            'fields': [
                ['field_name', 'textbox', 'join field'],
                ['join_table', 'textbox', 'join table'],
                ['join_type', 'dropdown', 'join type', {'values': '|'.join(allowed_join_types), 'type':'list'}],

            ],
            "params":{
                "form_type": "grid",
                "title" : "joins"
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
        elif self.command == '_delete':
            self.delete()

    def delete(self):
        try:
            table_id = int(self.data.get('id'))
        except:
            table_id = None
        table = r[table_id]
        r.drop_table(table)

    def save(self):

        self.saved = []
        self.errors = {}

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
        joins = self.data.get('joins')
        if table_id:
            self.edit_existing_table(table_id, table_name, entity, logged, fields, summary, joins)
        else:
            self.create_new_table(table_name, entity, logged, fields, summary, joins)


    def edit_existing_table(self, table_id, table_name, entity, logged, fields, summary, joins):

        # FIXME this wants to be a function in reformed.database.py
        # update the table summary
        session = r.Session()
        obj = r.get_class('__table')
        table = session.query(obj).filter_by(id = table_id).one()
        table.summary = summary
        session.save_or_update(table)
        session.commit()
        session.close()
        r[table_id].summary = summary

        # edit the table fields
        for field in fields:
            field_id = field.get('field_id')
            table = r[table_id]
            field_type = field.get('field_type')
            field_name = field.get('field_name')
            if field_type == 'Text':
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
                field_class = getattr(table_functions, field_type)
                table.add_field(field_class(field_name, **field_info))
        for join in joins:
            join_type = join.get('join_type')
            join_table = join.get('join_table')
            join_name = join.get('field_name')
            if join_name:
                join_class = getattr(table_functions, join_type)
                r[table_id].add_relation(join_class(join_name, join_table))

    def create_new_table(self, table_name, entity, logged, fields, summary, joins):

        table = table_functions.Table(table_name, logged=logged, summary = summary)

        for field in fields:
            field_type = field.get('field_type')
            field_name = field.get('field_name')
            if field_type == 'Text':
                length = field.get('length')
            else:
                length = None
            mandatory = field.get('mandatory', False)
            default = field.get('default')

            field_info = dict(length=length, mandatory=mandatory, default=default)
            field_class = getattr(table_functions, field_type)

            if field_name:
                table.add_field(field_class(field_name, **field_info))

        for join in joins:
            join_type = join.get('join_type')
            join_table = join.get('join_table')
            join_name = join.get('join_name')

            join_class = getattr(table_functions, join_type)
            table.add_field(join_class(join_name, join_table))

        if entity:
            r.add_entity(table)
        else:
            r.add_table(table)
        r.persist()

        # we need to send data back to the form about the saved items

        # main table info
        self.saved.append([self.data.get('__root'), r[table_name].table_id])
        # fields
        for field in fields:
            root = field.get('__root')
            id = 0 # FIXME need to get the real field_id & _version
            version = 1
            self.saved.append([root, id, version])

        # output data
        out = {}
        if self.errors:
            out['errors'] = self.errors
        if self.saved:
            out['saved'] = self.saved

        self.out = out
        self.action = 'save'


    def list(self):
        data = []
        for table_name in r.tables.keys():
            # only show editable tables
            table = r[table_name]
            if r[table_name].table_type != 'internal':

                edit = [self.build_node('Edit', 'edit', 't=%s' % table.table_id),
                        self.build_node('Edit table', 'edit', 't=%s' % table.table_id, 'table.Edit'),
                        self.build_node('List', 'list', 'table=%s' % table_name, 'test.AutoFormPlus'),
                        self.build_node('New', 'new', 'table=%s' % table_name, 'test.AutoFormPlus'),
                        self.build_function_node('Delete','node_delete') ]

                data.append({'title': "n:%s:edit:t=%s|%s" % (self.name, table.table_id, table_name),
                             'table_type' : table.table_type,
                             'id' : table.table_id,
                             'summary': table.summary,
                             'edit' : edit})
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
        join_data = []
        for (name, value) in table_info.fields.iteritems():
            if value.__class__.__name__ in self.allowed_field_types:
                field_data.append({'field_name': name,
                                   'field_type': value.__class__.__name__,
                                   'mandatory': value.mandatory,
                                   'length': value.length,
                                   'default': value.default,
                                   'field_id': value.field_id })
            if value.__class__.__name__ in self.allowed_join_types:
                join_data.append({'field_name': name,
                                    'join_table': value.other,
                                   'join_type': value.__class__.__name__,
                                   'field_id': value.field_id })


        table_data = {'table_name': table_info.name,
                      'table_type' : table_info.table_type,
                      'summary' : summary,
                      'table_id': table_info.table_id,
                      'entity': table_info.entity,
                      'logged': table_info.logged,
                      'fields': field_data,
                      'joins': join_data}

        data = node.create_form_data(self.fields, self.form_params, table_data)
        self.action = 'form'
        self.out = data

class Edit(node.TableNode):

    def initialise(self):
        self.table_id = int(self.data.get('t'))
        self.extra_data = {"t": self.table_id}
        fields = []
        field_list = []
        obj = r[self.table_id]
        self.table = obj.name
        columns = obj.schema_info
        for field in obj.field_order:
            if field not in ['_modified_date', '_modified_by','_core_entity_id', '_version'] and field in columns:
                # FIXME an easier way to do this would be nice
                if obj.fields[field].__class__.__name__ == 'Integer':
                    fields.append([field, 'intbox', '%s:' % field])
                else:
                    fields.append([field, 'textbox', '%s:' % field])
                field_list.append(field)
        self.field_list = field_list
        self.fields = fields
        self.form_params =  {"form_type": "grid",
                             "extras" : self.extra_data
                            }

    def view(self, read_only=False, limit =100):

        query = self.data.get('q', '')
        limit = self.data.get('l', limit)
        offset = self.data.get('o', 0)

        obj = r[self.table_id]
        results = r.search(obj.name, limit=limit, offset=offset, count=True)
        data = node.create_form_data(self.fields, self.form_params, results['data'])

        # add the paging info
        data['paging'] = {'row_count' : results['__count'],
                         'limit' : limit,
                         'offset' : offset,
                         'base_link' : 'n:%s:list:t=%s' % (self.name, self.table_id)}

        self.out = data
        self.action = 'form'



    def list(self):
        self.view()



    def save(self):
        self.saved = []
        self.errors = {}

        session = r.Session()

        self.save_record_rows(session, self.table, self.fields, self.data['data'], [])


        session.commit()
        session.close()

        # output data
        out = {}
        if self.errors:
            out['errors'] = self.errors
        if self.saved:
            out['saved'] = self.saved

        self.out = out
        self.action = 'save'
