from node import TableNode

class Ticket(TableNode):

    table = "ticket"
    form_params =  {"form_type": "action"}
    title_field = 'title'

    fields = [
        ['title', 'Text', 'title:'],
        ['', '', '', dict(layout = 'hr')],
        ['', '', '', dict(layout = 'column_start')],
        ['accepted', 'Boolean', 'accepted:', {"control" : "dropdown", "autocomplete" : ["true", "false"]}],
        ['complete_by', 'Date', 'complete by:'],
        ['', '', '', dict(layout = 'column_next')],
        ['severity', 'Text', 'severity:', {"control" : "dropdown", "autocomplete" : True}],
        ['', '', '', dict(layout = 'column_end')],
        ['', '', '', dict(layout = 'hr')],
        ['summary', 'Text', 'summary:', {"control" : "textarea", "css" : "large"}],
        ['button', 'submit', 'add ticket', {'control' : 'button', 'action': '_save', 'node': 'bug.Ticket'}]
    ]
    list_title = 'ticket %s'

    def view(self, read_only = False):

        self.next_node = "bug.ListTicket"
        self.next_data = dict(data = self.data,
                              command = "view")

class ListTicket(TableNode):

    table = "ticket"
    form_params =  {"form_type": "normal"}
    title_field = 'title'

    fields = [
        ['title', 'Text', 'title:'],
        ['accepted', 'Boolean', 'accepted:', {"control" : "dropdown", "autocomplete" : ["true", "false"]}],
        ['complete_by', 'Date', 'complete by:'],
        ['summary', 'Text', 'summary:', {"control" : "textarea", "css" : "large"}],
        ['severity', 'Text', 'severity:', {"control" : "dropdown", "autocomplete" : True}],
        ['old_comments', 'subform', 'old_comments'],
        ['comment', 'subform', 'comment']
    ]

    subforms = {
        'old_comments':{
            'fields': [
                ['created_date', 'DateTime', 'Date Created: '],
                ['note', 'Text', '', {"control" : "textarea", "css" : "large"}],
            ],
            "parent_id": "_core_entity_id",
            "child_id": "_core_entity_id",
            "table": "comment",
            "params":{
                "form_type": "continuous"
            }
        },

        'comment':{
            'fields': [
                ['note', 'Text', 'note:', {"control" : "textarea", "css" : "large"}],
                ['moo', 'Boolean', 'moo:', {"control" : "checkbox"}],
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

    def save(self):

        super(ListTicket, self).save()
        self.action = "redirect"
        print "-&"*5, self.data
        self.link = "bug.ListTicket:view:__id=%s" % self.data.get("_core_entity_id")

