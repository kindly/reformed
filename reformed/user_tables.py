from reformed.fields import *
from reformed.database import table, entity
import authenticate


def initialise(application):

    database = application.database

    table("_core", database,
        Text("type"),
        ForeignKey("primary_entity_id", "_core_entity", ),
        ForeignKey("secondary_entity_id", "_core_entity", ),
        modified_by = False,
        modified_date = False
         )



    table("_core_entity", database,
        Text("table"),
        Text("title"),
        Text("summary"),
        Integer("thumb"),
        ModifiedByNoRelation("modified_by"),
        table_type = "internal",
        summary = u'The entity table',
        lookup = True,  
        modified_by = False
    )


    entity("user",database,

        Text("name"),
        Boolean("active", default = True, mandatory = True),
        Boolean("locked", default = False),
        Text("login_name", mandatory = True),
        Text("auto_login", length = 100),
        Password("password"),
        Email("email"),
        DateTime("last_logged_in"),
        Text("notes", length = 4000),
        Text("about_me", length = 4000),

        Created("created_date"),
        CreatedBy("created_by"),

        UniqueIndex("login_name_index", "login_name"),

        title_field = 'name',
        table_type = "system",
        default_node = 'user.User',
    )

    entity("user_group",database,

        Text("groupname"),
        Text("name", mandatory = True),
        Text("description", length = 200),
        Text("notes", length = 4000),
        Boolean("active", default = True, mandatory = True),
        Integer("access_level", default = 0),
        default_node = 'user.UserGroup',

        table_type = "system",
        title_field = 'name'
    )

    table("user_group_user",database,

        LookupId("user_id", "user"),
        LookupId("user_group_id", "user_group"),

        table_type = "system"
    )

    table("user_group_permission",database,

        ##TODO Sort out backref problems
        LookupId("user_group_id", "user_group"),
        LookupId("permission_id", "permission"),
        table_type = "system"
    )

    table("permission",database,

        Text("permission"),
        Text("name", length = 200),
        Text("description", length = 4000),
        Integer("access_level", default = 0),
        table_type = "system",
        title_field = 'name'
    )

    table("bookmarks",database,

        Integer("entity_id"),
        Integer("user_id"),
        Text("bookmark"),
        Text("title"),
        Text("entity_table"),
        DateTime("accessed_date"),
        table_type = "system",
    )

    table("code", database,
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

    table("code_type", database,
          Text("code_type", mandatory = True),
          Text("name", mandatory = True),
          Text("desctiption", length = 2000),
          Created("created_date"),
          CreatedBy("created_by"),
          table_type = "system",
    )


## application user tables


    table("page",database,
        Text("page", length = 50, mandatory = True),
        Text("title", length = 200, mandatory = True),
        Text("body", length = 8000),
        table_type = "system"
    )

    entity('upload', database,
        Text("filename", mandatory = True),
        Text("category"),
        Text("title"),
        Text("path"),
        Text("mimetype"),
        Integer("size"),
        Boolean("thumb", default = False),
        Created("created_date"),
        CreatedBy("created_by"),

        title_field = "filename",
        summary_fields = "filename",

        table_type = "system",
    )

    database.persist()


    # permission

    # add admin user
    # this is a special case as no other users should be auto created
    data = dict(name = u"admin",
                created_by = 1,
                _modified_by = 1,
                active = True,
                auto_login = authenticate.create_auto_login_id(),
                password = u"admin")
    application.predefine.add_data("user", "login_name", u"admin", data)

    # sys admin user_group
    application.predefine.permission("SysAdmin", u'System Administrators', u'Administer the system.', 2)
    application.predefine.user_group(u'SysAdmins', u'System Administrators', u'Full system access', permissions = ['SysAdmin'], access_level = 2)

    # this is a special case too
    # make admin a sysadmin
    data = dict(created_by = 1,
                _modified_by = 1,
                user_id = 1,
                user_group_id = 1,)
    application.predefine.add_data("user_group_user", "user_id", 1, data)
