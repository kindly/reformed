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
##	reformed.py
##	======
##	
##	This file contains the standard reformed database instace, it will
##  boot the database up from whatever is in dbconfig.py

from fields import *
from tables import *
from database import *
from data_loader import FlatFile
import dbconfig
import migrate.versioning
from migrate.versioning import schemadiff
from sqlalchemy.sql import and_
import datetime

reformed = Database("reformed", 
            metadata = dbconfig.metadata,
            engine = dbconfig.engine,
            session = dbconfig.Session
            )


