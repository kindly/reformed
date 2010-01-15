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


import reformed.reformed as r
from reformed.database import table, entity
from reformed.fields import *


d =  r.reformed


entity("people",d,

    Text("name", mandatory = True, length = 50),
    DateTime("dob"),
    Boolean("active"),
    Address("supporter_address"),
    OneToMany("email","email",
              order_by = "email",
              eager = True),
    OneToMany("donkey_sponsorship",
              "donkey_sponsorship",
              many_side_not_null = False
               ),

    summary_fields = "name,address_line_1,postcode"
)

table("email",d,

    Email("email")
)

entity("user",d,

    Text("name"),
    Text("password"),

    primary_key = "name",
    table_type = "system"
)

table("user_group",d,

    Text("groupname"),

    primary_key = "groupname",
    table_type = "system"
)

table("user_group_user",d,

    ManyToOne("user", "user"),
    ManyToOne("user_group", "user_group"),

    table_type = "system"
)

table("user_group_permission",d,

    ManyToOne("user_group", "user_group"),
    ManyToOne("permissionx", "permission"),
      
    table_type = "system"
)


table("permission",d,

    Text("permission"),

    primary_key = "permission",
    table_type = "system"
)

entity("donkey",d,

    Text("name"), #validation = '__^[a-zA-Z0-9 ]*$'),
    Integer("age", validation = 'Int'),
    OneToOne("donkey_pics","donkey_pics",many_side_not_null = False),
    OneToMany("donkey_sponsorship", "donkey_sponsorship", many_side_not_null = False),

    summary_fields = "name,age"
)

table("donkey_pics",d,

    Binary("pic"),
    Text("pic_name")
)

table("donkey_sponsorship",d,

    Money("amount"),
    Date("giving_date"),

    entity_relationship = True
)

table("paymentdds",d,

    Date("giving_date"),
    Money("amount"),
    Text("source")
)

table("bookmarks",d,

    Integer("entity_id"),
    Integer("user_id"),
    Text("bookmark"),
    Text("title"),
    Text("entity_table"),
    DateTime("accessed_date")
)

d.persist()
