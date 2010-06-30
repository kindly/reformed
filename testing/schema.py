## This is a blank schema template

from reformed.database import table, entity, relation
from reformed.fields import *
from reformed.events import Event
from reformed.actions import *


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
           Image('Image', generator = dict(params = dict(category = 'donkey'))),
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
           Email('email'),
           Text('sex', generator = dict(name = 'sex')),
           Image('Image'),
           Text('street', generator = dict(name = 'road')),
           Text('town', generator = dict(name = 'town')),
           Text('postcode', generator = dict(name = 'postcode')),
           Text('notes', length = 1000),
           Boolean('active'),
           LookupId('LookupIdx', "colour", generator = 'skip', many_side_not_null = False),

           Event('new,change', CopyValue('Image', '_core_entity.thumb')),

           title_field = 'name',
           summary_fields = 'email, notes',

    )

    database.persist()




