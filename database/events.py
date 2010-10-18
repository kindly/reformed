import logging

LOGGER = logging.getLogger('reformed.main')

class Event(object):

    def __init__(self, event_cause, *actions, **kw):

        self.event_causes = event_cause.split()
        self.actions = actions
        self.field_id = kw.get("field_id", None)

    def _set_parent(self, table):

        if not self.field_id:
            new_id = table.max_field_id + 1
            table.max_field_id = new_id
            self.field_id = new_id
        else:
            table.max_field_id = max(table.max_field_id, self.field_id)
        table.field_list.append(self)

    def _set_actions(self, table):

        database = table.database

        for event_cause in self.event_causes:
            for action in self.actions:
                if not action.event_id:
                    new_event_id = database.max_event_id + 1
                    database.max_event_id = new_event_id
                    action._kw["event_id"] = new_event_id
                    action.event_id = new_event_id
                else:
                    new_max = max(database.max_event_id, action.event_id)
                    database.max_event_id = new_max

                table.events[event_cause].append(action)


    def code_repr(self):
        action_repr_list = [action.code_repr() for action in self.actions]

        return ("Event('" + " ".join(self.event_causes) + "',\n        "
                + ",\n        ".join(action_repr_list) + ",\n        "
                + "field_id = %s)" % self.field_id)



class EventState(object):

    def __init__(self, object, session, event_type):

        self.object = object
        self.session = session
        self.event_type = event_type

    def __repr__(self):
        return "event type: %s, object: %s" % (self.event_type, self.object)



