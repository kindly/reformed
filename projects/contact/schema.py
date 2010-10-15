## This is a blank schema template

from database.database import table, entity, relation, info_table
from database.fields import *
from database.events import Event
from database.actions import *


def initialise(application):

    sysinfo = application.predefine.sysinfo
    sysinfo("public", True, "Allow unregistered users to use the application")
    sysinfo("name", 'Reformed Application', "Name of the application")

    database = application.database

    table('search_info', database,
               Integer('_core_id'),
               Integer('table'),
               Integer('field'),
               Integer('original_id'),
               Text('value', length = 1000),
               Index('main_query', "_core_id, table, field, original_id"),
               modified_date = False,
               modified_by = False,
               version = False,
              )

    table('search_pending', database,
               Integer('_core_id'),
               Created('created'),
               modified_date = False,
               modified_by = False,
               version = False,
              )

    info_table('summary_info', database,
               Text('table_name'),
               Text('name'),
               Text('display_name'),
               Integer('original_id'),
               Text('value', length = 1000))

    info_table('note', database,
               Text('note', length = 1000),
               )

    entity('people', database,
           Text('name', generator = dict(name = 'full_name')),
           Text('preferred_name'),
           Text('alterative_name'),
           Text('salutation'),
           LookupId('gender', "code", filter_field = "code_type"),
           LookupId('source'),
           Date('dob', generator = dict(name = 'dob')),
           Created('created'),
           CreatedBy('created_by'),
           Thumb('image'),
           Event('new change', CopyValue('image', 'primary_entity._core_entity.thumb')),
           Event('new change delete',
                UpdateSearch(['name'])
                ),
           Event('new change delete',
                UpdateSearch(['dob'], "datetime")
                ),
           title_field = 'name',
           default_node = 'new_person.People',
           valid_info_tables = "communication summary_info note"
    )

    table("source", database,
          Text("code", length = 200),
          Text("code_desc", length = 400),
          Created('created'),
          CreatedBy('created_by'),
          lookup = True,
    )

    info_table('communication', database,
               Text('communication_type'),
               DateTime('defaulted_date'),
               Boolean('active', default = True),
               Text('description', length = 1000),
               Index('latest_com', "_core_id, defaulted_date, active"),
               Created('created'),
               CreatedBy('created_by'),
    )

    table('telephone', database,
          Integer("_core_id", mandatory = True),
          ForeignKey('communication_id', 'communication'),
          Text('number', generator = dict(name = 'phone')),
          Event('new', AddCommunication()),
          Event('new change delete',
                UpdateCommunicationInfo(['number'])),
          Event('new change delete',
                UpdateSearch(['number'], 
                              type = 'only_numbers')),
          table_class = 'communication',
    )

    table('email', database,
          Integer("_core_id", mandatory = True),
          ForeignKey('communication_id', 'communication'),
          Email('email', mandatory = True),
          Event('new', AddCommunication()),
          Event('new change delete',
                UpdateCommunicationInfo(['email'])),
          Event('new change delete',
                UpdateSearch(['email'])),
          table_class = 'communication',
    )

    table('address', database,
          Integer("_core_id", mandatory = True),
          ForeignKey('communication_id', 'communication'),
          Text('address_line_1', generator = dict(name = 'road')),
          Text('address_line_2'),
          Text('address_line_3'),
          Text('address_line_4'),
          Text('town', generator = dict(name = 'town')),
          Text('country'),
          Text('postcode', generator = dict(name = 'postcode')),
          Boolean('gone_away'),
          Event('new', AddCommunication()),
          Event('new change delete',
                UpdateCommunicationInfo(['address_line_1', 'town', 'postcode'])),
          Event('new change delete',
                UpdateSearch(['postcode'], type = "upper_no_space")),
          table_class = 'communication',
    )

    database.persist()
