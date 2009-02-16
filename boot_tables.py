from tables import Table
import fields


boot_tables = [Table("__table", fields.Text("name"),
                            fields.OneToMany("table_params","__table_params"),
                            fields.OneToMany("field","__field")
                           ),
               Table("__table_params", fields.Text("item"),
                            fields.Text("values")),
               Table("__field", fields.Text("name"),
                            fields.Text("other"))
              ]
