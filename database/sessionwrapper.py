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
##	sessionwrapper.py
##	======
##	
##	This file contains a wrapper for a sqlalchemy session class to add
##  funtionality such a as logging and validataion.
import datetime
import time
import logging
import warnings
import os
import collections

from sqlalchemy.orm import attributes 
from sqlalchemy.sql import text
import sqlalchemy as sa

import custom_exceptions
from util import get_table_from_instance
from events import EventState
from tables import Table

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
log_file = os.path.join(root, "session.log")

logger = logging.getLogger('reformed.session')
logger.setLevel(logging.INFO)
sessionhandler = logging.FileHandler(log_file)
logger.addHandler(sessionhandler)

class SessionWrapper(object):
    """add hooks and overides sqlalchemy session"""
            
    def __init__(self, Session, database, has_entity = False):
        self.session = Session()
        self.database = database
        self.has_entity = has_entity
        self.new = []
        self.changed = []
        self.deleted = []

        self.object_store = collections.defaultdict(set)

    def __getattr__(self, item):
        return getattr(self.session, item)

    def query(self, *args, **kw):

        new_args = []
        for arg in args:
            if isinstance(arg, Table):
                new_args.append(arg.sa_class)
            else:
                new_args.append(arg)

        return self.session.query(*new_args, **kw)

    def close(self):
        self.session.close()

    def save(self, obj):
        ##FIXME should be removed 
        self.add(obj)

    def save_or_update(self, obj):
        ##FIXME should be renamed

        self.add(obj)

        ## TODO find a quicker way to if its new
        if obj in self.session.new:
            return

        if not hasattr(obj, "_version_changed") or obj._version_changed == False:
            raise AttributeError("version has not been set")

        obj._version_changed = False


    def add(self, obj):
        """save or update and validate a sqlalchemy object"""
        ##FIXME should be renamed to say it does not do version checking
        if not obj._validated:
            obj._table.validate(obj, self)
            obj._validated = True
            self.session.add(obj)

    def add_no_validate(self, obj):
        """save or update and validate a sqlalchemy object"""
        obj._validated = True
        self.session.add(obj)

    def _flush(self):

        if self.has_entity:
            self.add_extra_instance()
        self.check_all_validated()

        self.add_events()
        self.delete_events()
        self.change_events()

        self.add_logged_instances()
        self.session.flush()

        self.add_events_after()
        self.delete_events_after()
        self.change_events_after()

        self.session.flush()
        for obj in self.session:
            obj._validated = False
            obj._version_changed = False
        self.object_store = collections.defaultdict(set)

    def _commit(self):

        self.session.commit()
    
    def commit(self):

        self._flush()
        self._commit()


    def make_keys(self, object):

        object.id = text("(select coalesce((select max(id) from (select * from %s) poo ),0) + 1)" % (object._table.name))
        self.session.add(object)

    def get_value_from_parent(self, object, column):

        parent_attribute = object._table.parent_columns_attributes[column]

        parent_obj = getattr(object, parent_attribute)

        result = getattr(parent_obj, column)

        if result:
            return result
        else:
            return self.get_value_from_parent(parent_obj, column)

    def update_children(self, obj, attrib, to_update):


        for child in getattr(obj, attrib):
            for col in to_update:
                value = self.get_value_from_parent(child, col)
                setattr(child, col, value)

            if child._table.primary_key_list:
                for attrib in child._table.dependant_attributes:
                    self.update_children(child, attrib, child._table.primary_key_list)


    def add_events(self):

        for obj in self.session.new:
            self.new.append(obj)

            if hasattr(obj, "_from_load"):
                continue
            ##FIXME special event to get values from parent table, should be normal event
            for column, property in obj._table.parent_columns_attributes.iteritems():
                new_value = self.get_value_from_parent(obj, column)
                setattr(obj, column, new_value )

            event_state = EventState(obj, self, "new")
            for action in obj._table.events["new"]:
                if not action.post_flush:
                    action(event_state)

    def add_events_after(self):

        for obj in self.new:
            event_state = EventState(obj, self, "new")
            for action in obj._table.events["new"]:
                if action.post_flush:
                    action(event_state)

        self.new = []


    def change_events(self):

        for obj in self.session.dirty:
            self.changed.append(obj)

            ##FIXME special event to get values from parent table, should be normal event
            if obj._table.primary_key_list:
                changed = False
                for column in obj._table.primary_key_list:
                    a, b, c = attributes.get_history(obj, column,
                                                  passive = False)
                    if c:
                        changed = True
                if changed:
                    for attrib in obj._table.dependant_attributes:
                        self.update_children(obj, attrib, obj._table.primary_key_list)

            event_state = EventState(obj, self, "change")
            for action in obj._table.events["change"]:
                if not action.post_flush:
                    action(event_state)

    def change_events_after(self):

        for obj in self.changed:
            event_state = EventState(obj, self, "change")
            for action in obj._table.events["change"]:
                if action.post_flush:
                    action(event_state)

        self.changed = []

    def delete_events(self):

        for obj in self.session.deleted:
            self.deleted.append(obj)
            event_state = EventState(obj, self, "delete")
            for action in obj._table.events["delete"]:
                if not action.post_flush:
                    action(event_state)


    def delete_events_after(self):

        for obj in self.deleted:
            event_state = EventState(obj, self, "delete")
            for action in obj._table.events["delete"]:
                if action.post_flush:
                    action(event_state)

        self.deleted = []


    def check_all_validated(self):

        for obj in self.session.dirty:
            if not obj._validated:
                raise custom_exceptions.NotValidatedError(
                    """obj %s has not been saved and validated""" % obj)

        for obj in self.session.new:
            if not obj._validated:
                raise custom_exceptions.NotValidatedError(
                    """obj %s has not been saved and validated""" % obj)

    def add_logged_instances(self):

        for obj in self.session.dirty:
            table = get_table_from_instance(obj, self.database)
            if not table.logged:
                continue
            logged_instance = self.database.get_instance("_log_%s"%table.name)
            changed = False
            for column in table.columns.keys():
                a, b, c = attributes.get_history(obj, column,
                                              passive = False)
                #logger.info (repr(a)+repr(b)+repr(c))
                if c:
                    setattr(logged_instance, column, c[0])
                    changed = True
                else:
                    setattr(logged_instance, column, getattr(obj, column))
            if changed:
                setattr(logged_instance, "_logged_table_id", obj.id)
                #setattr(logged_instance, table.name + "_logged", obj)
                self.add(logged_instance)

    def add_extra_instance(self):

        for obj in self.session.new:
            core = None
            if hasattr(obj, "_from_load"):
                continue
            table = get_table_from_instance(obj, self.database)
            if table.entity == True:
                core = obj._rel__core
                if not core:
                    core = self.database.get_instance("_core")
                    obj._rel__core = core
                core.type = unicode(table.name)
                entity = self.database.get_instance("_core_entity")
                entity.table = unicode(table.name)
                core._rel_primary_entity = entity
                self.add(obj)
                self.add(core)
                self.add(entity)
            elif table.relation == True:
                core = obj._rel__core
                if not core:
                    core = self.database.get_instance("_core")
                    obj._rel__core = core
                core.type = unicode(table.name)
                table = obj._table
                primary_id = obj._primary 
                secondary_id = obj._secondary
                core_entity_cls = self.database["_core_entity"].sa_class
                primary_obj = self.query(core_entity_cls).get(primary_id)
                secondary_obj = self.query(core_entity_cls).get(secondary_id)
                ##FIXME make a better error, a validation rule?
                assert(primary_obj.table) in table.primary_entities
                assert(secondary_obj.table) in table.secondary_entities
                core._rel_primary_entity = primary_obj
                core._rel_secondary_entity = secondary_obj
                self.add(primary_obj)
                self.add(secondary_obj)
                self.add(core)
                self.add(obj)
            elif table.info_table == True:
                if not obj._rel__core:
                    core_id = obj._core_id
                    core_cls = self.database["_core"].sa_class
                    core = self.query(core_cls).get(core_id)
                    assert(core.type) in table.valid_core_types
                    obj._rel__core = core
                    self.add(core)
                    self.add(obj)
                else:
                    core = obj._rel__core 

            if core:
                self.object_store["core"].add(core)


class SessionClass(object):

    def __init__(self, Session, database):
        self.Session = Session
        self.database = database

    def __call__(self):
        if "_core_entity" in self.database.tables:
            return SessionWrapper(self.Session, self.database, has_entity = True)
        return SessionWrapper(self.Session, self.database)
       
