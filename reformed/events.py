from custom_exceptions import InvalidEvent
from sqlalchemy.orm import attributes
import logging

LOGGER = logging.getLogger('reformed.main')

class ChangeEvent(object):
    
    def __init__(self, target, field, base_level = None):

        self.field = field
        if target.count(".") == 1:
            self.target_table, self.target_field = target.split(".")
        else:
            self.target_table, self.target_field = target, None
        self.table = None

        self.base_level = base_level

    def add_event(self, database):

        target_table = database.tables[self.target_table]

        self.table = self.field.table

        if self.base_level is None:
            if len(self.table.tables_with_relations) <> 1:
                raise InvalidEvent(("aggregate table can with no declared" 
                                   "base can only be joined to one base table"))

            table, relation = self.table.tables_with_relations.popitem()

            if relation.other <> self.table.name or relation.type <> "onetoone":
                raise InvalidEvent(("aggregate table must be joined to base"
                                    "table with a onetoone join"))

            self.base_table = relation.table
            self.relation = relation.name
            self.relation_type = relation.type
        else:
            self.base_table = self.database[self.base_level]
            relation_path, self.relation_type = self.base_table.table_path[self.table.name]
            if len(relation_path) > 1:
                raise InvalidEvent(("updated table can not be more then one"
                                    "join away from base table"))
            self.relation = relation_path[0]

        self.target_to_base_path = target_table.table_path[self.base_table.name][0]

        target_table.events.append(self)


    def insert_action(self, session, object):

        value = getattr(object, self.target_field)

        base_table_obj = reduce(getattr, self.target_to_base_path, object)

        result = getattr(base_table_obj, self.relation)

        # hook supplied by subclass
        result = self.add(result, base_table_obj, value, None, session)

        session.add(result)

    def delete_action(self, session, object):

        value = getattr(object, self.target_field)

        base_table_obj = reduce(getattr, self.target_to_base_path, object)

        result = getattr(base_table_obj, self.relation)

        # hook supplied by subclass
        self.delete(result, base_table_obj, value, None, session)

        session.add(result)

    def update_action(self, session, object):

        value = getattr(object, self.target_field)

        a, b, c = attributes.get_history(attributes.instance_state(object), self.target_field,
                                         passive = False)
        if not c:
            return

        base_table_obj = reduce(getattr, self.target_to_base_path, object)

        result = getattr(base_table_obj, self.relation)

        self.update(result, base_table_obj, value, c[0], session)

        session.add(result)


class SumEvent(ChangeEvent):

    def add(self, result, base_table_obj, value, old_value, session):

        if result:
            setattr(result, self.field.name, self.table.sa_table.c[self.field.name] + value)
        else:
            result = self.table.sa_class()
            setattr(result, self.field.name, value)
            setattr(base_table_obj, self.relation, result)

        return result

    def delete(self, result, base_table_obj, value, old_value, session):

        setattr(result, self.field.name, self.table.sa_table.c[self.field.name] - value)

    def update(self, result, base_table_obj, value, old_value, session):

        diff = value - old_value

        setattr(result, self.field.name, self.table.sa_table.c[self.field.name] + diff)

class CountEvent(ChangeEvent):

    def add(self, result, base_table_obj, value, old_value, session):

        if result:
            setattr(result, self.field.name, self.table.sa_table.c[self.field.name] + 1)
        else:
            result = self.table.sa_class()
            setattr(result, self.field.name, 1)
            setattr(base_table_obj, self.relation, result)

        return result

    def delete(self, result, base_table_obj, value, old_value, session):

        setattr(result, self.field.name, self.table.sa_table.c[self.field.name] - 1)

    def update(self, result, base_table_obj, value, old_value, session):
        return

