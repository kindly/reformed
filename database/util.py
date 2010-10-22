import datetime
import decimal
import os
import time
import errno

import formencode as fe

import data_loader

JOINS_DEEP = 6

# root_dir holds the root directory of the application
root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
root_dir = os.path.normpath(root_dir)

class Holder(object):
    def __init__(self, **kw):
        self.__dict__ = kw


def get_dir(file = None, extra_path = None):

    """path from parent directory of this this file
    file:
        file to be added to end of path
    extra path:
        path from this directory"""

    global root_dir

    if not file:
        if extra_path:
            return os.path.join(root_dir, extra_path)
        else:
            return root_dir
    if extra_path:
        return os.path.join(os.path.join(root_dir, extra_path), file)
    else:
        return os.path.join(root_dir, file)


def swap_relations(relation_type):
    if relation_type == "onetomany":
        return "manytoone"
    if relation_type == "manytoone":
        return "onetomany"
    return "onetoone"

def file_length(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def check_two_entities(tables, node, rtables):
    if node == "_core":
        counter = 0
        for table in tables[::-1]:
            if rtables[table].name == "_core":
                return False
            if rtables[table].entity:
                counter = counter + 1
                if counter == 2:
                    return True
        return False
    if rtables[node].entity:
        counter = 0
        for table in tables[::-1]:
            if rtables[table].entity:
                counter = counter + 1
            if rtables[table].name == "_core":
                if counter > 0:
                    return True
                else:
                    return False
        return False

def last_entity(tables, rtables):
    for table in tables[::-1]:
        if rtables[table].entity:
            return table


class Edge(object):

    def __init__(self, node, node1 = None, node2 =  None,
                 tables = None, path = None, path_no_rel = None,
                 name_changes = None, relation = None,
                 changed_table_names = None):

        self.node = node
        self.table = node
        self.node1 = node1
        self.node2 = node2
        self.tables = tables or []
        self.path = path or []
        self.path_no_rel = path_no_rel or []
        self.name_changes = name_changes or []
        self.changed_table_names = changed_table_names or []
        self.relation = relation

        # make sure table path includes next table

        if not relation:
            return

        if node == node1:
            self.join = swap_relations(relation.type)
        else:
            self.join = relation.type

        self.name = self.node

        name_change = [name_change for name_change in name_changes if name_change]
        self.alt_name = ".".join(name_change + [self.node])

        self.changed_table_names = self.changed_table_names + [self.alt_name]

        self.table_path = zip(self.changed_table_names, self.path)

def get_next_relation(gr, path_dict, edge, first = False):

    node = edge.node
    tables = edge.tables
    current_path = edge.path
    current_path_no_rel = edge.path_no_rel
    last_edge = (edge.node1, edge.node2)
    name_changes = edge.name_changes
    changed_table_names = edge.changed_table_names
    last_relation = edge.relation

    if last_relation and last_relation.no_auto_path:
        return


    for edge in gr.out_edges(node, data = True):
        node1, node2, relation = edge

        relation = relation["relation"]

        rtables = relation.table.database.tables
        old_table = rtables[node1]
        new_table = rtables[node2]

        if relation == last_relation:
            continue
        if rtables[node1].lookup and not rtables[node2].lookup and not first:
            continue
        if len(tables) > 1 and rtables[node2].entity and rtables[tables[-1]].name == "_core" and rtables[tables[-2]].entity:
            continue
        if len(tables) > 1 and check_two_entities(tables, node2, rtables):
            continue

        split = None

        relation_name = relation.name

        all_relations = old_table.tables_with_relations[(node2, "here")]
        auto_path = [rel for rel in all_relations if not rel.no_auto_path]
        if len(auto_path) > 1:
            split = relation_name[5:]

        new_name_changes = name_changes + [split]

        new_path = current_path + [relation_name]
        new_path_no_rel = current_path_no_rel + [relation_name[5:]]

        if len(new_path) > JOINS_DEEP:
            continue


        new_tables = tables + [node2]
        edge = Edge(node2, node1, node2, new_tables, new_path, new_path_no_rel,
                    new_name_changes, relation, changed_table_names)

        path_dict[tuple(new_path_no_rel)] = edge
        get_next_relation(gr, path_dict, edge)


    for edge in gr.in_edges(node, data = True):
        node1, node2, relation = edge
        relation = relation["relation"]
        rtables = relation.table.database.tables
        old_table = rtables[node2]
        new_table = rtables[node1]

        if relation == last_relation:
            continue
        if rtables[node2].lookup and not rtables[node1].lookup and not first:
            continue
        if len(tables) > 1 and rtables[node1].entity and rtables[tables[-1]].name == "_core" and rtables[tables[-2]].entity:
            continue
        if len(tables) > 1 and check_two_entities(tables, node1, rtables):
            continue

        split = None

        all_relations = old_table.tables_with_relations[(node1, "other")]
        auto_path = [rel for rel in all_relations if not rel.no_auto_path]
        if len(auto_path) > 1:
            split = relation.name[5:]


        backref = relation.sa_options.get("backref", "_%s" % node1)
        if not backref:
            continue
        new_path = current_path + [backref.encode("ascii")]
        new_path_no_rel = current_path_no_rel + [backref.encode("ascii")]

        new_name_changes = name_changes + [split]

        if len(new_path) > JOINS_DEEP:
            continue
        new_tables = tables + [node1]
        edge = Edge(node1, node1, node2, new_tables, new_path,
                    new_path_no_rel, new_name_changes, relation, changed_table_names)

        path_dict[tuple(new_path_no_rel)] = edge
        get_next_relation(gr, path_dict, edge)

def get_collection_of_obj(database, obj, parent_name):

    table_name = obj._table.name

    table = database.tables[table_name]

    relation_path = table.local_tables[parent_name]

    parent_obj = reduce(getattr, relation_path, obj)

    parent_obj_table = parent_obj._table

    relation_back_path = parent_obj_table.one_to_many_tables[table.name]

    return reduce(getattr, relation_back_path, parent_obj)


def get_paths(gr, table):

    path_dict = {}

    edge = Edge(table, tables = [table])

    get_next_relation(gr, path_dict, edge, first = True)


    return path_dict

def get_local_tables(path_dict, one_to_many_tables, local_tables, edge):

    new_name = edge.alt_name
    if edge.relation.no_auto_path:
        return
    if edge.join in ("manytoone", "onetoone"):
        local_tables[new_name] = edge
    else:
        one_to_many_tables[new_name] = edge
        return

    for new_path, new_edge in path_dict.iteritems():
        if len(edge.path_no_rel)+1 <> len(new_path):
            continue
        if list(new_path)[:len(edge.path)] == list(edge.path_no_rel):
            get_local_tables(path_dict, one_to_many_tables, local_tables, new_edge)


def make_local_tables(path_dict):

    local_tables = {}
    one_to_many_tables = {}

    for path, edge in path_dict.iteritems():
        if len(path) == 1:
            get_local_tables(path_dict, one_to_many_tables, local_tables, edge)

    return [local_tables, one_to_many_tables]


def create_table_path_list(path_dict):

    table_paths_list = []

    for k, v in path_dict.iteritems():
        table_paths_list.append([k, v])

    return table_paths_list


def create_table_path(table_path_list, table):

    table_path = {}

    table_path[table] = "root"

    tables = set()
    duplicate_tables = set()

    for item in table_path_list:
        key, edge = item
        table_name = edge.node
        relation = edge.relation
        if relation.no_auto_path:
            continue
        if table_name in tables:
            duplicate_tables.add(table_name)
        tables.add(table_name)


    for item in table_path_list:
        key, edge = item
        table_name = edge.node
        relation = edge.relation
        if relation.no_auto_path:
            continue
        elif edge.name in duplicate_tables:
            table_path[edge.alt_name] = edge #[list(key), relation]
        else:
            table_path[edge.node] = edge #[list(key), relation]

    return table_path

def get_fields_from_obj(obj):

    return obj._table.columns.keys() + ["id"]

INTERNAL_FIELDS = ("_modified_by", "_modified_date", "id",
                   "_core_id", "_core_entity_id", "_version")

def convert_value(value):

    if isinstance(value, datetime.datetime):
        # use .isoformat not .strftime as this allows dates pre 1900
        value = '%sZ' % value.isoformat()
        if len(value) == 20:
            value = '%s.000Z' % value[:19]
    if isinstance(value, datetime.date):
        value = '%sT00:00:00.000Z' % value.isoformat()

    if isinstance(value, decimal.Decimal):
        value = str(value)
    return value

def get_row_data(obj, fields = None, keep_all = False,
                 internal = False, basic = False,
                 table = None, alias_name = None):

    row_data = {}

    obj_table = obj._table.name

    if not alias_name:
        alias_name = obj_table

    if not table:
        table = obj_table

    for field in get_fields_from_obj(obj):

        if fields:
            if not((field in fields) or (keep_all and field in INTERNAL_FIELDS)):
                continue
        else:
            if not keep_all and field in INTERNAL_FIELDS:
                continue

        if obj_table == table:
            field_name = field
        else:
            field_name = '%s.%s' % (alias_name, field)

        value = getattr(obj, field)

        if internal:
            row_data[field_name] = value
        else:
            row_data[field_name] = convert_value(value)

    if fields and obj_table == table:
        row_data["id"] = obj.id

    if keep_all and not fields:
        if obj_table == table:
            id_name = "id"
        else:
            id_name = "%s.id" % alias_name
        row_data[id_name] = obj.id

    return row_data

def create_data_dict(result, **kw):

    data = {}
    if hasattr(result, "_table"):
        data[result.id] = get_row_data(result, **kw)
        return data

    for row in result:
        data[row.id] = get_row_data(row, **kw)
    return data


def create_data_array(result, **kw):

    data = []
    if hasattr(result, "_table"):
        out = get_row_data(result, **kw)
        out['id'] = result.id
        data.append(out)
        return data

    for row in result:
        out = get_row_data(row, **kw)
        out['id'] = row.id
        data.append(out)
    return data

def split_table_fields(field_list, table_name):

    table_field_dict = {}

    for table_field in field_list:
        table_field_list = table_field.split(".")
        if len(table_field_list) == 2:
            out_table, out_field = table_field_list
            table_field_dict.setdefault(out_table,[]).append(out_field)
        else:
            table_field_dict.setdefault(table_name,[]).append(table_field)

    return table_field_dict


def get_all_local_data(obj, **kw):

    internal = kw.pop("internal", False)
    fields = kw.pop("fields", False)
    tables = kw.pop("tables", False)
    allow_system = kw.pop("allow_system", False)
    keep_all = kw.pop("keep_all", False)
    extra_obj = kw.pop("extra_obj", None)
    extra_fields = kw.pop("extra_fields", None)

    table = obj._table


    if fields:
        row = get_row_with_fields(obj, fields, internal = internal, keep_all = keep_all)
    elif tables:
        row = get_row_with_table(obj, tables, keep_all = keep_all, internal = internal)
    elif allow_system:
        all_local_tables = table.local_tables.keys() + [table.name]
        row = get_row_with_table(obj, all_local_tables, keep_all = keep_all, internal = internal)
    else:
        all_local_tables = table.local_tables.keys() + [table.name]
        local_tables = [table for table in all_local_tables if not table.startswith("_")]
        row = get_row_with_table(obj, local_tables, keep_all = keep_all, internal = internal)

    if extra_obj:
        for obj in extra_obj:
            table_name = obj._table
            data = get_row_data(obj, fields = fields, keep_all = keep_all, internal = internal, table = table.name)
            row.update(data)
    if extra_fields:
        row.update(extra_fields)

    return row

def get_row_with_table(obj, tables, keep_all = True, internal = False):

    table = obj._table

    row_data = {"__table": table.name}
    database = table.database
    local_tables = table.local_tables

    if obj._table.name in tables:
        data = get_row_data(obj, keep_all = keep_all, internal = internal, table = table.name)
        row_data.update(data)

    for aliased_table_name, edge in table.local_tables.iteritems():
        #table_name = edge.node
        if aliased_table_name not in tables:
            continue

        current_obj =  recurse_relationships(database, obj, edge)

        if not current_obj:
            continue

        data = get_row_data(current_obj, keep_all = keep_all, internal = internal,
                            table = table.name, alias_name = aliased_table_name)

        row_data.update(data)

    return row_data

def get_row_with_fields(obj, fields, keep_all = False, internal = False):

    table = obj._table

    table_field_dict = split_table_fields(fields, table.name)

    row_data = {"__table": table.name}
    database = table.database
    local_tables = table.local_tables

    if table.name in table_field_dict:
        fields = table_field_dict[table.name]

    if fields:
        data = get_row_data(obj, fields = fields, keep_all = keep_all, internal = internal, table = table.name)
        row_data.update(data)

    for aliased_table_name, edge in table.local_tables.iteritems():
        table_name = edge.node

        if table_name not in table_field_dict or table_name == table.name:
            continue

        if table_name in table_field_dict:
            fields = table_field_dict[table_name]

        if fields:
            current_obj = recurse_relationships(database, obj, edge)
            if not current_obj:
                continue
            data = get_row_data(current_obj, fields = fields, keep_all = keep_all, internal = internal, table = table.name)
            row_data.update(data)

    return row_data

def recurse_relationships(database, obj, edge):

    current_obj = obj
    for relation in edge.path:
        current_obj = getattr(current_obj, relation)
        if not current_obj:
            #current_obj = database.get_instance(table_name)
            break
    return current_obj



def load_local_data(database, data):

    session = database.Session()

    table = data["__table"]
    rtable = database.tables[table]

    record = {}

    for key, value in data.iteritems():
        if key.startswith("__"):
            continue
        fields = key.split(".")
        if len(fields) == 1:
            alias, field = table, fields[0]
        else:
            alias, field = fields
        if alias == table:
            path_key = "root"
        else:
            path_key = []
            for item in rtable.local_tables[alias].path_no_rel:
                path_key.extend([item,0])
            path_key = tuple(path_key)

        if isinstance(value, basestring):
            value = value.decode("utf8")

        record.setdefault(path_key, {})[field] = value
    try:
        data_loader.SingleRecord(database, table, all_rows = record).load()
        session.close()
    except fe.Invalid, e:
        error_dict = {}
        invalid_msg = ""
        for key, invalid in e.error_dict.iteritems():
            new_key = key[:-1:2]
            field_name = key[-1]
            if key[0] == table:
                new_table = table
            else:
                edge = rtable.paths[new_key]
                new_table = edge.name


            error_dict["%s.%s" % (new_table,
                                  field_name)] = invalid

            invalid_msg = invalid_msg + "\n" + "\n".join(["%s\n" % inv.msg for inv in invalid])

        if error_dict:
            raise fe.Invalid(invalid_msg, data, record, None, error_dict)
        session.close()


def get_table_from_instance(instance, database):

    return database.tables[instance.__class__.__name__]

## {{{ http://code.activestate.com/recipes/576669/ (r18)
## Raymond Hettingers proporsal to go in 2.7
from collections import MutableMapping

class OrderedDict(dict, MutableMapping):

    # Methods with direct access to underlying attributes

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at 1 argument, got %d', len(args))
        if not hasattr(self, '_keys'):
            self._keys = []
        self.update(*args, **kwds)

    def clear(self):
        del self._keys[:]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            self._keys.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __iter__(self):
        return iter(self._keys)

    def __reversed__(self):
        return reversed(self._keys)

    def popitem(self):
        if not self:
            raise KeyError
        key = self._keys.pop()
        value = dict.pop(self, key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        inst_dict.pop('_keys', None)
        return (self.__class__, (items,), inst_dict)

    # Methods with indirect access via the above methods

    setdefault = MutableMapping.setdefault
    update = MutableMapping.update
    pop = MutableMapping.pop
    keys = MutableMapping.keys
    values = MutableMapping.values
    items = MutableMapping.items

    def __repr__(self):
        pairs = ', '.join(map('%r: %r'.__mod__, self.items()))
        return '%s({%s})' % (self.__class__.__name__, pairs)

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d
## end of http://code.activestate.com/recipes/576669/ }}}



## From Evan Fosmark found on http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/

class FileLockException(Exception):
    pass

class FileLock(object):
    """ A file locking mechanism that has context-manager support so
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
    """

    def __init__(self, file_name, timeout=10, delay=.05):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.is_locked = False
        self.lockfile = file_name + ".lock"
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay


    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws
            an exception.
        """
        start_time = time.time()
        while True:
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
                break;
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if (time.time() - start_time) >= self.timeout:
                    raise FileLockException("Timeout occured.")
                time.sleep(self.delay)
        self.is_locked = True


    def release(self):
        """ Get rid of the lock by deleting the lockfile.
            When working in a `with` statement, this gets automatically
            called at the end.
        """
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False


    def __enter__(self):
        """ Activated when used in the with statement.
            Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self


    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()

    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()
###

class SchemaLock(FileLock):

    def __init__(self, database, timeout=10, delay=.05):

        self.database = database
        self.schema_path = database.get_file_path()
        self.uuid_path = database.get_file_path(True)

        self.is_locked = False
        self.lockfile = self.schema_path + ".lock"
        self.timeout = timeout
        self.delay = delay
        self.export_uuid = False

    def export(self, uuid = False):
        if uuid:
            self.database.code_repr_export(self.uuid_path)
            self.export_uuid = True
        else:
            self.database.code_repr_export(self.schema_path)

    def __enter__(self):
        if not self.is_locked:
            self.acquire()

        return self

    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()
        if not traceback and self.export_uuid:
            os.rename(self.uuid_path, self.uuid_path[:-3] + "-complete.py")
