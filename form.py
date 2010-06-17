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
import formencode
import sqlalchemy
import reformed.util as util
import reformed.custom_exceptions as custom_exceptions
import urllib
from page_item import input, FormItemFactory

class Form(object):

    def __init__(self, name, node, *args, **kw):

        self.provided_form_items = args

        # TD why have a name?
        self.name = name

        self.node = node
        self.node_name = node.name

        # provided keywords
        # TD document `table`
        # use default table for the node if none specified
        self.table = kw.get("table", node.table)
        # general
        self.params = kw.get("params")
        self.title_field = kw.get("title_field")
        self.read_only = kw.get("read_only", False)

        # subform
        self.child_id = kw.get("child_id")
        self.parent_id = kw.get("parent_id")

        # save actions
        self.save_next_node = kw.get("save_next_node")
        self.save_next_command = kw.get("save_next_command")
        self.save_redirect = kw.get("save_redirect")

        self.buttons = {}

        self.form_items = []
        self.form_item_name_list = []

        self.volatile = False # Set to True if any form items are declared non thread safe

        ## get title field from table if needed
        if not self.title_field and self.table:
            self.title_field = r[self.table].title_field

        self.initiate_form_items()

    def initiate_form_items(self):
        """set up the form_items supplied to the form"""

        ## not in init as fields want to know what table the forms is in
        for form_item in self.provided_form_items:
            if isinstance(form_item, FormItemFactory):
                # here is where we call our form_items
                form_item_instance = form_item(self)
                # check if form item declared non thread safe
                if not form_item_instance.static:
                    self.volatile = True
                self.form_items.append(form_item_instance)
                if form_item_instance.name:
                    self.form_item_name_list.append(form_item_instance.name)
                if hasattr(form_item_instance, "extra_fields"):
                    self.form_item_name_list.extend(form_item_instance.extra_fields)
            else:
                raise Exception('Item is not FormItemFactory')

    def set_name(self, name):
        # don't like want to kill TD
        # only used in TableNode
        self.name = name

    def set_node(self, node):
        # don't like want to kill TD
        # only used in TableNode
        self.node = node
        self.node_name = node.name
        self.table = self.table or node.table

        # TD wtf?
        ## not in init as fields want to know what table the forms is in
        for form_item in self.form_items:
            form_item.set_form(self)

    def load_subform(self, node_token, parent_result, data, session):
        # TD wtf how can be called load subform when returns data?
        # can we get a better name for this?
        # get_subform_data()?

        node = self.node
        session = r.Session()
        data_out = {}
        table = self.table
        tables = util.split_table_fields(self.form_item_name_list, table).keys()

        parent_value = data.get(self.parent_id)
        where = "%s=?" % self.child_id

        result = r.search(self.table, where, session = session, 
                          tables = tables, values = [parent_value])

        out = []

        for counter in range(0, len(result.results)):
            result.current_row = counter
            data_out = {}
            for field in util.INTERNAL_FIELDS:
                try:
                    data_out[field] = result.get(field)
                except AttributeError:
                    extra_field = None

            for form_item in self.form_items:
                form_item.display_page_item(node_token, result, data_out, session)

            out.append(data_out)

        return out


    def show(self, node_token, data = None):
        """display form on front end including data if supplied"""

        if not data:
            data = {}
        # update the node that the form is associated with
        node_token.out = self.create_form_data(node_token, data)
        node_token.action = 'form'


    def new(self, node_token):
        """display a 'blank' form on the front end"""

        data_out = {}
        data_out['__buttons'] = [['add %s' % self.table, '%s:_save:' % self.node_name],
                                 ['cancel', 'BACK']]
        data_out['__message'] = "Hello, add new %s" % self.table

        # update the node that the form is associated with
        node_token.out = self.create_form_data(node_token, data_out)
        node_token.action = 'form'

    def save_row(self, node_token, data, session, as_subform, parent_obj = None, relation_attr = None):

        """Saves an individual database row.  Subforms are saved last and
        the subforms call this method in their own form instance. 
        relation_attr is the attribute on the newly created object that should
        have the parent_obj as its value.  This is to allow sqlalchemy to determine
        the ids for new objects.
        Both form and subform manipulate the same data which is stored agianst the
        node."""

        id = data.get('id')
        root = data.get('__root')

        # existing record
        if id:
            try:
                result = r.search_single(self.table, "id = ?",
                                      values = [id],
                                      session = session)
                obj = result.results[0]
                obj._new = False
            except custom_exceptions.SingleResultError:
                form.errors[root] = 'record not found'
                raise

            version = data["_version"]
            setattr(obj, "_version", version)

        else:
            # new record (create blank one)
            obj = r.get_instance(self.table)
            obj._new = True
            # subform data will have a parent_obj
            # which we need to link
            if parent_obj:
                setattr(obj, relation_attr, parent_obj)

        ## prepare save data for normal fields

        # TD we loop through the form items and try to save them

        for form_item in self.form_items:
      #      if form_item.page_item_type not in ["subform", "layout"]:
      #     we may need this if we decide to save subforms with main form
            form_item.save_page_item(node_token, obj, data, session)

        if as_subform:
            child_id = self.child_id
            setattr(obj, child_id, data[child_id])

        try:
            session.save_or_update(obj)
        except formencode.Invalid, e:
            print "failed to save\n%s" % e.msg
            errors = {}
            for key, value in e.error_dict.items():
                errors[key] = value.msg
            node_token.errors[root] = errors

