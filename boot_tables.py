from tables import Table
import fields


boot_tables = [Table("__table", fields.Text("table_name"),
                            fields.OneToMany("table_params","__table_params"),
                            fields.OneToMany("field","__field"),
                            primary_key = "table_name"
                           ),
               Table("__table_params", fields.Text("item"),
                            fields.Text("value")),
               Table("__field", fields.Text("name"),
                            fields.Text("type"),
                            fields.Text("other"))
              ]
