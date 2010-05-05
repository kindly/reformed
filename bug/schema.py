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

# define defaults
from predefine import sysinfo
sysinfo("public", True, "Allow unregistered users to use the application")
sysinfo("name", 'Reformed Application', "Name of the application")

d =  global_session.database

entity('ticket', d,

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

table("comment", d, ## notes for each user
      ManyToOne("entity", "_core_entity"),
      Created("created_date"),
      CreatedBy("created_by"),
      Text("note", length = 4000),

      valid_entities = "ticket"
)

relation("involvement", d,
      LookupId("role", "code", filter_field = "code_type"),
      Created("created_date"),
      CreatedBy("created_by"),

      valid_entities1 = "ticket",
      valid_entities2 = "user,usergroup",
      table_type = "system",
)


table("role", d, ## notes for each user
      Text("name", mandatory = True),
      Text("desctiption", length = 2000),
      valid_entities = "ticket",
      table_type = "system",
)


table("bookmarks",d,

    Integer("entity_id"),
    Integer("user_id"),
    Text("bookmark"),
    Text("title"),
    Text("entity_table"),
    DateTime("accessed_date"),
    table_type = "system",
)

table("code", d,
      Text("name", mandatory = True),
      Text("desctiption", length = 2000),
      LookupTextValidated("code_type", "code_type.code_type"),
      Boolean("active", default = True),
      Created("created_date"), 
      CreatedBy("created_by"),
      lookup = True,

      table_type = "system",
      title_field = "name"
)

table("code_type", d,
      Text("code_type", mandatory = True),
      Text("name", mandatory = True),
      Text("desctiption", length = 2000),
      Created("created_date"), 
      CreatedBy("created_by"),
      table_type = "system",
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

    title_field = 'name',
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



table("page",d,
    Text("page", length = 50, mandatory = True),
    Text("title", length = 200, mandatory = True),
    Text("body", length = 8000),
    table_type = "system"
)

entity('upload', d,
    Text("filename", mandatory = True),
    Text("path"),
    Created("created_date"),
    CreatedBy("created_by"),

    title_field = "filename",
    summary_fields = "filename"
)

d.persist()




