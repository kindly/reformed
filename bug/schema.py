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

from reformed.database import table, entity, relation
from reformed.fields import *


def initialise(application):

    sysinfo = application.predefine.sysinfo
    sysinfo("public", True, "Allow unregistered users to use the application")
    sysinfo("name", 'Reformed Application', "Name of the application")

    database = application.database

    entity('ticket', database,

           Text("title", mandatory = True),
           Text("summary", length = 4000),
           LookupId("severity", "code", filter_field = "code_type"),
           LookupId("priority", "code", filter_field = "code_type"),
           DateTime("complete_by"),
           Boolean("accepted"),

           Created("created_date"),
           CreatedBy("created_by"),

           title_field = "title",
           summary_fields = "summary"
    )

    table("comment", database, ## notes for each user
          ManyToOne("entity", "_core_entity"),
          Created("created_date"),
          CreatedBy("created_by"),
          Text("note", length = 4000),

          valid_entities = "ticket"
    )

    relation("involvement", database,
          LookupId("role", "code", filter_field = "code_type"),
          Created("created_date"),
          CreatedBy("created_by"),

          valid_entities1 = "ticket",
          valid_entities2 = "user,usergroup",
          table_type = "system",
    )


    table("role", database, ## notes for each user
          Text("name", mandatory = True),
          Text("desctiption", length = 2000),
          valid_entities = "ticket",
          table_type = "system",
    )


    database.persist()




