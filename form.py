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
import reformed.custom_exceptions as custom_exceptions
from page_item import input

class Form(object):

    def __init__(self, *args, **kw):

        self.fields = args

        self.table = kw.get("table")
        self.params = kw.get("params")
        self.title_field = kw.get("title_field")

        self.save_redirect = kw.get("save_redirect")

        self.read_only = kw.get("read_only", False)

        self.child_id = kw.get("child_id")
        self.parent_id = kw.get("parent_id")

        self.save_next_node = kw.get("save_next_node")
        self.save_next_command = kw.get("save_next_command")

        self.buttons = {}

    def set_name(self, name):
        self.name = name

    def set_node(self, node):
        self.node = node
        self.node_name = node.name.split(':')[0]
        self.table = self.table or node.table

    def load_subform(self, data):

        parent_value = data.get(self.parent_id)

        where = "%s=%s" % (self.child_id, parent_value)
        out = r.search(self.table, where)["data"]

        return out


    def new(self):

        data_out = {}
        data_out['__buttons'] = [['add %s' % self.table, '%s:_save:' % self.node_name],
                                 ['cancel', 'BACK']]
        data_out['__message'] = "Hello, add new %s" % self.table

        data = self.create_form_data(data_out)
        self.node.out = data
        self.node.action = 'form'

    def save_row(self, data, session, parent_obj = None, relation_attr = None):

        """Saves an individual database row.  Subforms are saved last and
        the subforms call this method in their own form instance. 
        relation_attr is the attribute on the newly created object that should
        have the parent_obj as its value.  This is to allow sqlalchemy to determine
        the ids for new objects.
        Both form and subform manipulate the same data which is stored agianst the
        node."""

        id = data.get('id')
        root = data.get('__root')
        node = self.node

        if id:
            try:
                obj = r.search_single(self.table, "id = ?",
                                      values = [id],
                                      session = session)
                obj._new = False
            except custom_exceptions.SingleResultError:
                form.errors[root] = 'record not found'
                raise
        else:
            obj = r.get_instance(self.table)
            obj._new = True

        ## normal fields
        for field in self.fields:
            if field.page_item_type == "subform":
                continue
            field.save(self, self.node, obj, data, session)

        ## when subforms are saved on their own
        subform = node.data.get("__subform")
        if subform:
            child_id = node[subform].child_id
            id_field = input(child_id, data_type = "Integer")
            id_field.save(self, self.node, obj, data, session)

        ## if a new object and a subform add the parent object to
        ## relation property
        if not id and parent_obj:
            setattr(obj, relation_attr, parent_obj)

        version = data.get("_version")
        if version:
            setattr(obj, "_version", version)

        try:
            session.save_or_update(obj)
        except fe.Invalid, e:
            print "failed to save\n%s" % e.msg
            errors = {}
            for key, value in e.error_dict.items():
                errors[key] = value.msg
            node.errors[root] = errors

        for field in self.fields:
            if field.page_item_type <> "subform":
                continue
            field.save(self, self.node, obj, data, session)

        return obj

    def save(self):
        """Save this form. Its job is to set up the node belongs to 
        and handle errors"""

        ## set up data to be stored
        node = self.node
        node.saved = []
        node.errors = {}
        node.out = {}
        node.action = 'save'

        session = r.Session()

        data = node.data

        try:
            obj = self.save_row(data, session)
            if not node.errors:
                session.commit()
        except Exception, e:
            session.rollback()
            session.close()
            raise

        if node.errors:
            node.out['errors'] = node.errors
        if node.saved:
            node.out['saved'] = node.saved


        if obj._new:
            if self.title_field:
                title = getattr(obj, self.title_field)
            else:
                title = obj.id
            data_out = {}
            data_out['__buttons'] = [['add %s' % self.table, '%s:_save:' % self.node_name],
                                     ['cancel', 'BACK']]
            data_out['__message'] = "%s saved!  Add more?" % title

            node.next_data_out = data_out

            node.data["id"] = obj.id

            if self.save_redirect:
                node.action = 'redirect'
                node.link = self.save_redirect + ":id=" + str(obj.id)
                return

            node.next_node = self.save_next_node or self.node_name
            node.next_data = dict(data = node.data,
                                  command = self.save_next_command or 'new')

        else:
            node.action = 'redirect'
            node.link = 'BACK'


    def view(self, read_only=True, where = None):
        node = self.node
        id = node.data.get('id')
        if where:
            pass
        elif id:
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
                    data_out[field] = util.convert_value(extra_field)
                except AttributeError:
                    extra_field = None

            for field in self.fields:
                field.load(self, node, obj, data_out, session)

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

        if self.title_field:
            title = getattr(obj, self.title_field)
        else:
            title = obj.id

        if '__buttons' not in data_out:
            data_out['__buttons'] = [['save %s' % self.table, '%s:_save:' % self.node_name],
                                     ['delete %s' % self.table, '%s:_delete:' % self.node_name],
                                     ['cancel', 'BACK']]
        if not data_out['__buttons']:
            data_out.pop('__buttons')

        if '__message' not in data_out:
            data_out['__message'] = "Hello, edit %s" % title

        if not data_out['__message']:
            data_out.pop('__message')

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


        data['__buttons'] = [['add new %s' % self.table, '%s:new' % self.node_name],
                             ['cancel', 'BACK']]

        data['__message'] = "These are the current %s(s)." % self.table

        out = node["listing"].create_form_data(data)

        # add the paging info
        out['paging'] = {'row_count' : results['__count'],
                         'limit' : limit,
                         'offset' : offset,
                         'base_link' : 'n:%s:list:q=%s' % (self.name, query)}

        node.out = out
        node.action = 'form'
        node.title = 'listing'


    def create_form_data(self, data=None, read_only=False):

        out = {
            "form": {
                "fields":self.create_fields(data)
            },
            "type": "form",
        }

        if data:
            out['data'] = data
        else:
            out['data'] = []
        if self.params:
            out['form']['params'] = self.params.copy()
        if read_only:
            if not out['form']['params']:
                out['form']['params'] = {}
            out['form']['params']['read_only'] = True


        return out

    def create_fields(self, data):

        fields = []
        for field in self.fields:
            row = field.convert(self, self.fields, data)
            #skip invisible fields
            if row:
                fields.append(row)
        return fields

def form(*args, **kw):
    return Form(*args, **kw)

