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
##	dbconfig.py
##	======
##	
##	This file gives the connection details to any sqlalchemy supported
##  database.

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
import os

metadata = MetaData()

this_dir = os.path.dirname(os.path.abspath(__file__))
print 'engine = sqlite:///%s/reformed.sqlite' % this_dir
engine = create_engine('sqlite:///%s/reformed.sqlite' % this_dir, echo = False)
#engine = create_engine('sqlite:///', echo = False)
#engine = create_engine('mysql://localhost/test_donkey')
#engine = create_engine('postgres://david:@:5432/test_donkey', echo = True)
metadata.bind = engine
Session = sessionmaker(bind=engine, autoflush = False)

