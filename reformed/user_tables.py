from reformed.fields import *

class UserTables(object):

    def __init__(self, rdatabase):
        
        if "user" in rdatabase.tables:
            return

        d = rdatabase

        from reformed.database import *

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

        table("permission",d,

            Text("permission"),
            Text("description", length = 200),
            Text("long_description", length = 4000),
            table_type = "system",
            title_field = 'permission'
        )

        rdatabase.persist()
