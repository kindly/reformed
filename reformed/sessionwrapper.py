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
import logging
from util import get_table_from_instance

logger = logging.getLogger('reformed.session')
logger.setLevel(logging.INFO)
sessionhandler = logging.FileHandler("session.log")
logger.addHandler(sessionhandler)

class SessionWrapper(object):
    """add hooks and overides sqlalchemy session"""
            
    def __init__(self, Session, database, has_entity = False):
        self.session = Session()
        self.database = database
        self.has_entity = has_entity
        self.new_entities = []

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
        get_table_from_instance(obj, self.database).validate(obj)
        self.session.add(obj)
    
    def query(self, mapper):
        return self.session.query(mapper)

    def flush(self):
        if self.has_entity:
            self.add_entity_instance()
        self.add_logged_instances()
        self.session.flush()

    def commit(self):
        if self.has_entity:
            self.add_entity_instance()
        self.add_logged_instances()
        self.session.flush()
        self.session.commit()

        if self.new_entities:
            for obj in self.new_entities:
                obj._entity.table_id = obj.id
                self.session.add(obj)
            self.new_entities = []
            self.commit()

    def add_logged_instances(self):

        for obj in self.session.dirty:
            table = get_table_from_instance(obj, self.database)
            if not table.logged:
                continue
            logged_instance = self.database.get_instance("_log_%s"%table.name)
            changed = False
            for column in table.columns.keys():
                a,b,c = attributes.get_history(attributes.instance_state(obj), column,
                                              passive = False)
                #logger.info (repr(a)+repr(b)+repr(c))
                if c:
                    setattr(logged_instance, column, c[0])
                    changed = True
                else:
                    setattr(logged_instance, column, getattr(obj,column))
            if changed:
                setattr(logged_instance, table.name + "_logged" , obj )
                self.session.add(logged_instance)

    def add_entity_instance(self):

        for obj in self.session.new:
            table = get_table_from_instance(obj, self.database)
            if table.entity == True:
                entity = self.database.get_instance("_core_entity")
                self.new_entities.append(obj)
                entity.table = table.table_id
      #          logger.info(dir(obj))
                obj._entity = entity
      #          logger.info(dir(obj.__core_entity))
                self.add(obj)

class SessionClass(object):

    def __init__(self, Session, database):
        self.Session = Session
        self.database = database

    def __call__(self):
        if "_core_entity" in self.database.tables:
            return SessionWrapper(self.Session, self.database, has_entity = True)
        return SessionWrapper(self.Session, self.database)
       
