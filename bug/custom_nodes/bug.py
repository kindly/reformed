from node import TableNode
from page_item import *
from form import form
from global_session import global_session
r = global_session.database


def initialise():

    predefine = global_session.application.predefine
    # priority codes
    predefine.code_type(u'priority', u'Ticket priority', u'How important')
    predefine.code(u'Low', u'priority', u'low priority', u'Not very important')
    predefine.code(u'Medium', u'priority', u'medium priority', u'Not very important')
    predefine.code(u'High', u'priority', u'high priority', u'Not very important')
    # severity codes
    predefine.code_type(u'severity', u'Ticket severity', u'How important')
    predefine.code(u'Low ', u'severity', u'low severity', u'Not very important')
    predefine.code(u'Medium ', u'severity', u'medium severity', u'Not very important')
    predefine.code(u'High ', u'severity', u'high severity', u'Not very important')

class Ticket(TableNode):

    main = form(
        input('title'),
        layout('hr'),
        layout('column_start'),
        input('accepted'),
        input('complete_by'),
        layout('column_next'),
        input('code_severity_id', default = 'low severity', label = "severity:"),
        input('code_priority_id', default = 'low priority', label = "priority:"),
        layout('column_end'),
        layout('hr'),
        wmd('summary', css = 'large'),
        file_upload('attachment'),
        extra_data(["created_by"]),
        table = "ticket",
        params =  {"form_type": "action"},
        title_field = 'title',

        save_redirect = "bug.ListTicket:view"
    )

    list_title = 'ticket %s'


class ListTicket(TableNode):

    main = form(
        input('title'),
        textarea('summary',css = "large"),
        layout('box_start'),
        layout('column_start'),
        input('accepted'),
        input('complete_by' ),
        layout('column_next'),
        dropdown_code('code_severity_id', True, label = "severity:"),
        input('code_priority_id', label = "priority:"),
        layout('column_end'),
        layout('box_end'),
        button('bug.Ticket:edit:{id}' ,label = 'edit', permissions = ['logged_in']), 
        layout('hr'),
        subform('old_comments'),
        subform('comment'),
        buttons("view", False),

        table = "ticket",
        params =  {"form_type": "normal"},
        title_field = 'title',
    )

    old_comments = form(
        wmd('note', label = "", css = "large"),
        layout('area_start', css = 'record_info'),
        layout('area_end'),
        text('Created {created_date:ds} by user #{created_by}', css = 'record_info'),

        extra_data(["created_by", "created_date"]),

        parent_id = "_core_entity_id",
        child_id = "_core_entity_id",
        table = "comment",
        params = {"form_type": "continuous"},
        read_only = True
    )

    comment = form(

        wmd('note', label = "", css = "large"),
        button('bug.ListTicket:_save:', label = 'add comment'),

        parent_id = "_core_entity_id",
        child_id = "_core_entity_id",
        table = "comment",
        params ={"form_type": "action"}
    )

    list_title = 'ticket %s'

    def save(self, node_token):
        self["comment"].save(node_token)
        node_token.action = "redirect"
        node_token.link = "bug.ListTicket:view:__id=%s" % node_token.data.get("_core_entity_id")
        # FIXME this is stupid
        node_token.next_node = None


class Permission(TableNode):

    main = form(
        layout("box_start"),
        info("permission"),
        input("name", css = 'large'),
        textarea("description", css = 'large'),

        table = "permission",
        params =  {"form_type": "action"},
        title_field = 'name'
    )



class SysInfo(TableNode):

    main = form(
        input('key'),
        input('value'),
        dropdown_code('type', dict(keys = [1, 2, 3], descriptions = ['String', 'Integer', 'Boolean'])),

        table = "_system_info",
        params =  {"form_type": "action"},
        title_field = 'key',

    )

class Page(TableNode):

    main = form(
        input("page", css = "large", description = "A reference for the page used for links etc."),
        input("title", css = "large", description = "The displayed title for the page."),
        wmd("body", css = "large long", description = "A longer more detailed description"),

        table = "page",
        params =  {"form_type": "action"},
        title_field = 'title'
    )

    view_form = form( 
        info('title'),
        info('body'),

        buttons('view', False),

        table = "page",
        params =  {"form_type": "action"},
        title_field = 'title'
    )

    def view(self, node_token):
        where = 'page = %s' % node_token.data.get("page")
        self["view_form"].view(node_token, where = where)


