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
##	saveset.py
##	======

import formencode
import sqlalchemy

import custom_exceptions


class SaveNew(object):

    def __init__(self, database, table, session = None):

        if not session:
            self.session = database.Session()
        else:
            self.session = session

        self.database = database
        self.table = table
        self.save_items = {}
        self.save_values = {}
        self.paths = {}
        self.core_id = None
        self.core = None
        self.obj = None
        self.parent_save_set = None
        self.all_errors = {}
        self.rtable = database[self.table]
        self.path_to_defined_name = {}
        self.path_to_value = {}
        self.prepared = False

    def set_value(self, field, value, accept_empty = False):

        if not value and value is not False and not accept_empty:
            return

        self.save_values[field] = value

    def process_value(self, field, value):

        table_name = self.table
        edge = self.database[self.table].get_edge_from_field(field)
        path = ()
        if edge:
            table_name = edge.table
            path = tuple(edge.path) 

        field_name = field.split(".")[-1]

        self.path_to_value[(path, field_name)] = value 


        self.path_to_defined_name[(path, field_name)] = field
        self.paths[path] = table_name


    def process_values(self, accept_empty = False):

        for field, value in self.save_values.items():
            ## pop the objects as this is run twice
            self.save_values.pop(field)
            if not value and value is not False and not accept_empty:
                continue
            self.process_value(field, value)

    def get_obj_from_field(self, value, field = "_core_id", table = None):
        if not table:
            table = self.table

        try:
            search_single = self.database.search_single
            result = search_single(table,
                                   "%s = ?" % field,
                                   values = [value],
                                   session = self.session)
        except custom_exceptions.SingleResultError, e:
            raise
        return result.results[0]

    def set_main_obj(self):

        if self.obj:
            return

        if self.rtable.relation or self.rtable.entity:
            core_id_key = ((), "_core_id")
            core_id_field = self.path_to_defined_name.get(core_id_key)
            if core_id_field:
                self.core_id = self.path_to_value(core_id_key)
                obj = self.get_obj_from_field(self.core_id)
            else:
                obj = self.database.get_instance(self.table)
                core = self.database.get_instance("_core")
                core.type = obj._table.name
                self.session.add_no_validate(core)
                self.core = core
        else:
            id_field = self.path_to_defined_name.get(((), "id"))
            if id_field:
                id_value = self.save_values[id_field]
                obj = self.get_obj_from_field(id_value, "id")
            else:
                obj = self.database.get_instance(self.table)

        self.obj = obj

    def create_main_saveitem(self):

        self.save_items[()] = SaveItem(self.obj, self.session)

    def update_core_id(self):

        if self.rtable.relation or self.rtable.entity:

            self.core_id = self.obj._core_id
            if self.core:
                self.core_id = self.core.id
                self.obj._rel__core = self.core
                self.obj._core_id = self.core_id


    def create_save_items(self):

        self.update_core_id()

        for path, table_name in self.paths.iteritems():
            if path == ():
                continue

            id_key = (path, "id")
            id_field = self.path_to_defined_name.get(id_key)
            if id_field:
                id_value = self.path_to_value(id_key)
                obj = self.get_obj_from_field(id_value, "id", table_name)
                if self.core_id and "_core_id" in obj._table.fields:
                    assert obj._core_id == self.core_id
            else:
                obj = self.database.get_instance(table_name)
                if self.core_id and "_core_id" in obj._table.fields:
                    obj._core_id = self.core_id

            self.save_items[path] = SaveItem(obj, self.session)

    def populate_save_items(self):

        for (path, field_name), value in self.path_to_value.iteritems():
            self.save_items[path].set_value(field_name, value)

    def prepare(self, parent_save_set = None, defer = False):
        
        if self.prepared:
            return

        if parent_save_set:
            self.obj = parent_save_set.obj
            self.parent_save_set = parent_save_set

        self.process_values()
        self.set_main_obj()
        self.create_main_saveitem()
        if not defer:
            self.session.session.flush()
        self.prepared = True

    def save(self, finish = True):

        self.prepare()
        self.process_values()
        self.create_save_items()
        self.populate_save_items()

        if self.parent_save_set and self.parent_save_set.all_errors:
            self.all_errors = {"__error": "original row failed validation"}
            return self.all_errors

        all_errors = {}
        for path, save_item in self.save_items.iteritems():
            errors = save_item.save(finish = False)
            for key, value in errors.items():
                try:
                    field = self.path_to_defined_name[(path, key)]
                except KeyError:
                    for def_path, def_key in self.path_to_defined_name:
                        if def_path == path:
                            field = self.path_to_defined_name[path, def_key]
                            field = ".".join(field.split(".")[:-1]) + "." + key

                all_errors[field] = value

        if finish:
            if all_errors:
                self.session.rollback()
            else:
                self.session.commit()
        elif all_errors:
            for save_item in self.save_items.itervalues():
                save_item.expunge()
            if self.core:
                self.session.session.delete(self.core)
            self.all_errors = all_errors

        return all_errors

class SaveError(object):

    def __init__(self, error):
        self.all_errors = error
        self.obj = None

    def set_value(self):
        pass

    def save(self, finish = False):
        return self.all_errors

    def prepare(self, **kw):
        pass

            

class SaveItem(object):

    def __init__(self, obj, session):
        self.obj = obj
        self.session = session

    def set_value(self, field, value):
        setattr(self.obj, field, value)

    def expunge(self):
        try:
            self.session.session.expunge(self.obj)
        except sqlalchemy.exc.InvalidRequestError:
            pass

    def save(self, finish = True):
        errors = {}
        try:
            self.session.save(self.obj)
        except formencode.Invalid, e:
            for key, value in e.error_dict.items():
                errors[key] = value.msg

        if finish:
            if errors:
                self.session.rollback()
            else:
                self.session.commit()

        return errors

    def prepare(self, **kw):
        pass


