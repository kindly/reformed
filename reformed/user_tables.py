from reformed.fields import *
from reformed.database import table, entity

from global_session import global_session
d = global_session.database

import predefine

entity("user",d,

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

d.persist()

sys_admin = d.get_instance("user")
sys_admin.name = u"admin"
sys_admin.login_name = u"admin"
sys_admin.password = u"admin"
sys_admin.active = True
sys_admin.created_by = 1
sys_admin._modified_by = 1


##        admin_group = database.get_instance("user_group")
##        admin_group.groupname = u"admin"
##        admin_group.created_by = 1
##        admin_group._modified_by = 1
##        admin_group.active = True

##        user_group_user = database.get_instance("user_group_user")
##        user_group_user.user = sys_admin
##        user_group_user.user_group = admin_group

session = d.Session()
session.add(sys_admin)
##        session.add(user_group_user)
##        session.add(admin_group)
session.commit()

predefine.user_group('admin', 'System Administrators')

