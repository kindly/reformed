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

#reformed.add_table(Table("email_type", Text("email_type"), ManyToOne("email", "email")))

#flat_file = FlatFile(reformed, "people", "tests/new_people_with_header_type.csv")
#flat_file.load()

#session = reformed.Session()

#people_class =reformed.get_class("people")
#spon_class =reformed.get_class("donkey_sponsership")
##email_class =reformed.get_class("email")
#email_type_class =reformed.get_class("email_type")
#don_class =reformed.get_class("donkey")

#print str(datetime.datetime.now())
#freddy1 = session.query(people_class).filter(and_(people_class.email.any(email_class._email_type.any(email_type_class.email_type == u"work")),
                                                  ##people_class.email.any(email_class._email_type.any(email_type_class.email_type == u"home")))
                                            #).all()
#print str(datetime.datetime.now())

#freddya = session.query(people_class).join(["email","_email_type"]).filter(email_type_class.email_type == u"home")
#freddyb = session.query(people_class).join(["email","_email_type"]).filter(email_type_class.email_type == u"work")
#newfred=freddya.intersect(freddyb).all()
#print str(datetime.datetime.now())


#freddya = session.query(people_class.id).join(["email","_email_type"]).filter(email_type_class.email_type == u"home").subquery()
#freddyb = session.query(people_class.id).join(["email","_email_type"]).filter(email_type_class.email_type == u"work").subquery()
#newfred2 = session.query(people_class).\
           #join((freddya, freddya.c.id == people_class.id)).\
           #join((freddyb, freddyb.c.id == people_class.id)).all()
#print str(datetime.datetime.now())

#print str(datetime.datetime.now())
#weee = email_type_class.email_type
#print str(datetime.datetime.now())

#weee2 = and_(email_type_class.email_type == u"home", email_type_class.email_type > u"poop")


#freddyl = session.query(people_class.id).join(["email","_people"])

#and_(h.people.name == "david" and h.email["email"] == "boo" or h.email.email_type["email_type"] == "home")
#and
#(h.email.email_type == "email")


