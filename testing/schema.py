## This is a blank schema template

from reformed.database import table, entity, relation
from reformed.fields import *


def initialise(application):

    sysinfo = application.predefine.sysinfo
    sysinfo("public", True, "Allow unregistered users to use the application")
    sysinfo("name", 'Reformed Application', "Name of the application")

    database = application.database

    table('colour', database,
          Text('name'),
          Text('hex'),

          title_field = 'name',
    )

    database.persist()




