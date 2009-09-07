from custom_exceptions import InvalidEvent
from sqlalchemy.orm import attributes
from sqlalchemy.sql import func, select, and_
from operator import add
import datetime
import logging

LOGGER = logging.getLogger('reformed.main')

class ChangeEvent(object):
    
    def __init__(self, target, field, base_level = None, initial_event = False):

        self.field = field
        if target.count(".") == 1:
            self.target_table, self.target_field = target.split(".")
        else:
            self.target_table, self.target_field = target, None
        self.table = None

        self.base_level = base_level
        self.initial_event = initial_event

    def add_event(self, database):

        self.database = database

        target_table = database.tables[self.target_table]

        self.table = self.field.table

        if self.base_level is None:
            self.base_table = target_table
        else:
            self.base_table = self.database.tables[self.base_level]

        relation_path, self.relation_type = self.base_table.table_path[self.table.name]
        if len(relation_path) > 1:
            raise InvalidEvent(("updated table can not be more then one"
                                "join away from base table"))
        self.relation = relation_path[0]

        if target_table == self.base_table:
            self.target_to_base_path = []
        else:
            self.target_to_base_path = target_table.table_path[self.base_table.name][0]

        if self.initial_event:
            target_table.initial_events.append(self)
            #target_table.initial_events.insert(0, self)
        else:
            target_table.events.append(self)

    def get_parent_primary_keys(self, object):


        #target and base table are the same. [] will be ignored by sqlalchemy
        if not self.target_to_base_path:
            return [object.id == object._table.sa_table.c.id] 

        relation_attr = self.target_to_base_path[0]
        parent_table_obj = getattr(object, relation_attr)
            

        parent_table = parent_table_obj._table
        table = object._table
        relation = table.relation_attributes[relation_attr]

        if relation.table == table:
            join_keys = relation.this_table_join_keys
        if relation.table == parent_table:
            join_keys = relation.this_table_join_keys[::-1]

        join_keys_combined = zip(join_keys[0],join_keys[1])

        join =  [getattr(parent_table_obj, key[1]) ==\
                 table.sa_table.c[key[0]]\
                 for key in join_keys_combined]
        
        return join


    def insert_action(self, session, object):

        if self.base_level:
            base_table_obj = object
            for attribute in self.target_to_base_path:
                base_table_obj = getattr(base_table_obj, attribute)
                if base_table_obj._table.name == "_core_entity" and base_table_obj.table <> self.base_table.table_id:
                    return
        else:
            base_table_obj = object


        result = getattr(base_table_obj, self.relation)

        # hook supplied by subclass
        self.add(result, base_table_obj, object, session)

    def delete_action(self, session, object):

        if self.base_level:
            base_table_obj = reduce(getattr, self.target_to_base_path, object)
        else:
            base_table_obj = object

        result = getattr(base_table_obj, self.relation)

        # hook supplied by subclass
        self.delete(result, base_table_obj, object, session)

    def update_action(self, session, object):

        if self.base_level:
            base_table_obj = reduce(getattr, self.target_to_base_path, object)
        else:
            base_table_obj = object


        result = getattr(base_table_obj, self.relation)

        # hook supplied by subclass
        self.update(result, base_table_obj, object, session)


class AddRow(ChangeEvent):

    def add(self, result, base_table_obj, object, session, initial_event = True):

        new_obj = self.table.sa_class()
        setattr(base_table_obj, self.relation, new_obj)
        session.save(new_obj)

    def delete(self, result, base_table_obj, object, session):

        pass

    def update(self, result, base_table_obj, object, session):

        pass


class SumEvent(ChangeEvent):

    def add(self, result, base_table_obj, object, session):

        value = getattr(object, self.target_field)

        setattr(result, self.field.name, self.table.sa_table.c[self.field.name] + value)

        session.add(result)


    def delete(self, result, base_table_obj, object, session):

        value = getattr(object, self.target_field)

        setattr(result, self.field.name, self.table.sa_table.c[self.field.name] - value)

        session.add(result)

    def update(self, result, base_table_obj, object, session):

        value = getattr(object, self.target_field)

        a, b, c = attributes.get_history(attributes.instance_state(object), self.target_field,
                                         passive = False)
        if not c:
            return

        diff = value - c[0]

        setattr(result, self.field.name, self.table.sa_table.c[self.field.name] + diff)

        session.add(result)

class CountEvent(ChangeEvent):

    def add(self, result, base_table_obj, object, session):

        value = getattr(object, self.target_field)

        setattr(result, self.field.name, self.table.sa_table.c[self.field.name] + 1)

        session.add(result)

    def delete(self, result, base_table_obj, object, session):

        value = getattr(object, self.target_field)

        setattr(result, self.field.name, self.table.sa_table.c[self.field.name] - 1)

        session.add(result)

    def update(self, result, base_table_obj, object, session):
        return

class MaxDate(ChangeEvent):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(MaxDate, self).__init__(target, field, base_level, initial_event)

        self.end = kw.get("end", "end_date") 
        self.default_end = kw.get("default_end", "2199,12,31")

    def update_after(self, object, result, session):

        join = self.get_parent_primary_keys(object)
        end_date_field = object._table.sa_table.c[self.end]
        setattr(result, self.field.name,
                select([func.max(func.coalesce(end_date_field, datetime.datetime(2199,12,31)))],
                       and_(*join))
               )
        session.save(result)

    def add(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))

    def delete(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))
            
    def update(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))


class CopyTextAfter(ChangeEvent):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(CopyTextAfter, self).__init__(target, field, base_level, initial_event)

        fields = kw.get("field_list", self.target_field)
        self.changed_flag = kw.get("changed_flag", None)
        self.update_when_flag = kw.get("update_when_flag" , None)

        self.field_list = [s.strip() for s in fields.split(",")]

    def update_after(self, object, result, session):


        join = self.get_parent_primary_keys(object)
        fields = [object._table.sa_table.c[field] + u' ' for field in self.field_list] 
        fields_concat = reduce(add, fields)
        
        if self.update_when_flag:
            condition_column = object._table.sa_table.c[self.update_when_flag]

            setattr(result, self.field.name,
                    select([fields_concat],
                           and_(condition_column, *join))
                   )
        else:
            setattr(result, self.field.name,
                    select([fields_concat],
                           and_(*join))
                   )

        if self.changed_flag:
            setattr(result, self.changed_flag, True)
        
        session.save(result)

    def add(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))

    def delete(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))
            
    def update(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))

class CopyText(ChangeEvent):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(CopyText, self).__init__(target, field, base_level, initial_event)

        fields = kw.get("field_list", self.target_field)
        self.changed_flag = kw.get("changed_flag", None)
        self.update_when_flag = kw.get("update_when_flag" , None)

        self.field_list = [s.strip() for s in fields.split(",")]


    def update_after(self, object, result, session):

        if self.update_when_flag and getattr(result, self.update_when_flag):
            setattr(result, self.field.name, u" ".join([getattr(result, field) for field in self.field_list]))
        if not self.update_when_flag:
            setattr(result, self.field.name, u" ".join([getattr(object, field) for field in self.field_list]))

        if self.changed_flag:
            setattr(result, self.changed_flag, True)

    def add(self, result, base_table_obj, object, session):
        session.add_after_flush(self.update_after, (object, result, session))

    def delete(self, result, base_table_obj, object, session):
        return

    def update(self, result, base_table_obj, object, session):
        session.add_after_flush(self.update_after, (object, result, session))

