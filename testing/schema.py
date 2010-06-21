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

    entity('table1', database,
           Text('text'),
           Integer('int'),
           Text('longtext', length = 1000),
           Password('password'),
           DateTime('DateTime'),
           Image('Image'),
           Boolean('Boolean'),
           Money('Money'),
           Email('Email'),
           Date('Date'),
           LookupId('LookupId', "colour"),

           title_field = 'text',
    )

    entity('people', database,
           Text('name', generator = dict(name = 'full_name')),
           Date('dob', generator = dict(name = 'dob')),
           Integer('age', generator = dict(params = dict(min = 16, max = 110))),
           Text('street', generator = dict(name = 'road')),
           Text('town', generator = dict(name = 'town')),
           Text('postcode', generator = dict(name = 'postcode')),
           Text('notes', length = 1000),
           Boolean('active'),
           title_field = 'name',
    )

    database.persist()




