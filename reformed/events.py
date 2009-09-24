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
        if not target:
            self.target_table, self.target_field = None, None
        elif target.count(".") == 1:
            self.target_table, self.target_field = target.split(".")
        else:
            self.target_table, self.target_field = target, None

        ## get table when event is added    
        self.table = None

        self.base_level = base_level
        self.initial_event = initial_event

    def add_event(self, database):

        self.database = database


        self.table = self.field.table

        if not self.target_table:
            self.target_table = self.table.name

        target_table = database.tables[self.target_table]

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
        else:
            target_table.events.append(self)

    def get_parent_primary_keys(self, object):

        if not self.target_to_base_path:
            return [object.id == object._table.sa_table.c.id] 

        relation_attr = self.target_to_base_path[0]
        parent_table_obj = getattr(object, relation_attr)

        parent_table = parent_table_obj._table
        table = object._table

        join_tuples = self.get_join_tuples(relation_attr, table, parent_table)

        join =  [getattr(parent_table_obj, key[1]) ==\
                 table.sa_table.c[key[0]]\
                 for key in join_tuples]
        
        return join
    
    def get_join_tuples(self, relation_name, this_table, other_table):

        if isinstance(this_table, basestring):
            this_table = self.database.tables[this_table]
        if isinstance(other_table, basestring):
            other_table = self.database.tables[other_table]

        relation = this_table.relation_attributes[relation_name]


        if relation.table == this_table:
            join_keys = relation.this_table_join_keys
        if relation.table == other_table:
            join_keys = relation.this_table_join_keys[::-1]

        return zip(join_keys[0],join_keys[1])

    def join_condition_of_path(self, start_table, path):

        if path == []:
            return
        join_cond = []

        if isinstance(start_table, basestring):
            start_table = self.database.tables[start_table]

        for index, attribute in enumerate(path):
            if index == 0:
                current_table = start_table
                new_table = start_table.paths[(path[index],)][0]
            else:
                current_table = start_table.paths[tuple(path[:index])][0]
                new_table = start_table.paths[tuple(path[:index+1])][0]


            tuples = self.get_join_tuples(attribute, current_table, new_table)

            condition_holder = self.join_conditions(tuples, current_table, new_table)

            join_cond.append(condition_holder)
                                                                                   
        return join_cond


    def join_conditions(self, tuples, current_table, new_table):

        if not isinstance(current_table, basestring):
            current_table = current_table.sa_table.name
        if not isinstance(new_table, basestring):
            new_table = new_table.sa_table.name

        return JoinConditionHolder(self.database, current_table, new_table, tuples)

    def join_condition_result_to_base(self):

        all_conditions = []

        target_to_base_cond = self.join_condition_of_path(self.target_table,
                                                   self.target_to_base_path)
        if target_to_base_cond:
            for join_holder in target_to_base_cond:
                all_conditions.extend(join_holder.join_conditions())


        base_to_result_cond = self.join_condition_of_path(self.base_table,
                                                          [self.relation])

        for join_holder in base_to_result_cond:
            all_conditions.extend(join_holder.join_conditions())

        return all_conditions


    def insert_action(self, session, object):

        if self.base_level:
            base_table_obj = object
            ## check to see if entity table is related to correct table
            for attribute in self.target_to_base_path:
                base_table_obj = getattr(base_table_obj, attribute)
                if base_table_obj._table.name == "_core_entity" and\
                   base_table_obj.table <> self.base_table.table_id and\
                   self.base_level <> "_core_entity" :
                    return
        else:
            base_table_obj = object


        result = getattr(base_table_obj, self.relation)

        # hook supplied by subclass
        self.add(result, base_table_obj, object, session)

    def delete_action(self, session, object):

        if self.base_level:
            base_table_obj = object
            ## check to see if entity table is related to correct table
            for attribute in self.target_to_base_path:
                base_table_obj = getattr(base_table_obj, attribute)
                if base_table_obj._table.name == "_core_entity" and\
                   base_table_obj.table <> self.base_table.table_id and\
                   self.base_level <> "_core_entity" :
                    return
        else:
            base_table_obj = object

        result = getattr(base_table_obj, self.relation)

        # hook supplied by subclass
        self.delete(result, base_table_obj, object, session)

    def update_action(self, session, object):

        if self.base_level:
            base_table_obj = object
            ## check to see if entity table is related to correct table
            for attribute in self.target_to_base_path:
                base_table_obj = getattr(base_table_obj, attribute)
                if base_table_obj._table.name == "_core_entity" and\
                   base_table_obj.table <> self.base_table.table_id and\
                   self.base_level <> "_core_entity" :
                    return
        else:
            base_table_obj = object


        result = getattr(base_table_obj, self.relation)

        # hook supplied by subclass
        self.update(result, base_table_obj, object, session)


