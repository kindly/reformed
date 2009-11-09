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
                    r.Text("password")
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

d.add_table(r.Table("_core_lock",
              r.Text("table_name"),
              r.Integer("row_id"),
              r.DateTime("date"),
              r.UniqueConstraint("unique", "table_name,row_id,date"),
              logged = False)
           )


d.persist()



