import logging
import datetime

from sqlalchemy.orm import attributes
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
import sqlalchemy as sa
from sqlalchemy.sql import func, select, and_, cast
from operator import add

import custom_exceptions

logger = logging.getLogger('rebase.actions')

class PersistBaseClass(object):

    def __new__(cls, *args, **kw):

        obj = object.__new__(cls)
        obj._args = list(args)
        obj._kw = kw.copy()
        obj._class_name = cls.__name__

        return obj


class Action(PersistBaseClass):

    post_flush = False

    def __new__(cls, *arg, **kw):
        obj = PersistBaseClass.__new__(cls, *arg, **kw)
        obj.event_id = None
        if "event_id" in kw:
            obj.event_id = kw.pop("event_id")
        return obj

    def __call__(self, action_state):
        
        logger.info(self.__class__.__name__)
        logger.info(action_state)
        self.run(action_state)
            
class AddRow(Action):

    def __init__(self, related_table, pre_flush = True, **kw):

        self.related_table = related_table
        self.pre_flush = pre_flush

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session

        path = table.get_path(self.related_table)

        if len(path) != 1:
            raise custom_exceptions.InvalidTableReference(
                "table %s not one join away from objects table %s" % 
                (self.related_table, table.name))

        new_obj = database[self.related_table].sa_class()

        setattr(object, path[0], new_obj)
        session.add_no_validate(new_obj)


class DeleteRows(Action):

    def __init__(self, related_table, **kw):

        self.related_table = related_table

    def run(self, action_state):

        object = action_state.object

        table = object._table
        database = table.database
        session = action_state.session

        path = table.get_path(self.related_table)
        new_obj = object

        for item in path:
            to_delete = getattr(new_obj, item)
            new_obj = to_delete
            session.delete(to_delete)


class SumEvent(Action):

    def __init__(self, result_field, number_field, **kw):

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

        action_state.session.add_no_validate(new_obj)



class CountEvent(Action):

    def __init__(self, result_field, number_field, **kw):

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

        action_state.session.add_no_validate(new_obj)

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
        session.add_no_validate(result)

class AddCommunication(Action):

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        communication = object._rel_communication

        if not communication:
            core = None
            communication = database.get_instance("communication")
            communication.communication_type = table.name
            object._rel_communication = communication
            core_store = session.object_store.get("core")
            core = session.query(database["_core"]).get(object._core_id)
            communication._rel__core = core
        elif event_type == 'delete':
            session.delete(communication)
            return

        if hasattr(object, "defaulted") and object.defaulted:
            communication.defaulted_date = datetime.datetime.now()

        session.add_no_validate(communication)
        session.add_no_validate(object)
        session.add_no_validate(core)


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

        session.add_no_validate(object)

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
        action_state.session.add_no_validate(new_obj)
 

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
        action_state.session.add_no_validate(new_obj)

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
        action_state.session.add_no_validate(new_obj)


class UpdateCommunicationInfo(Action):

    post_flush = True

    def __init__(self, fields, display_name = None, **kw):

        self.fields = fields
        self.display_name = display_name
        self.seperator = kw.get("seperator", "\n")
        self.name = kw.get("name")
        self.only_latest = kw.get("only_latest", False)

    def make_text(self, object):

        values = []

        for field in self.fields:
            value = getattr(object, field)
            if value:
                values.append(value)

        return self.seperator.join(values)

    def set_names(self, table):

        if not self.display_name:
            self.display_name = table.name
        if not self.name:
            if len(self.fields) == 1:
                self.name = self.fields[0]
            else:
                self.name = table.name

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        ## optimisation
        defaulted = object.__dict__.get("defaulted")
        if not defaulted and event_type == "new":
            return

        self.set_names(table)

        communication = object._rel_communication
        core = communication._rel__core
        core_id = core.id

        ##check to see this has not already been run
        for stored_info_obj in session.object_store["communication_info"]:
            if (stored_info_obj._core_id == core_id and
                stored_info_obj.table_name == table.name and
                stored_info_obj.name == self.name):
                return

        query = {
            "communication._core_id": core_id,
            "communication.defaulted_date": ("<>", None),
            "communication.active": 1,
        }


        result = database.search(
            table.name,
            query,
            session = session,
            order_by = 'communication.defaulted_date desc',
            first = True
        )

        default_obj = result.results[0]

        try:
            query = {
                "_core_id": core_id,
                "table_name": table.name,
                "name": self.name
            }
            result = database.search_single(
                "summary_info",
                query,
                session = session,
            )
            info_obj = result.results[0]
        except custom_exceptions.SingleResultError:
            info_obj = None

        if not info_obj:
            if not default_obj:
                return
            info_obj = database.get_instance("summary_info")
            info_obj.table_name = table.name
            info_obj.name = self.name
            info_obj.display_name = self.display_name
            info_obj._core_id = core.id
        ##TODO  check this works.  It makes sure that if the current object is
        ## then there will be no default.
        elif (self.only_latest and info_obj.original_id == object.id):
            if not default_obj or default_obj.id <> object.id:
                session.delete(info_obj)

        elif not default_obj:
            session.delete(info_obj)
            return

        text = self.make_text(default_obj)
        info_obj.original_id = default_obj.id
        info_obj.value = text
        session.object_store["communication_info"].add(info_obj)
        session.add_no_validate(info_obj)
        session.add_no_validate(core)


class UpdateSearch(Action):

    post_flush = True

    def __init__(self, fields, index_type = "text",
                 type = None, name = None, **kw):

        self.fields = fields
        self.name = name
        self.type = type or index_type

        self.cleaner = getattr(self, self.type)

        self.index_type = index_type
        self.weight = kw.get("weight", None)
        self.stem = kw.get("stem", False)

    def text(self, txt):
        return unicode(txt.lower())

    def datetime(self, date):
        return date.date().isoformat()

    def only_numbers(self, txt):
        chars = []
        for char in txt:
            try:
                int(char)
                chars.append(char)
            except ValueError:
                continue
        return "".join(chars)

    def upper_no_space(self, txt):
        return txt.upper().replace(" ", "")

    def make_text(self, object):

        values = []

        for field in self.fields:
            value = getattr(object, field)
            if value:
                values.append(self.cleaner(value))

        return " ".join(values)

    def set_names(self, table):

        if not self.name:
            if len(self.fields) == 1:
                self.name = self.fields[0]
            else:
                self.name = table.name

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        self.set_names(table)

        search_obj = None
        if event_type <> "new": 
            try:
                query = dict(
                    _core_id = object._core_id,
                    table = table.table_id,
                    field = self.event_id,
                    original_id = object.id)
                result = database.search_single("search_info",
                                                query,
                                                session = session
                                               )
                search_obj = result.results[0]
            except custom_exceptions.SingleResultError:
                pass

        if not search_obj:
            search_obj = database.get_instance("search_info")
            search_obj.table = table.table_id
            search_obj.field = self.event_id
            search_obj._core_id = object._core_id
        else:
            if event_type == 'delete':
                session.delete(search_obj)
                return

        text = self.make_text(object)
        if not text and event_type == 'new':
            return

        search_pending = database.get_instance("search_pending")
        search_pending._core_id = object._core_id
        session.add_no_validate(search_pending)

        search_obj.original_id = object.id
        search_obj.value = text
        session.add_no_validate(search_obj)
