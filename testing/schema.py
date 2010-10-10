## This is a blank schema template

from reformed.database import table, entity, relation, info_table
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

    entity('donkey', database,
           Text('text'),
           Integer('int'),
           Text('longtext', length = 1000),
           Password('password'),
           DateTime('DateTime'),
           Thumb('image', generator = dict(params = dict(category = 'donkey'))),
           Boolean('Boolean'),
           Money('Money'),
           Email('Email'),
           Date('Date'),
           LookupId('LookupId', "colour"),

           Event('new change', CopyValue('image', 'primary_entity._core_entity.thumb')),
           title_field = 'text',
           default_node = 'test.Node5',
    )

    entity('people', database,
           Text('name', generator = dict(name = 'full_name')),
           Date('dob', generator = dict(name = 'dob')),
           Integer('age', generator = dict(params = dict(min = 16, max = 110))),
           Email('email', description = 'email address or something'),
           Text('sex', generator = dict(name = 'sex')),
           Thumb('image'),
           Text('street', generator = dict(name = 'road')),
           Text('town', generator = dict(name = 'town')),
           Text('postcode', generator = dict(name = 'postcode')),
           Text('notes', length = 1000),
           Boolean('active'),
           LookupId('colour', many_side_not_null = False, generator = dict(name = 'lookup', params = dict(table = 'colour' , field = 'id'))),

           Event('new change', CopyValue('image', 'primary_entity._core_entity.thumb')),

           title_field = 'name',
           summary_fields = 'email, notes',
           default_node = 'test.People',
           valid_info_tables = "communication membership"
    )

    info_table('communication', database,
          Text('communication_type'),
    )

    table('telephone', database,
          ForeignKey('communication_id', 'communication'),
          Text('number', generator = dict(name = 'phone')),
          Event('new delete', AddCommunication()),
          table_class = 'communication',
    )

    info_table('membership', database,
          Text('membership_type'),
          Money('amount'),
          DateTime('start_date'),
          DateTime('end_date'),
    )

    relation('sponsership', database,
          Money('amount'),
          DateTime('start_date'),
          DateTime('end_date'),
          primary_entities = 'people',
          secondary_entities = 'donkey',
          valid_info_tables = 'membership'
    )

    database.persist()
