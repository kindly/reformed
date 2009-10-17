import reformed.reformed as r


d = r.reformed


d.add_entity(r.Table("people",
                    r.Text("name", mandatory = True, length = 30),
                    r.Address("supporter_address"),
                    r.OneToMany("email","email",
                              order_by = "email",
                              eager = True,
                              cascade = "all, delete-orphan"),
                    r.OneToMany("donkey_sponsership",
                              "donkey_sponsership",
                              many_side_not_null = False
)
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
                             many_side_not_null = False
                             ),
                    r.OneToMany("donkey_sponsership",
                              "donkey_sponsership",
                                many_side_not_null = False)
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

d.add_table(r.Table("_core_lock",
              r.Text("table_name"),
              r.Integer("row_id"),
              r.DateTime("date"),
              r.UniqueConstraint("unique", "table_name,row_id,date"),
              logged = False)
           )


d.persist()

from reformed.data_loader import FlatFile
flatfile = FlatFile(d,
                    "people",
                    "tests/new_people_with_header.csv")    
flatfile.load()

