import formencode as fe
from formencode import validators
import node
from node import TableNode, Node, AutoForm
from .reformed.reformed import reformed as r
import sqlalchemy as sa
from global_session import global_session
from .reformed import reformed as table_functions

class Ticket(TableNode):

    table = "ticket"
    form_params =  {"form_type": "action"}
    title_field = 'title'

    fields = [
        ['title', 'Text', 'title:'],
        ['accepted', 'Boolean', 'accepted:', {"dropdown" : True, "autocomplete" : ["true", "false"]}],
        ['complete_by', 'Date', 'complete by:'],
        ['summary', 'Text', 'summary:', {"control" : "textarea", "css" : "large"}],
        ['button', 'submit', 'add ticket', {'control' : 'button', 'action': '_save', 'node': 'bug.Ticket'}]
    ]
    list_title = 'ticket %s'

class ListTicket(TableNode):

    table = "ticket"
    form_params =  {"form_type": "normal"}
    title_field = 'title'

    fields = [
        ['title', 'Text', 'title:'],
        ['accepted', 'Boolean', 'accepted:', {"dropdown" : True, "autocomplete" : ["true", "false"]}],
        ['complete_by', 'Date', 'complete by:'],
        ['summary', 'Text', 'summary:', {"control" : "textarea", "css" : "large"}],
        ['comment', 'subform', 'comment']
    ]

    subforms = {
        'comment':{
            'fields': [
                ['note', 'Text', 'note:', {"control" : "textarea", "css" : "large"}],
                ['button', 'submit', 'add comment', {'control' : 'button', 'action': '_save', 'node': 'bug.ListTicket'}]
            ],
            "parent_id": "_core_entity_id",
            "child_id": "_core_entity_id",
            "table": "comment",
            "params":{
                "form_type": "action"
            }
        }
    }

    list_title = 'ticket %s'
