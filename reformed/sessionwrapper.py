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
class SessionWrapper(object):
            
    def __init__(self, Session):
        self.session = Session()

    def __getattr__(self, item):
        return getattr(self.session, item)

    def close(self):
        self.session.close()

    def add(self, obj):
            
        obj._table.validate(obj)
        self.session.add(obj)
    
    def query(self, mapper):
        return self.session.query(mapper)

    def flush(self):
        self.add_logged_instances()
        self.session.flush()

    def commit(self):
        self.add_logged_instances()
        self.session.flush()
        self.session.commit()

    def add_logged_instances(self):

        for obj in self.session.dirty:
            database = obj._table.database
            table = obj._table
            if not table.logged:
                continue
            logged_instance = database.get_instance("_log_%s"%table.name)
            changed = False
            for column in table.columns.keys():
                a,b,c = attributes.get_history(attributes.instance_state(obj), column,
                                              passive = False)
                print a,b,c
                if c:
                    setattr(logged_instance, column, c[0])
                    changed = True
                else:
                    setattr(logged_instance, column, getattr(obj,column))
            if changed:
                self.session.add(logged_instance)

#       print "finished first"

class SessionClass(object):

    def __init__(self, Session):
        self.Session = Session

    def __call__(self):
        return SessionWrapper(self.Session)
       
