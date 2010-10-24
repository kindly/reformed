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
import urllib

import sqlalchemy

from web.global_session import global_session
import database.util as util
import custom_exceptions
from database.saveset import SaveItem, SaveNew
from page_item import FormItemFactory

r = global_session.database

class Form(object):

    # list of form types
    # NOTE is this the best place to define this?
    # what about expansion?
    form_types = "active normal grid results input".split()

    def __init__(self, name, node, version, *form_items, **kw):

        self._form_items = form_items

        self.name = name

        self.version = version + 1

        # provided keywords
        # TD document `table`
        self.table = kw.get("table", None)
        # general
        self.params = kw.get("params")
        self.title_field = kw.get("title_field")
        self.layout_title = kw.get("layout_title")
        self.read_only = kw.get("read_only", False)
        self.form_type = kw.get("form_type", 'input') # TODO do we want this to default?
        self.form_buttons = kw.get("form_buttons")

        # subform
        self.child_id = kw.get("child_id")
        self.parent_id = kw.get("parent_id")

        # save actions
        self.save_next_node = kw.get("save_next_node")
        self.save_next_command = kw.get("save_next_command")
        self.save_redirect = kw.get("save_redirect")
        self.save_update = kw.get("save_update")

        self.buttons = {}

        self.form_items = []
        self.form_item_name_list = []

        # Set to True if any form items are declared non thread safe
        # forms can be specifically made volatile by adding it as a keyword
        # useful for auto forms etc
        self.volatile = kw.get('volatile', False)
        if self.volatile:
            self.version = 0

        ## get title field from table if needed
        if not self.title_field and self.table:
            self.title_field = r[self.table].title_field

        self.initiate_form_items()

    def __repr__(self):
        return '<Form `%s`>' % (self.name)

    def initiate_form_items(self):
        """set up the form_items supplied to the form"""

        ## not in init as fields want to know what table the forms is in
        for form_item in self._form_items:
            if isinstance(form_item, FormItemFactory):
                # here is where we call our form_items
                form_item_instance = form_item(self)
                if not form_item_instance:
                    continue
                # check if form item declared non thread safe
                if not form_item_instance.static:
                    self.volatile = True
                    self.version = 0
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


    def load_subform(self, node_token, parent_result, data, session):
        # TD wtf how can be called load subform when returns data?
        # can we get a better name for this?
        # get_subform_data()?

        node = self.node
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


    def show(self, node_token, data = None, **kw):
        """display form on front end including data if supplied"""

        if not data:
            data = {}
        # update the node that the form is associated with
        self.create_form_data(node_token, data)
        node_token.form(self)


    def new(self, node_token):
        """display a 'blank' form on the front end"""

        data_out = {}

        if self.form_buttons:
            data_out['__buttons'] = self.form_buttons
        else:
            data_out['__buttons'] = [['add %s' % self.table, 'f@%s:_save' % node_token.node_name],
                                 ['cancel', 'CLOSE']]
        data_out['__message'] = "Hello, add new %s" % self.table

        # update the node that the form is associated with
        self.create_form_data(node_token, data_out)

        node_token.form(self)



    def save_row(self, node_token, session = None):
        """Saves an individual database row.  Subforms are saved last and
        the subforms call this method in their own form instance.
        relation_attr is the attribute on the newly created object that should
        have the parent_obj as its value.  This is to allow sqlalchemy to determine
        the ids for new objects.
        Both form and subform manipulate the same data which is stored agianst the
        node."""
        data = node_token[self.name]

        id = data.get('id')
        root = data.get('__root')

        if id:
            # existing record
            try:
                result = r.search_single(self.table, "id = ?",
                                      values = [id],
                                      session = session)
                save_set = SaveItem(result.results[0], session)
                save_set.new = False
            except custom_exceptions.SingleResultError:
                form.errors[root] = 'record not found'
                raise

            version = data.get("_version")
            save_set.set_value("_version", version)
        else:
            # new record (create blank one)
            _core_id = data.get('__id')

            save_set = SaveNew(r, self.table, session)
            if _core_id:
                save_set.set_value('_core_id', _core_id)
            session = save_set.session
            save_set.new = True

        ## prepare save data for normal fields

        # TD we loop through the form items and try to save them
        for form_item in self.form_items:
            form_item.save_page_item(node_token, save_set, data, session)

        errors = save_set.save()

        # FIXME get errors working again :)
