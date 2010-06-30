from custom_exceptions import DependencyError
from sqlalchemy.orm import attributes
import sqlalchemy as sa
from sqlalchemy.sql import func, select, and_, cast
from operator import add
import datetime
import custom_exceptions
import logging


class PersistBaseClass(object):

    def __new__(cls, *args, **kw):

        obj = object.__new__(cls)
        obj._args = list(args)
        obj._kw = kw.copy()
        obj._class_name = cls.__name__

        return obj


class Action(PersistBaseClass):

    post_flush = False

    def __call__(self, action_state):

        self.run(action_state)
            
class AddRow(Action):

    def __init__(self, related_table, pre_flush = True):

        self.related_table = related_table
        self.pre_flush = pre_flush

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session

        path = table.get_path(self.related_table)

        if len(path) != 1:
            raise custom_exceptions.InvalidTableReferenceValue(
                "table %s not one join away from objects table %s" % 
                (self.related_table, table.name))

        new_obj = database[self.related_table].sa_class()

        setattr(object, path[0], new_obj)
        session.save(new_obj)


class DeleteRow(Action):

    def __init__(self, related_table):

        self.related_table = related_table

    def run(self, action_state):

        object = action_state.object

        table = object._table
        database = table.database
        session = action_state.session

        path = table.get_path(self.related_table)

        if len(path) != 1:
            raise custom_exceptions.InvalidTableReferenceValue(
                "table %s not one join away from objects table %s"
                % (self.related_table, table.name))

        to_delete = getattr(object, path[0])

        session.delete(to_delete)


class SumEvent(Action):

    def __init__(self, result_field, number_field):

        self.result_field = result_field
        self.number_field = number_field

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        path = table.get_path_from_field(self.result_field)
        result_field = self.result_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None


        value = getattr(object, self.number_field)

        new_table = new_obj._table

        if event_type == "delete":
            diff = -value
        elif event_type == "new":
            diff = value
        elif event_type == "change":
            a, b, c = attributes.get_history(
                attributes.instance_state(object),
                self.number_field,
                passive = False
            )
            if not c:
                return
            diff = value - c[0]
        else:
            return


        setattr(new_obj, result_field,
                new_table.sa_table.c[result_field] + diff)

        action_state.session.save(new_obj)



class CountEvent(Action):

    def __init__(self, result_field, number_field):

        self.result_field = result_field
        self.number_field = number_field

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        path = table.get_path_from_field(self.result_field)
        result_field = self.result_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None

        new_table = new_obj._table

        if event_type == "delete":
            diff = -1
        elif event_type == "new":
            diff = 1
        else:
            return

        setattr(new_obj, result_field,
                new_table.sa_table.c[result_field] + diff)

        action_state.session.save(new_obj)

class MaxDate(Action):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(MaxDate, self).__init__(target, field, base_level, initial_event, **kw)

        self.end = kw.get("end", "end_date") 
        self.default_end = kw.get("default_end", datetime.datetime(2199,12,31))

    def update_after(self, object, result, session):

        join = self.get_parent_primary_keys(object)
        end_date_field = object._table.sa_table.c[self.end]
        setattr(result, self.field_name,
                select([func.max(func.coalesce(end_date_field, self.default_end))],
                       and_(*join))
               )
        session.save(result)


class Counter(Action):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(Counter, self).__init__(target, field, base_level, initial_event, **kw)

    def update_after(self, object, result, session):

        relation_attr = self.target_to_base_path[0]

        join_tuples = self.get_join_tuples(relation_attr, object._table, self.base_level)

        target_table = self.database.tables[self.target_table].sa_table.alias()

        join_keys = [key[0] for key in join_tuples]

        key_values = [target_table.c[key] == getattr(object, key) for key in join_keys]

        setattr(object, self.field_name,
                select([select([func.max(func.coalesce(target_table.c[self.field_name], 0)) + 1],
                       and_(*key_values)).alias()])
               )

        session.save(object)

    def add(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))

    def delete(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))
            
    def update(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))


class CopyValue(Action):


    def __init__(self, src_field, dest_field, **kw):

        self.dest_field = dest_field
        self.src_field = src_field

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database

        path = table.get_path_from_field(self.dest_field)
        dest_field = self.dest_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None

        value = getattr(object, self.src_field)

        setattr(new_obj, dest_field, value)
        action_state.session.save(new_obj)
 

class CopyTextAfter(Action):

    ##TODO rename class and update_initial method

    def __init__(self, result_field, fields, **kw):

        self.result_field = result_field

        #self.changed_flag = kw.get("changed_flag", None)
        #self.update_when_flag = kw.get("update_when_flag" , None)

        self.field_list = [s.strip() for s in fields.split(",")]

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database

        path = table.get_path_from_field(self.result_field)
        result_field = self.result_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None
        
        values = [getattr(object, field) for field in self.field_list]

        value = u' '.join([val for val in values if val])

        ## Truncate value if too long for field
        length = new_obj._table.fields[result_field].length
        if value:
            value = value[:length]

        setattr(new_obj, result_field, value)
        action_state.session.save(new_obj)