class JoinConditionHolder(object):

    def __init__(self, database, table1, table2, join_keys):

        self.database = database

        self.table1_name = table1
        self.table2_name = table2

        self.join_keys = join_keys

        self.table1 = database.tables[table1].sa_table
        self.table2 = database.tables[table2].sa_table

    def alias(self, table):

        if table == 1:
            self.table1 = self.table1.alias()
            return self.table1

        if table == 2:
            self.table2 = self.table2.alias()
            return self.table2

    def join_conditions(self):

        join_conditions = []

        for key in self.join_keys:
            join_conditions.append(self.table1.c[key[0]] == self.table2.c[key[1]])

        return join_conditions

    def apply_join_conditions(self, table):

        join_conditions = self.join_conditions()

        return table.join(self.table2, and_(*join_conditions))


    def join_statement(self):

        join_conditions = self.join_conditions()

        return self.table1.join(self.table2, and_(*join_conditions))

    def outerjoin_statment(self):

        join_conditions = self.join_conditions()

        return self.table1.outerjoin(self.table2, and_(*join_conditions))
            
class AddRow(ChangeEvent):

    def add(self, result, base_table_obj, object, session, initial_event = True):

        new_obj = self.table.sa_class()
        setattr(base_table_obj, self.relation, new_obj)
        session.save(new_obj)

    def delete(self, result, base_table_obj, object, session):

        pass

    def update(self, result, base_table_obj, object, session):

        pass

    def update_all(self, session):

        session.query(self.table.sa_class).delete()

        join_tuple = self.get_join_tuples(self.relation, self.base_table, self.table)

        primary_keys = [self.base_table.sa_table.c[field[0]] for field in join_tuple]

        ids = session.query(*primary_keys).all()

        for row in ids:
            new = self.table.sa_class()
            for number, field in enumerate(row):
                setattr(new, join_tuple[number][1], field)
            session.save(new)

        session.commit()

            

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

    def update_all(self, session):

        all_cond = self.join_condition_result_to_base()

        target_table = self.database.tables[self.target_table].sa_table

        statement = select([func.sum(target_table.c[self.target_field])],
                           and_(*all_cond))

        session.query(self.table.sa_class).update({self.field.name :statement})


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

    def update_all(self, session):

        all_cond = self.join_condition_result_to_base()

        target_table = self.database.tables[self.target_table].sa_table

        statement = select([func.count(target_table.c["id"])],
                           and_(*all_cond))

        session.query(self.table.sa_class).update({self.field.name :statement})


class MaxDate(ChangeEvent):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(MaxDate, self).__init__(target, field, base_level, initial_event)

        self.end = kw.get("end", "end_date") 
        self.default_end = kw.get("default_end", datetime.datetime(2199,12,31))

    def update_after(self, object, result, session):

        join = self.get_parent_primary_keys(object)
        end_date_field = object._table.sa_table.c[self.end]
        setattr(result, self.field.name,
                select([func.max(func.coalesce(end_date_field, self.default_end))],
                       and_(*join))
               )
        session.save(result)

    def add(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))

    def delete(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))
            
    def update(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))

    def update_all(self, session):

        all_cond = self.join_condition_result_to_base()

        target_table = self.database.tables[self.target_table].sa_table

        end_date_field = target_table.c[self.end]

        statement = select([func.max(func.coalesce(end_date_field, self.default_end))],
                           and_(*all_cond))

        session.query(self.table.sa_class).update({self.field.name :statement})


class Counter(ChangeEvent):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(Counter, self).__init__(target, field, base_level, initial_event)

    def update_after(self, object, result, session):

        relation_attr = self.target_to_base_path[0]

        join_tuples = self.get_join_tuples(relation_attr, object._table, self.base_level)

        target_table = self.database.tables[self.target_table].sa_table.alias()

        join_keys = [key[0] for key in join_tuples]

        key_values = [target_table.c[key] == getattr(object, key) for key in join_keys]

        setattr(object, self.field.name,
                select([select([func.max(func.coalesce(target_table.c[self.field.name], 0)) + 1],
                       and_(*key_values)).alias()])
               )

        session.save(object)

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
        fields = [func.coalesce(object._table.sa_table.c[field], "") + u' ' 
                  for field 
                  in self.field_list[:-1]] 
        fields.append(func.coalesce(object._table.sa_table.c[self.field_list[-1]], ""))
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

    def update_all(self, session):

        all_cond = self.join_condition_result_to_base()

        target_table = self.database.tables[self.target_table].sa_table

        fields = [func.coalesce(target_table.c[field], "") + u' ' for field in self.field_list[:-1]] 
        fields.append(func.coalesce(target_table.c[self.field_list[-1]], ""))
        fields_concat = reduce(add, fields)
        
        if self.update_when_flag:
            condition_column = target_table.c[self.update_when_flag]
            statement= select([fields_concat], and_(condition_column, *all_cond))
        else:
            statement= select([fields_concat], and_(*all_cond))


        if self.changed_flag:
            session.query(self.table.sa_class).update({self.field.name: statement,
                                                       self.changed_flag: True})
        else:
            session.query(self.table.sa_class).update({self.field.name: statement})


class CopyText(ChangeEvent):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(CopyText, self).__init__(target, field, base_level, initial_event)

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

        setattr(result, self.field.name, " ".join(text_list))

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
            session.query(self.table.sa_class).update({self.field.name: statement,
                                                       self.changed_flag: True})
        else:
            session.query(self.table.sa_class).update({self.field.name: statement})

