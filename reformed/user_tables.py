from reformed.fields import *
from reformed.database import table, entity


def initialise(application):

    database = application.database


    table("_core_entity", database,
        Text("table"),
        Text("title"),
        Text("summary"),
        ModifiedByNoRelation("modified_by"),
        table_type = "internal",
        summary = u'The entity table',
        modified_by = False
    )


    entity("user",database,

        Text("name"),
        Boolean("active", default = True, mandatory = True),
        Boolean("locked", default = False),
        Text("login_name", mandatory = True),
        Password("password"),
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

    entity("user_group",database,

        Text("groupname", mandatory = True),
        Text("name", mandatory = True),
        Text("description", length = 200),
        Text("notes", length = 4000),
        Boolean("active", default = True, mandatory = True),


        table_type = "system",
        title_field = 'name'
    )

    table("user_group_user",database,

        LookupId("user", "user"),
        LookupId("user_group", "user_group"),

        table_type = "system"
    )

    table("user_group_permission",database,

        ##TODO Sort out backref problems
        LookupId("user_group_name", "user_group"),
        LookupId("permission_name", "permission"),
        table_type = "system"
    )

    table("permission",database,

        Text("permission"),
        Text("name", length = 200),
        Text("description", length = 4000),
        table_type = "system",
        title_field = 'name'
    )

    database.persist()


    # permission
    application.predefine.permission("sysadmin", u'System Administrators', u'Administer the system.')

    # add admin user
    # this is a special case as no other users should be auto created
    data = dict(name = u"admin",
                created_by = 1,
                _modified_by = 1,
                active = True,
                password = u"admin")
    application.predefine.add_data("user", "login_name", u"admin", data)

    # sys admin user_group
    application.predefine.user_group(u'admin', u'System Administrators', u'Full system access', permissions = ['sysadmin'])

    # this is a special case too
    # make admin a sysadmin
    data = dict(created_by = 1,
                _modified_by = 1,
                user_id = 1,
                user_group_id = 1,)
    application.predefine.add_data("user_group_user", "user_id", 1, data)
