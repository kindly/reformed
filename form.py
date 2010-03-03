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
import formencode as fe
import sqlalchemy as sa
import reformed.util as util

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

    def new(self):

        data_out = {}
        data = self.create_form_data(data_out)
        self.node.out = data
        self.node.action = 'form'

    def save(self):

        self.saved = []
        self.errors = {}
        node =self.node

        session = r.Session()
        id = node.data.get('id')
        root = node.data.get('__root')
        if id:
            filter = {'id' : id}
        else:
            filter = {}
        subform = node.data.get("__subform")
        if subform:
            child_id = node[subform].child_id
            fields = list(node[subform].fields) + [input(child_id, data_type = "Integer")]
            table = node[subform].table
        else:
            table = self.table
            fields = self.fields

        record_data = self.save_record(session, table, fields, node.data, filter, root)


        # FIXME how do we deal with save errors more cleverly?
        # need to think about possible behaviours we want
        # and add some 'failed save' options
        #if not self.errors:
            # subforms
        #    for subform_name in self.subforms.keys():
        #        subform_data = self.data.get(subform_name)
        #        if subform_data:
        #            subform = self.subforms.get(subform_name)
        #            table = subform.get('table')
        #            fields = subform.get('fields')
        #            # do we have a joining field?
        #            child_id = subform.get('child_id')
        #            if child_id:
        #                join_fields= [child_id]
        #            self.save_record_rows(session, table, fields, subform_data, join_fields)

        session.commit()
        session.close()

        # output data
        out = {}
        if self.errors:
            out['errors'] = self.errors
        if self.saved:
            out['saved'] = self.saved

        self.node.out = out
        self.node.action = 'save'

    def view(self, read_only=True):
        node = self.node
        id = node.data.get('id')
        if id:
            where = 'id=%s' % id
        else:
            id = node.data.get('__id')
            where = '_core_entity_id=%s' % id

        try:
            session = r.Session()

            data_out = {}

            table = self.table or node.table

            obj = r.search_single(table, where, session = session)

            for field in util.INTERNAL_FIELDS:
                try:
                    extra_field = getattr(obj, field)
                except AttributeError:
                    extra_field = None

                if extra_field:
                    data_out[field] = util.convert_value(extra_field)

            for field in self.fields:
                field.load(self, self, obj, data_out, session)

            id = data_out.get('id')
            if self.title_field and data_out.has_key(self.title_field):
                self.title = data_out.get(self.title_field)
            else:
                self.title = '%s: %s' % (self.table, id)

        except sa.orm.exc.NoResultFound:
            data = None
            data_out = {}
            id = None
            self.title = 'unknown'
            print 'no data found'


        data = self.create_form_data(data_out, read_only)

        node.out = data
        node.action = 'form'

        node.bookmark = dict(
            table_name = obj._table.name,
            bookmark_string = node.build_node('', 'view', 'id=%s' %  id),
            entity_id = id
        )

    def delete(self):
        ##FIXME does not work and has not been tested
        node = self.node
        id = node.data.get('id')
        if id:
            filter = {'id' : id}
        else:
            id = node.data.get('__id')
            filter = {'_core_entity_id' : id}

        table = self.table

        session = r.Session()
        obj = r.get_class(table)
        try:
            data = session.query(obj).filter_by(**filter).one()

            for field in self.fields:
                field.delete(self, node, data, data, session)

            session.delete(data)
            session.commit()
            # FIXME this needs to be handled more nicely and needs to be completely fixed
            if self.form_params['form_type'] != 'grid' and self.table == table:
                node.next_data = {'command': 'list', 'data' : self.extra_data}
                node.next_node = self.name
            else:
                node.out = {'deleted': [self.data]}
                node.action = 'delete'
        except sa.orm.exc.NoResultFound:
            error = 'Record not found.'
            node.out = error
            node.action = 'general_error'
        except sa.exc.IntegrityError, e:
            print e

            error = 'The record cannot be deleted,\nIt is referenced by another record.'
            node.out = error
            node.action = 'general_error'
            session.rollback()
        session.close()

    def list(self, limit=20):

        node = self.node

        query = node.data.get('q', '')
        limit = node.get_data_int('l', limit)
        offset = node.get_data_int('o')

        table = self.table or node.table

        if r[table].entity:
            results = r.search('_core_entity',
                               where = "%s.id >0" % table,
                               limit = limit,
                               offset = offset,
                               count = True)
        else:
            results = r.search(table,
                               where = "id >0",
                               limit = limit,
                               offset = offset,
                               count = True)

        data = results['data']
        # build the links
        if r[table].entity:
            for row in data:
                row['title'] = node.build_node(row['title'], 'edit', '__id=%s' % row['id'])
                row['edit'] = [node.build_node('Edit', 'edit', '__id=%s' % row['id']),
                               node.build_node('Delete', '_delete', '__id=%s' % row['id']),
                              ]
                # the id is actually the _core_entity id so let's rename it to __id
                row['__id'] = row['id']
                del row['id']
        else:
            for row in data:
                if self.title_field and row.has_key(self.title_field):
                    row['title'] = node.build_node(row[self.title_field], 'edit', 'id=%s' % row['id'])
                else:
                    row['title'] = node.build_node('%s: %s' % (self.table, row['id']), 'edit', 'id=%s' % row['id'])

                row['edit'] = [node.build_node('Edit', 'edit', 'id=%s' % row['id']),
                               node.build_node('Delete', '_delete', 'id=%s' % row['id']),
                              ]
        data = {'__array' : data}

        out = node["listing"].create_form_data(data)

        # add the paging info
        out['paging'] = {'row_count' : results['__count'],
                         'limit' : limit,
                         'offset' : offset,
                         'base_link' : 'n:%s:list:q=%s' % (self.name, query)}

        node.out = out
        node.action = 'form'
        node.title = 'listing'

    def save_record(self, session, table, fields, data, filter, root, join_fields = []):
        print 'table %s' % table
        #print 'fields %s' % fields
        errors = None
        try:
            if filter:
                print 'existing record'
                obj = r.get_class(table)
                record_data = session.query(obj).filter_by(**filter).one()
            else:
                print 'new record'
                record_data = r.get_instance(table)
            for field in fields:
                field.save(self, self.node, record_data, data, session)

            # if this is a subform we need to update/add the join field
            # FIXME is this needed here or just for new?
            # maybe shift up a few lines to new record
            for field_name in join_fields:
                    value = data.get(field_name)
                    print 'join: %s = %s' % (field_name, value)
                    setattr(record_data, field_name, value)
            version = data.get("_version")
            if version:
                setattr(record_data, "_version", version)
            try:
                session.save_or_update(record_data)
                session.commit()
                self.saved.append([root, record_data.id, record_data._version])
                return record_data
            except fe.Invalid, e:
                session.rollback()
                print "failed to save\n%s" % e.msg
                errors = {}
                for key, value in e.error_dict.items():
                    errors[key] = value.msg
                print repr(errors)
                self.errors[root] = errors
        except sa.orm.exc.NoResultFound:
            self.errors[root] = 'record not found'

    def save_record_rows(self, session, table, fields, data, join_fields):
        ##not used yet
        for row_data in data:
            row_id = row_data.get('id', 0)
            root = row_data.get('__root')
            if row_id:
                filter = {'id' : row_id}
            else:
                filter = {}
            self.save_record(session, table, fields, row_data, filter, root = root, join_fields = join_fields)

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