class CopyTextAfterField(CopyTextAfter):

    ## rename class and update_initial method

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database

        path = table.get_path_from_field(self.result_field)
        result_field = self.result_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None
        
        values = [getattr(object, field) for field in self.field_list]

        values = [u"%s: %s" % (field, getattr(object, field)) for field in self.field_list]

        value = u' -- '.join([val for val in values if val])

        ## Truncate value if too long for field
        length = new_obj._table.fields[result_field].length
        if value:
            value = value[:length]

        setattr(new_obj, result_field, value)
        action_state.session.save(new_obj)


class CopyText(Action):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(CopyText, self).__init__(target, field, base_level, initial_event, **kw)

        self.fields = kw.get("field_list", self.target_field)
        self.changed_flag = kw.get("changed_flag", None)
        self.update_when_flag = kw.get("update_when_flag" , None)
        self.counter = kw.get("counter", "counter") 


    def add_event(self, database):

        super(CopyText, self).add_event(database)

        self.field_list_all = [s.strip() for s in self.fields.split(",")]

        self.field_list = []
        self.table_field_list = []

        for field in self.field_list_all:
            if field.count(".") == 1:
                self.table_field_list.append(field.split("."))
            else:
                self.field_list.append(field)

        target_table = self.database.tables[self.target_table]


    def update_after(self, object, result, session):

        join = self.get_parent_primary_keys(object)


        target_table = self.database.tables[self.target_table]

        rows = session.query(target_table.sa_class).filter(*join).all()

        text_list = []

        for row in rows:
            for field in self.field_list:
                text = getattr(row, field)
                if text:
                    text_list.append(text)

            for table, field in self.table_field_list:
                obj = reduce(getattr, target_table.local_tables[table], row)
                text = getattr(obj, field)
                if text:
                    text_list.append(text)

        setattr(result, self.field_name, " ".join(text_list))

        if self.changed_flag:
            setattr(result, self.changed_flag, True)

        session.save(result)

    def add(self, result, base_table_obj, object, session):
        session.add_after_flush(self.update_after, (object, result, session))

    def delete(self, result, base_table_obj, object, session):
        session.add_after_flush(self.update_after, (object, result, session))

    def update(self, result, base_table_obj, object, session):
        session.add_after_flush(self.update_after, (object, result, session))

    def update_all(self, session):

        innerjoins = []

        target_to_base_cond = self.join_condition_of_path(self.target_table,
                                                   self.target_to_base_path)

        for join_holder in target_to_base_cond:
            innerjoins.append(join_holder)

        base_to_result_cond = self.join_condition_of_path(self.base_table,
                                                          [self.relation])

        for join_holder in base_to_result_cond:
            innerjoins.append(join_holder)
        
        join_statement = innerjoins[0].table1
        for join_holder in innerjoins:
             join_statement = join_holder.apply_join_conditions(join_statement)



        target_table = self.database.tables[self.target_table].sa_table

        max_counter = select([func.max(target_table.c[self.counter])]).execute().fetchone()[0]
        if not max_counter:
            return

        fields = [func.coalesce(target_table.c[field], "") for field in self.field_list]

        for table, field in self.table_field_list:
            sa_table = self.database.tables[table].sa_table
            fields.append(func.coalesce(sa_table.c[field], ""))


        first_join_cond = target_to_base_cond[0]

        lookup_paths = {}
        for table, field in self.table_field_list:
            lookup_paths[table] = self.database.tables[self.target_table].local_tables[table]


        distinct_lookup_path = []

        for table, path in lookup_paths.iteritems():
            duplicate = False
            for other_table, other_path in lookup_paths.iteritems():
                if table == other_table:
                    continue
                if list(path) == list(other_path)[:len(path)]:
                    duplicate = True

            if not duplicate:
                distinct_lookup_path.append(path)


        current_table = target_table
        for path in distinct_lookup_path:
            join_holders = self.join_condition_of_path(self.target_table, path)
            for join_holder in join_holders:
                current_table = join_holder.table2
                join_condition = join_holder.join_conditions()
                join_statement = join_statement.join(current_table, and_(*join_condition))
        

        for num in range(1, max_counter + 1):
            if num == 1:
                continue
            aliased_table = first_join_cond.alias(1)
            join_condition = first_join_cond.join_conditions()

            join_statement = join_statement.outerjoin(aliased_table,
                                                      and_(aliased_table.c[self.counter] == num,
                                                      *join_condition))
            current_table = aliased_table
            for path in distinct_lookup_path:
                join_holders = self.join_condition_of_path(self.target_table, path)
                for join_holder in join_holders:
                    join_holder.table1 = current_table
                    current_table = join_holder.alias(2)
                    for table, field in self.table_field_list:
                        if current_table.original.name == table:
                            fields.append(func.coalesce(current_table.c[field], ""))
                    join_condition = join_holder.join_conditions()
                    join_statement = join_statement.outerjoin(current_table, and_(*join_condition))

            fields.extend([func.coalesce(aliased_table.c[field], "") for field in self.field_list])

        fields_concat = [field + u' ' for field in fields[:-1]] 
        fields_concat.append(fields[-1])
        fields_concat = reduce(add, fields_concat)
        
        if self.update_when_flag:
            condition_column = target_table.c[self.update_when_flag]
            statement= select([fields_concat], condition_column, from_obj = join_statement)
        else:
            statement= select([fields_concat], from_obj = join_statement)

        if self.changed_flag:
            session.query(self.table.sa_class).update({self.field_name: statement,
                                                       self.changed_flag: True})
        else:
            session.query(self.table.sa_class).update({self.field_name: statement})

