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


d = r.reformed


d.add_entity(r.Table("people",
                    r.Text("name", mandatory = True, length = 50),
                    r.DateTime("dob"),
                    r.Boolean("active"),
                    r.Address("supporter_address"),
                    r.OneToMany("email","email",
                              order_by = "email",
                              eager = True),
                    r.OneToMany("donkey_sponsorship",
                              "donkey_sponsorship",
                              many_side_not_null = False
                               ),
                    summary_fields = "name,address_line_1,postcode"

                   )
           )

d.add_table(r.Table("email",
                    r.Email("email")
                   )
           )

d.add_entity(r.Table("user",
                    r.Text("name"),
                    r.Text("password"),
                    primary_key = "name",
                    table_type = "system"
                  )
           )

d.add_table(r.Table("user_group",
                    r.Text("groupname"),
                    primary_key = "groupname",
                    table_type = "system"
                  )
           )

d.add_table(r.Table("user_group_user",
                    r.ManyToOne("user", "user"),
                    r.ManyToOne("user_group", "user_group"),
                    table_type = "system"
                 )
           )

d.add_table(r.Table("user_group_permission",
                    r.ManyToOne("user_group", "user_group"),
                    r.ManyToOne("permissionx", "permission"),
                    table_type = "system"
                   )
           )


d.add_table(r.Table("permission",
                    r.Text("permission"),
                    primary_key = "permission",
                    table_type = "system"
                   )
           )

d.add_entity(r.Table("donkey",
                    r.Text("name"), #validation = '__^[a-zA-Z0-9 ]*$'),
                    r.Integer("age", validation = 'Int'),
                    r.OneToOne("donkey_pics","donkey_pics",
                             many_side_not_null = False
                             ),
                    r.OneToMany("donkey_sponsorship",
                              "donkey_sponsorship",
                                many_side_not_null = False),
                    summary_fields = "name,age"
                   )
           )

d.add_table(r.Table("donkey_pics",
                    r.Binary("pic"),
                    r.Text("pic_name")
                   )
           )

d.add_table(r.Table("donkey_sponsorship",
                    r.Money("amount"),
                    r.Date("giving_date"),
                    entity_relationship = True
                   )
           )

d.add_table(r.Table("paymentdds",
                    r.Date("giving_date"),
                    r.Money("amount"),
                    r.Text("source")
                   )
           )


d.persist()



