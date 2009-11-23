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

from sqlalchemy.orm import attributes 
from sqlalchemy.sql import text
import sqlalchemy as sa
import datetime
import time
import logging
import custom_exceptions
import warnings
from util import get_table_from_instance
import os

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
        self.after_flush_list = []
        self.has_entity = has_entity

    def __getattr__(self, item):
        return getattr(self.session, item)

    def close(self):
        self.session.close()

    def save(self, obj):
        self.add(obj)

    def save_or_update(self, obj):
        self.add(obj)

    def add(self, obj):
        """save or update and validate a sqlalchemy object"""
        obj._table.validate(obj, self.session)
        obj._validated = True
        self.session.add(obj)

    def add_no_validate(self, obj):
        """save or update and validate a sqlalchemy object"""
        obj._validated = True
        self.session.add(obj)

    def _flush(self):

        if self.has_entity:
            self.add_entity_instance()
        self.check_all_validated()
        self.add_events()
        self.delete_events()
        self.update_events()
        self.add_locked_rows()
        self.add_logged_instances()
        self.session.flush()
        self.after_flush()
        self.session.flush()
        self.after_flush_list = []
        for obj in self.session:
            obj._validated = False

    def _commit(self):

        self.session.commit()
    
    def commit(self):

        self._flush()
        self._commit()


    def after_flush(self):

        for function, args in self.after_flush_list:
            try:
                function(*args)
            except Exception:
                self.session.rollback()
                raise

    def add_after_flush(self, function, params = ()):

        self.after_flush_list.append([function, params])

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

            ##  special event to get values from parent table
            for column, property in obj._table.parent_columns_attributes.iteritems():
                new_value = self.get_value_from_parent(obj, column)
                setattr(obj, column, new_value )

            for events in obj._table.initial_events:
                events.insert_action(self, obj)

        for obj in self.session.new:
            for events in obj._table.events:
                events.insert_action(self, obj)

    def update_events(self):

        for obj in self.session.dirty:

            ## special event to update children on change
            if obj._table.primary_key_list:
                changed = False
                for column in obj._table.primary_key_list:
                    a, b, c = attributes.get_history(attributes.instance_state(obj), column,
                                                  passive = False)
                    if c:
                        changed = True
                if changed:
                    for attrib in obj._table.dependant_attributes:
                        self.update_children(obj, attrib, obj._table.primary_key_list)

            for events in obj._table.initial_events:
                events.update_action(self, obj)
        for obj in self.session.dirty:
            for events in obj._table.events:
                events.update_action(self, obj)

    def delete_events(self):

        for obj in self.session.deleted:
            for events in obj._table.initial_events:
                events.delete_action(self, obj)
        for obj in self.session.deleted:
            for events in obj._table.events:
                events.delete_action(self, obj)

    def add_locked_rows(self):

        if "_core_lock" not in self.database.tables:
            return
        
        to_check = []

        for obj in self.session.dirty:

            table = get_table_from_instance(obj, self.database)
            
            changed = False
            for column in table.columns.keys():
                a, b, c = attributes.get_history(attributes.instance_state(obj), column,
                                              passive = False)
                if c:
                    changed = True
            if changed:
                to_check.append(obj)

        for obj in self.session.deleted:
            if obj._table.name == "_core_lock":
                continue
            to_check.append(obj)

        for row in to_check:
            lock = self.database.get_instance("_core_lock")
            lock.row_id = row.id
            lock.date = row.modified_date
        
            ## hack to make sure times are unique for mysql
            if lock.date == datetime.datetime.now().replace(microsecond = 0):
                time.sleep(1)

            lock.table_name = u"%s" % row._table.name
            self.session.add(lock)

            try:
                #FIXME need to find a better way to flush locking rows
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.session.flush([lock])
            except sa.exc.IntegrityError:
                self.session.rollback()
                raise custom_exceptions.LockingError(
                    "object %s has been modified" % row, row)

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
                a, b, c = attributes.get_history(attributes.instance_state(obj), column,
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

    def add_entity_instance(self):

        for obj in self.session.new:
            table = get_table_from_instance(obj, self.database)
            if table.entity == True:
                entity = self.database.get_instance("_core_entity")
                entity.table = table.table_id
                obj._entity = entity
                self.add(obj)
                self.add(entity)

class SessionClass(object):

    def __init__(self, Session, database):
        self.Session = Session
        self.database = database

    def __call__(self):
        if "_core_entity" in self.database.tables:
            return SessionWrapper(self.Session, self.database, has_entity = True)
        return SessionWrapper(self.Session, self.database)
       
