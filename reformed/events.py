from custom_exceptions import InvalidEvent, DependencyError
from sqlalchemy.orm import attributes
import sqlalchemy as sa
from sqlalchemy.sql import func, select, and_, cast
from operator import add
import datetime
import custom_exceptions
import logging

LOGGER = logging.getLogger('reformed.main')

class Event(object):

    def __init__(self, event_cause, *actions):

        self.event_causes = event_cause.split()
        self.actions = actions

    def _set_parent(self, table):

        for event_cause in self.event_causes:
            table.events[event_cause].extend(self.actions)

    def code_repr(self):
        action_repr_list = [action.code_repr() for action in self.actions]

        return ("Event(" + " ". join(self.event_causes) + ",\n        " 
                + ",\n        ".join(action_repr_list) + "\n    )")



class EventState(object):

    def __init__(self, object, session, event_type):

        self.object = object
        self.session = session
        self.event_type = event_type

    def __repr__(self):
        return "event type: %s, object: %s" % (self.event_type, self.object)



