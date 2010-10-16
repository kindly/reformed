import logging

LOGGER = logging.getLogger('reformed.main')

class Event(object):

    def __init__(self, event_cause, *actions):

        self.event_causes = event_cause.split()
        self.actions = actions

    def _set_parent(self, table):

        for event_cause in self.event_causes:
            table.events[event_cause].extend(self.actions)


class EventState(object):

    def __init__(self, object, session, event_type):

        self.object = object
        self.session = session
        self.event_type = event_type

    def __repr__(self):
        return "event type: %s, object: %s" % (self.event_type, self.object)



