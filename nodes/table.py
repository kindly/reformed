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


import node
import reformed.fields as rfields
from global_session import global_session
r = global_session.database
from form import form
from page_item import *


class Table(node.TableNode):

    allowed_field_types = ['Text', 'Email', 'Integer', 'Money', 'DateTime', 'Boolean']
    allowed_join_types = ['OneToMany','OneToOne','ManyToOne']

    listing = form(
        input("title", control = link(css = 'form_title')),
        input("summary", control = info()),
        input("table_type", control = info()),
        input("edit", control = link_list()),

        params = {"form_type": "results"}
    )


    main = form(
        input('table_name'),
        input('table_type', control = dropdown(allowed_field_types, type = 'list')),
        input('summary', control = textarea()),
        input('entity'),
        input('logged'),
        subform('fields'),
        params = {'title' : 'Table', 'noautosave' : True}

    )

    fields = form(
        input('field_name'),
        input('field_type', control = dropdown(allowed_field_types)),
        input('length'),
        input('mandatory'),
        input('default'),
        params = {
            "form_type": "grid",
            "title": 'fields',
            "id_field": "field_id",
            'noautosave' : True}
    )


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
        self.saved.append(['', table.id, table._version])
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

            field_info = dict(mandatory=mandatory, default=default)
            if length:
                field_info['length'] = length

            if field_id:
                # the field exists so edit it
                # FIXME make this do something
                pass
            else:
                # add a new field
                field_class = getattr(rfields, field_type)
                table.add_field(field_class(field_name, **field_info))

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


    def create_new_table(self, table_name, entity, logged, fields, summary, joins):

        table = Table(table_name, logged=logged, summary = summary)

        for field in fields:
            field_type = field.get('field_type')
            field_name = field.get('field_name')
            if field_type == 'Text':
                length = field.get('length')
            else:
                length = None
            mandatory = field.get('mandatory', False)
            default = field.get('default')

            field_info = dict(mandatory=mandatory, default=default)
            if length:
                field_info['length'] = length

            field_class = getattr(rfields, field_type)

            if field_name:
                table.add_field(field_class(field_name, **field_info))

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
        data = self["listing"].create_form_data({'__array' : data})
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
            if value.__class__.__name__ in self.allowed_field_types and name[0] != '_':
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

        # add the table extra param (need a copy to not infect the shared data)
        form_params = self.form_params.copy()
        form_params['extras'] = {'table' : table_id}

        data = self["main"].create_form_data(table_data)
        self.action = 'form'
        self.out = data

class Edit(node.TableNode):

    def initialise(self):
        self.table_id = int(self.data.get('t'))

        rtable = r[int(self.table_id)]

        self.extra_data = {'t':self.table_id}

        title_field = rtable.title_field

        form_params =  {"form_type": "grid",
                             "extras" : self.extra_data,
                             "title" : rtable.name,
                             "read_only" : False
                        }

        fields = []

        for name, field in rtable.fields.iteritems():
            if field.category <> "field":
                continue

            if field.type == "Text" and field.length > 500:
                fields.append(input(field.name,
                                    control = textarea(css = "large")))
            elif field.type == "Boolean":
                fields.append(input(field.name,
                                    control = dropdown(["true", "false"])))
            else:
                fields.append(input(field.name))

        main = form(*fields, table = self.table, params = form_params)
        main.set_name("main")
        main.set_node(self)
        self._forms["main"] = main


    def view(self, read_only=False, limit = 100):

        query = self.data.get('q', '')
        limit = self.get_data_int('l', limit)
        offset = self.get_data_int('o')

        obj = r[self.table_id]
        results = r.search(obj.name, limit=limit, offset=offset, count=True)
        data = self["main"].create_form_data(results['data'])

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
