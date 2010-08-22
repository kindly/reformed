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


class SaveNew(object):

    def __init__(self, database, table, session = None):

        if not session:
            self.session = database.Session()
        else:
            self.session = session

        self.database = database
        self.table = table
        self.save_items = {}
        self.core_id = None
        rtable = database[self.table]
        self.path_to_defined_name = {}

        obj = database.get_instance(self.table)
        if rtable.relation or rtable.entity:
            core = database.get_instance("_core")
            core.type = obj._table.name
            self.session.add_no_validate(core)
            self.session.session.flush()
            self.core_id = core.id
            obj._rel__core = core

        self.save_items[()] = SaveItem(obj, self.session)
        self.obj = obj

    def set_value(self, field, value, accept_empty = False):

        if not value and value is not False and not accept_empty:
            return


        table_name = self.table
        edge = self.database[self.table].get_edge_from_field(field)
        path = ()
        if edge:
            table_name = edge.table
            path = tuple(edge.path) 

        field_name = field.split(".")[-1]
        self.path_to_defined_name[(path, field_name)] = field

        save_item = self.save_items.get(path)
        if not save_item:
            obj = self.database.get_instance(table_name)
            save_item = SaveItem(obj, self.session)
            self.save_items[path] = SaveItem(obj, self.session)
            if self.core_id and "_core_id" in obj._table.fields:
                save_item.set_value("_core_id", self.core_id)

        save_item.set_value(field_name, value)


    def save(self):

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



