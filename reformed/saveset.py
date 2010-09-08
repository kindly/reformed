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
import custom_exceptions


class SaveNew(object):

    def __init__(self, database, table, session = None, defer_core_save = False):

        if not session:
            self.session = database.Session()
        else:
            self.session = session

        self.database = database
        self.table = table
        self.save_items = {}
        self.save_values = {}
        self.paths = set()
        self.core_id = None
        self.core = None
        self.obj = None
        self.rtable = database[self.table]
        self.path_to_defined_name = {}
        self.path_to_value = {}

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
        self.paths.add((path, table_name))


    def process_values(self):

        for field, value in self.save_values.iteritems():
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

    def create_main_saveitem(self):

        if self.rtable.relation or self.rtable.entity:
            core_id_field = self.path_to_defined_name.get(((), "_core_id"))
            if core_id_field:
                self.core_id = self.save_values[core_id_field]
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
        self.save_items[()] = SaveItem(obj, self.session)

    def update_core_id(self):

        if self.rtable.relation or self.rtable.entity and not self.core_id:
            if not self.core_id:
                self.session.session.flush()
            self.core_id = self.core.id
            self.obj._core_id = self.core_id


    def create_save_items(self):

        self.update_core_id()

        for path, table_name in self.paths:
            if path == ():
                continue

            id_field = self.path_to_defined_name.get((path, "id"))
            if id_field:
                id_value = self.save_values[id_field]
                obj = self.get_obj_from_field(id_value, "id", table_name)
                if self.core_id and "_core_id" in obj._table.fields:
                    assert obj._core_id == self.core_id
            else:
                obj = self.database.get_instance(table_name)
                if self.core_id and "_core_id" in obj._table.fields:
                    obj._core_id = self.core_id

            save_item = SaveItem(obj, self.session)
            self.save_items[path] = SaveItem(obj, self.session)

    def populate_save_items(self):

        for (path, field_name), value in self.path_to_value.iteritems():
            self.save_items[path].set_value(field_name, value)

    def prepare(self):

        self.process_values()
        self.create_main_saveitem()

    def save(self):

        if not self.paths:
            self.prepare()
        self.create_save_items()
        self.populate_save_items()

        all_errors = {}
        for path, save_item in self.save_items.iteritems():
            errors = save_item.save(False)
            for key, value in errors.items():
                field = self.path_to_defined_name[(path, key)]
                all_errors[field] = value

        if all_errors:
            self.session.rollback()
        else:
            self.session.commit()

        return all_errors
            

class SaveItem(object):

    def __init__(self, obj, session):
        self.obj = obj
        self.session = session

    def set_value(self, field, value):
        setattr(self.obj, field, value)

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



