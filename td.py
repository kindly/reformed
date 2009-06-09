import reformed.reformed as r


d = r.reformed

d.add_table(r.Table("entity",
                     r.Integer("table"),
                     r.Integer("table_id"),
                     )
            )

d.add_entity(r.Table("people",
                    r.Text("name", mandatory = True, length = 30),
                    r.Address("supporter_address"),
                    r.OneToMany("email","email",
                              order_by = "email",
                              eager = True,
                              cascade = "all, delete-orphan"),
                    r.OneToMany("donkey_sponsership",
                              "donkey_sponsership")
                   )
           )

d.add_table(r.Table("email",
                    r.Email("email")
                   )
           )

d.add_entity(r.Table("donkey",
                    r.Text("name", validation = '__^[a-zA-Z0-9]*$'),
                    r.Integer("age", validation = 'Int'),
                    r.OneToOne("donkey_pics","donkey_pics",
                             many_side_mandatory = False,
                             ),
                    r.OneToMany("donkey_sponsership",
                              "donkey_sponsership")
                   )
           )

d.add_table(r.Table("donkey_pics",
                    r.Binary("pic"),
                    r.Text("pic_name")
                   )
           )

d.add_table(r.Table("donkey_sponsership",
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

d.add_table(r.Table("form", r.Text("name"),
                   r.OneToMany("form_param","form_param"), r.OneToMany("form_item","form_item")))

d.add_table(r.Table("form_param", r.Text("key", mandatory = True, length = 30), r.Text("value", mandatory = True, length = 30)))

d.add_table(r.Table("form_item" ,r.Text("name") ,
                   r.Text("label"),r.Text("item"),r.Boolean('active'),r.Integer('sort_order'),
                                  r.OneToMany("form_item_param","form_item_param")))



d.add_table(r.Table("form_item_param", r.Text("key"),r.Text("value")))

d.persist()
