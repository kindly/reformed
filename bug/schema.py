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
from global_session import global_session

d =  global_session.database

entity('ticket', d,

       Text("title", mandatory = True),
       Text("summary", length = 4000),
       LookupTextValidated("severity", "severity.severity", length = 4000),
       LookupId("priority", "priority", length = 4000),
       DateTime("complete_by"),
       Boolean("accepted"),

       Created("created_date"),
       CreatedBy("created_by"),

       title_field = "title",
       summary_fields = "summary"
)

table("comment", d, ## notes for each user
      ManyToOne("entity", "_core_entity"),
      Created("created_date"),
      CreatedBy("created_by"),
      Text("note", length = 4000),

      valid_entities = "ticket"
)

table("bookmarks",d,

    Integer("entity_id"),
    Integer("user_id"),
    Text("bookmark"),
    Text("title"),
    Text("entity_table"),
    DateTime("accessed_date")
)

table("severity", d,
      Text("severity", mandatory = True),
      Text("desctiption", length = 2000),
      Created("created_date"), ## when data was gathered
      CreatedBy("created_by"),
      lookup = True
)

table("priority", d,
      Text("priority", mandatory = True),
      Text("desctiption", length = 2000),
      Created("created_date"), ## when data was gathered
      CreatedBy("created_by"),
      lookup = True,
      title_field = "priority",
)

## application user tables

entity("user",d,

    Text("name"),
    Boolean("active", default = True, mandatory = True),
    Boolean("locked", default = False),
    Text("login_name", mandatory = True),
    Text("password"),
    Email("email"),
    DateTime("last_logged_in"),
    Text("notes", length = 4000),
    Text("about_me", length = 4000),

    Created("created_date"),
    CreatedBy("created_by"),

    Index("login_name_index", "login_name", unique = True),

    table_type = "system",
)

entity("user_group",d,

    Text("groupname", mandatory = True),
    Text("description", length = 200),
    Text("notes", length = 4000),
    Boolean("active", default = True, mandatory = True),

    table_type = "system",
    title_field = 'groupname'
)

table("user_group_user",d,

    LookupId("user", "user"),
    LookupId("user_group", "user_group"),

    table_type = "system"
)

table("user_group_permission",d,

    ##TODO Sort out backref problems
    LookupId("user_group_name", "user_group"),
    LookupId("permission_name", "permission"),
    table_type = "system"
)


table("permission",d,

    Text("permission"),
    Text("description", length = 200),
    Text("long_description", length = 4000),
    table_type = "system",
    title_field = 'permission'
)

table("_system_info",d,

    Text("key", length = 100, mandatory = True),
    Text("value", length = 2000),
    Integer("type", default = 1),
    table_type = "system"
)

d.persist()