####        errors = {}
####        try:
####            session.save_or_update(obj)
####        except formencode.Invalid, e:
####            print "failed to save\n%s" % e.msg
####            for key, value in e.error_dict.items():
####                errors[key] = value.msg
####            errors[root] = errors


        return (save_set, errors)



    def save(self, node_token):
        """Save this form. Its job is to set up the node belongs to
        and handle errors"""
        # TD not reviewed

        ## set up data to be stored
    #    node_token.saved = []
    #    node_token.errors = {}
    #    node_token.out = {}
        #node_token.action = 'save'

        session = r.Session()

      #  data = node_token.data

        try:
            (save_set, errors) = self.save_row(node_token, session)
        except Exception, e:
            session.rollback()
            session.close()
            raise

    #    if node_token.errors:
    #        node_token.out['errors'] = node_token.errors
            # If there are errors during the save we want to show them at the front end
            # FIXME is this the best way to do this?
     #       return
     #   if node_token.saved:
     #       node_token.out['saved'] = node_token.saved


        if save_set.new:
            obj = save_set.obj
            if self.title_field:
                title = getattr(obj, self.title_field)
            else:
                title = obj.id
            data_out = {}
            data_out['__buttons'] = [['add %s' % self.table, '%s:_save:' % node_token.node_name],
                                     ['cancel', 'BACK']]
            data_out['__message'] = "%s saved!  Add more?" % title

            node_token.next_data_out = data_out

            # FIXME disabled as currently broken
            # need to decide on how to handle node redirects better
            #node_token.data["id"] = obj.id

        if self.save_redirect:
            # make sure redirect is correct
            while self.save_redirect.count(':') < 2:
                self.save_redirect += ':'
            if not self.save_redirect.endswith(':'):
                self.save_redirect += '&'
            # add data
            link = self.save_redirect + "id=" + str(obj.id)
            node_token.redirect(link)
            return

        elif self.save_next_node:
            node_token.next_node = self.save_next_node
            return

        elif self.save_update:
            node = node_token.node
            for form in self.save_update.split():
                node[form].view(node_token, read_only = False)
            return
            # FIXME as above node data forwarding
            #node_token.next_data = dict(data = node_token.data,
            #                      command = self.save_next_command or 'new')
        else:
            node_token.redirect_back()
    # FIXME We do not want to do the auto back stuff now due to layouts
    # but we will want it for some forms etc so leave it here for now
    # even if it is disabled.
    #    node_token.redirect_back()

    def view(self, node_token, **kw):
        """Calls the appropriate view function for the form"""
        if self.form_type in ['input']:
            self.view_single(node_token, **kw)
        elif self.form_type in ['action']:
            self.show(node_token, **kw)
        elif self.form_type in ['results']:
            pass
        elif self.form_type in ['grid']:
            self.view_multiple(node_token, **kw)
        else:
            raise Exception('Unknown form_type `%s` form `%s`' % (self.form_type, self.name))

    def view_single(self, node_token, read_only=True, where = None):

        # TD not reviewed
        node = node_token.node
        is_main_form = (node.layout_main_form == self.name)

        request_data = node_token[self.name]
        form_title = None
        layout_title = None
        join_data = None
        get_data = request_data.get
        id = get_data('id') or get_data('%s.id' % self.table)
        if where:
            pass
        elif id:
            where = 'id=?'
        else:
            id = get_data('__id')
            where = '_core_id=?'
        try:
            session = r.Session()

            data_out = {}

            table = self.table

            tables = util.split_table_fields(self.form_item_name_list, table).keys()

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
            _core_id = data_out.get('_core_id')

            # set the join data for the form will be returned from the front end
            if is_main_form:
                check_table = r[self.table]
                if check_table.entity or check_table.relation:
                    join_data = dict(__id = data_out.get('_core_id'))
                else:
                    join_data = dict(id = id)

            # set the title for bookmarks if this is the main form
            if is_main_form:
                if self.title_field and data_out.has_key(self.title_field):
                    form_title = data_out.get(self.title_field)
                    if not form_title:
                        form_title = 'untitled (%s)' % id
                else:
                    form_title = '%s: %s' % (self.table, id)
                # TODO currently the layout title just defaults to the page title
                # but can be extended as needed.
                layout_title = form_title

            if self.title_field:
                title = result.get(self.title_field)
            else:
                title = result.get("id")

        except custom_exceptions.SingleResultError:
            # no result found so return error to front end
            node_token.general_error('No record found for give id')
            session.close()
            return
        except KeyError:
            # table not found
            # we shouldn't be hitting this so raise error
            # keep code incase we need it
            raise Exception('Table `%s` not found for form `%s`' % (table, self.name))
            print 'TABLE NOT FOUND', self.name, table
            data_out = {}
            result = None
            id = None
            join_field = None
            title = 'Table not Found'
            data_out = {}
            for form_item in self.form_items:
                form_item.display_page_item(node_token, result, data_out, session)
            session.close()

        if self.form_buttons:
            data_out['__buttons'] = self.form_buttons
        elif '__buttons' not in data_out:
            data_out['__buttons'] = [['save %s' % self.table, 'f@%s:_save' % node_token.node_name],
                                     ['delete %s' % self.table, '@%s:_delete' % node_token.node_name],
                                     ['cancel', 'BACK']]


        if '__message' not in data_out:
            data_out['__message'] = "Hello, edit %s" % title


    #    if join_field:
    #        data_out['__join_data'] = join_data

        self.create_form_data(node_token, data_out, read_only)

        if is_main_form and join_data:
            node_data = join_data
        else:
            node_data = None


        node_token.form(self, title = form_title, layout_title = layout_title, node_data = node_data)

        # hack to stop null bookmarks
        if is_main_form and _core_id:
            node_token.bookmark = dict(
                table_name = table,
                title = form_title,
                _core_id = _core_id
            )

        session.close()



    def view_multiple(self, node_token, read_only=True, where = None, limit=5, is_main_form = True, **kw):
        # TD not reviewed

        data = node_token[self.name]
        query = data.get('q', '')
        limit = data.get_data_int('l', limit)
        offset = data.get_data_int('o')
        id_data = data
        node = node_token.node

        id = id_data.get('id')
        if where:
            link_id = ''
            join_data = {}
            pass
        elif id:
            where = 'id=?'
            link_id = '&id=%s' % id
            join_data = dict(id = id)
        else:
            id = id_data.get('__id')
            where = '_core_id=?'
            link_id = '&__id=%s' % id
            join_data = dict(__id = id)

        session = r.Session()

        data_out = {}

        table = self.table or node.table

        tables = util.split_table_fields(self.form_item_name_list, table).keys()

        results = r.search(table, where,
                                      session = session, tables = tables,
                            limit = limit,
                           offset = offset,
                           count = True,
                                      values = [id])
        results.collect()

        session.close()

        out = []
        # build the links
        for result in results:
            row = {}
            for field in util.INTERNAL_FIELDS:
                try:
                    row[field] = result.get(field)
                except AttributeError:
                    extra_field = None
            for form_item in self.form_items:
                form_item.display_page_item(node_token, result, row, session)
            out.append(row)

        if self.form_buttons:
            buttons = self.form_buttons
        else:
            buttons = [['add %s' % self.table, '%s:_add:' % node_token.node_name],
                       ['delete %s' % self.table, '%s:_delete:' % node_token.node_name],
                       ['cancel', 'BACK']]

        data_out = {'__array' : out}
        data_out ['__message'] = "moo table!"
        data_out['__buttons'] = buttons
        data_out['__join_data'] = join_data

        self.create_form_data(node_token, data_out, read_only)

        # add the paging info
        base_link = '@%s:_update?form=%s&q=%s%s' % (node_token.node_name, self.name, query, link_id)
        node_token.add_paging(self,
                              count = results.row_count,
                              limit = limit,
                              offset = offset,
                              base_link = base_link)

        node_token.form(self)

        session.close()

    def delete(self, node_token):
        # TD not reviewed
        ##FIXME does not work and has not been tested

        data = node_token[self.name]
        id = data.get_data_int("%s.id" % self.table)
        if not id:
            id = data.get_data_int("id")

        if id:
            filter = {'id' : id}
        else:
            id = data.get_data_int("__id")
            filter = {'_core_id' : id}

        table = self.table

        session = r.Session()
        obj = r.get_class(table)
        try:
            data = session.query(obj).filter_by(**filter).one()

            for form_item in self.form_items:
                form_item.delete_page_item(node_token, data, data, session)
            session.delete(data)
            session.commit()
            # FIXME this needs to be handled more nicely and needs to be completely fixed
            #if self.form_type != 'grid' and self.table == table:
                #node_token.next_data = {'command': 'list', 'data' : self.extra_data}
                #node_token.next_node = self.name
            #else:
                #node_token.out = {'deleted': [self.data]}
                #node_token.action = 'delete'
            node = node_token.node
            for form in self.save_update.split():
                node[form].view(node_token, read_only = False)
        except sqlalchemy.orm.exc.NoResultFound:
            error = 'Record not found.'
            node_token.general_error(error)
        except sqlalchemy.exc.IntegrityError, e:
            print e

            error = 'The record cannot be deleted,\nIt is referenced by another record.'
            node_token.general_error(error)
            session.rollback()
        session.close()

    def list(self, node_token, limit=20, **kw):
        # TD not reviewed

        node = node_token.node

        query = node_token[self.name].get('q', '')
        limit = node_token[self.name].get_data_int('l', limit)
        offset = node_token[self.name].get_data_int('o')
        table = self.table or node.table

        ##FIXME do we need these separated?

        session = r.Session()

        if not table:
            where = kw.pop('where', "id>0")
            values = kw.pop('values', None)
            results = r.search('_core_entity',
                               where = where,
                               values = values,
                               limit = limit,
                               session = session,
                               offset = offset,
                               count = True)

        elif r[table].entity:
            results = r.search('_core',
                               where = "type = %s" % table,
                               extra_inner = ["primary_entity._core_entity"],
                               limit = limit,
                               session = session,
                               offset = offset,
                               count = True)
        else:
            results = r.search(table,
                               limit = limit,
                               offset = offset,
                               session = session,
                               count = True)

        results.collect()

        session.close()

        out = []
        # build the links
        if not table:
            for result in results:
                row = {}
                row['title'] = result.get('title')
                row['entity'] = result.get('table')
                row['__id'] = result.get('id')
                row['thumb'] = result.get('thumb')
                row['summary'] = result.get('summary')
                row['actions'] = None
                out.append(row)

        elif r[table].entity:
            for result in results:
                row = {}
                row['title'] = result.get('primary_entity._core_entity.title')
                row['entity'] = result.get('type')
                row['__id'] = result.get('id')
                row['thumb'] = result.get('primary_entity._core_entity.thumb')
                row['summary'] = result.get('primary_entity._core_entity.summary')
                row['actions'] = None
                out.append(row)
        else:
            title_field = self.title_field or node.title_field
            for result in results:
                row = {}
                if title_field:
                    row['title'] = result.get(title_field)
                else:
                    row['title'] = '%s: %s' % (table, result.get('id'))
                row['id'] = result.get('id')
                row['entity'] = None
                row['result_url'] = '%s:edit?id=%s' % (node.name, result.get('id'))
                out.append(row)

        data = {'__array' : out}

        encoded_data = urllib.urlencode(node.extra_data)

        data['__buttons'] = [['add new %s' % table, 'd@%s:new?%s:' % (node_token.node_name, encoded_data)],
                             ['cancel', 'BACK']]

        data['__message'] = "These are the current %s(s)." % table

        node[self.name].create_form_data(node_token, data)

        # add the paging info
        node_token.add_paging(self,
                              count = results.row_count,
                              limit = limit,
                              offset = offset,
                              base_link = '%s:list?q=%s' % (node.name, query))

        current_page = offset/limit + 1
        total_pages = results.row_count/limit + 1
        title = 'listing page %s of %s' % (current_page, total_pages)

        node_token.form(self, title = title, layout_title = self.layout_title, clear_node_data = True)


    def create_form_data(self, node_token, data=None, read_only=False):
        """creates and returns the data stucture required by the front end
        for the this form"""

        # TD maybe we should just pass data to the front end
        # if some actually exists?
        # not much in it though

        if not data:
            data = {}

        cached_version = 0
        if node_token.form_cache:
            try:
                cached_version = node_token.form_cache[self.name]
            except KeyError:
                pass

        if cached_version and cached_version == self.version:
            form = {
                "cache_form" : self.name,
                "cache_node" : node_token.node_name
            }
        else:
            form = {
                "fields" : self.create_form_item_output(node_token, data),
                "version" : self.version,
                "name" : self.name,
                "form_type" : self.form_type,
            }
            # add copy of params if there are some
            # copy is used as it may get modified
            if self.params:
                form['params'] = self.params.copy()
            # FIXME read_only should really move into the data?
            if read_only:
                form['read_only'] = True


        output = {
            "form" : form,
            "type" : "form",
            "data" : data,
        }

        node_token.output_form_data(self.name, output)


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
        self.version = 0

    def __call__(self, name, node):

        if not self.instance:
            instance = Form(name, node, self.version, *self.form_items, **self.kw)
            if instance.volatile:
                self.version = 0
                return instance
            else:
                # we have a new stable form update it's version
                self.version = instance.version
                self.instance = instance
        return self.instance


def form(*form_items, **kw):
    return FormFactory(*form_items, **kw)