# FIXME subform 
###        for form_item in self.form_items:
###            if form_item.page_item_type <> "subform":
###                continue
###            form_item.save(self, self.node, obj, data, session)

        return obj

    def save(self, node_token, as_subform = False):
        """Save this form. Its job is to set up the node belongs to 
        and handle errors"""
        # TD not reviewed

        ## set up data to be stored
        node_token.saved = []
        node_token.errors = {}
        node_token.out = {}
        node_token.action = 'save'

        session = r.Session()

        data = node_token.data

        try:
            obj = self.save_row(node_token, data, session, as_subform)
            if not node_token.errors:
                session.commit()
        except Exception, e:
            session.rollback()
            session.close()
            raise

        if node_token.errors:
            node_token.out['errors'] = node_token.errors
            # If there are errors during the save we want to show them at the front end
            # FIXME is this the best way to do this?
            return
        if node_token.saved:
            node_token.out['saved'] = node_token.saved


        if obj._new:
            if self.title_field:
                title = getattr(obj, self.title_field)
            else:
                title = obj.id
            data_out = {}
            data_out['__buttons'] = [['add %s' % self.table, '%s:_save:' % self.node_name],
                                     ['cancel', 'BACK']]
            data_out['__message'] = "%s saved!  Add more?" % title

            node_token.next_data_out = data_out

            node_token.data["id"] = obj.id

            if self.save_redirect:
                node_token.action = 'redirect'
                node_token.link = self.save_redirect + ":id=" + str(obj.id)
                return

            node_token.next_node = self.save_next_node or self.node_name
            node_token.next_data = dict(data = node_token.data,
                                  command = self.save_next_command or 'new')

        else:
            node_token.action = 'redirect'
            node_token.link = 'BACK'


    def view(self, node_token, read_only=True, where = None):
        # TD not reviewed
        node = self.node
        print 'VIEW', node_token.data
        id = node_token.data.get('id')
        if where:
            pass
        elif id:
            where = 'id=?'
        else:
            id = node_token.data.get('__id')
            where = '_core_entity_id=?'

        try:
            session = r.Session()

            data_out = {}

            table = self.table

            tables = util.split_table_fields(self.form_item_name_list, table).keys()
            print 'VIEW', table, where
            result = r.search_single(table, where, 
                                          session = session, tables = tables,
                                          values = [id])

            for field in util.INTERNAL_FIELDS:
                try:
                    data_out[field] = result.get(field)
                except AttributeError:
                    extra_field = None

            for form_item in self.form_items:
                form_item.display_page_item(node_token, result, data_out, session)

            id = data_out.get('id')
            # set the title for bookmarks
            if self.title_field and data_out.has_key(self.title_field):
                node_token.title = data_out.get(self.title_field)
            else:
                node_token.title = '%s: %s' % (self.table, id)

        except sqlalchemy.orm.exc.NoResultFound:
            data = None
            data_out = {}
            id = None
            node_token.title = 'unknown'
            print 'no data found'

        if self.title_field:
            title = result.get(self.title_field)
        else:
            title = result.get("id")

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

        data = self.create_form_data(node_token, data_out, read_only)

        node_token.out = data
        node_token.action = 'form'

        node_token.bookmark = dict(
            table_name = table,
            bookmark_string = node.build_node('', 'view', 'id=%s' %  id),
            entity_id = id
        )

    def delete(self, node_token):
        # TD not reviewed
        ##FIXME does not work and has not been tested
        node = node_token  # FIXME
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

            for form_item in self.form_items:
                form_item.delete(self, node, data, data, session)

            session.delete(data)
            session.commit()
            # FIXME this needs to be handled more nicely and needs to be completely fixed
            if self.form_params['form_type'] != 'grid' and self.table == table:
                node.next_data = {'command': 'list', 'data' : self.extra_data}
                node.next_node = self.name
            else:
                node.out = {'deleted': [self.data]}
                node.action = 'delete'
        except sqlalchemy.orm.exc.NoResultFound:
            error = 'Record not found.'
            node.out = error
            node.action = 'general_error'
        except sqlalchemy.exc.IntegrityError, e:
            print e

            error = 'The record cannot be deleted,\nIt is referenced by another record.'
            node.out = error
            node.action = 'general_error'
            session.rollback()
        session.close()

    def list(self, node_token, limit=20):
        # TD not reviewed

        node = node_token.node

        query = node_token.data.get('q', '')
        limit = node_token.get_data_int('l', limit)
        offset = node_token.get_data_int('o')

        table = self.table or node.table

        ##FIXME do we need these separated?
        if r[table].entity:
            results = r.search('_core_entity',
                               where = "table = %s" % table,
                               limit = limit,
                               offset = offset,
                               count = True)
        else:
            results = r.search(table,
                               limit = limit,
                               offset = offset,
                               count = True)

        data = results.data
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

        encoded_data = urllib.urlencode(node.extra_data)

        data['__buttons'] = [['add new %s' % self.table, '%s:new:%s:' % (self.node_name, encoded_data)],
                             ['cancel', 'BACK']]

        data['__message'] = "These are the current %s(s)." % self.table

        out = node["listing"].create_form_data(node_token, data)

        # add the paging info
        out['paging'] = {'row_count' : results.row_count,
                         'limit' : limit,
                         'offset' : offset,
                         'base_link' : 'n:%s:list:q=%s' % (self.node.name, query)}

        node_token.out = out
        node_token.action = 'form'
        node_token.title = 'listing'


    def create_form_data(self, node_token, data=None, read_only=False):
        """creates and returns the data stucture required by the front end
        for the this form"""

        # TD maybe we should just pass data to the front end
        # if some actually exists?
        # not much in it though

        if not data:
            data = {}

        out = {
            "form": {
                "fields":self.create_form_item_output(node_token, data)
            },
            "type": "form",
            "data": data
        }
        # add copy of params if there are some
        # copy is used as it may get modified
        if self.params:
            out['form']['params'] = self.params.copy()
        if read_only:
            if not out['form']['params']:
                out['form']['params'] = {}
            out['form']['params']['read_only'] = True

        return out

    def create_form_item_output(self, node_token, data):
        """create and return the form data stucture used by the front end"""

        form_items = []
        for form_item in self.form_items:
            row = form_item.get_page_item_structure(node_token, data)
            if row:
                form_items.append(row)
        return form_items



class FormFactory(object):

    def __init__(self, *form_items, **kw):
        self.form_items = form_items
        self.kw = kw
        self.instance = None

    def __call__(self, name, node):

        if  not self.instance:
            print 'create form %s' % name
            instance = Form(name, node, *self.form_items, **self.kw)
            if instance.volatile:
                return instance
            else:
                self.instance = instance
        else:
            print 'reuse form %s' % name

        return self.instance


def form(*form_items, **kw):
    return FormFactory(*form_items, **kw)

