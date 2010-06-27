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

        self.event_cause = event_cause
        self.actions = actions

    def _set_parent(self, table):

        table.events[self.event_cause].extend(self.actions)


class EventState(object):

    def __init__(self, object, session):

        self.object = object
        self.session = session



