import custom_exceptions
import sqlalchemy
import logging
import re
import csv
import datetime
import time
import formencode as fe
import json
import datetime
import Queue
import sqlalchemy as sa
from multiprocessing import Pool
import multiprocessing

logger = logging.getLogger('reformed.main')
reformed_database = None
data_load_queues = {}

def get_key_data(key, database, table):
    """from a particular key get out what table the key relates to and the last 
    join to that table"""

    relations = key[::2]
    paths = database.tables[table].paths

    try:
        key_data = paths[relations]
    except KeyError:
        raise custom_exceptions.InvalidKey("key %s can not be used with %s table" , key, table)

    return key_data

def get_parent_key(key, all_rows):
    """get the key of the of the table that joins to the keys table"""
    
    if len(key) <= 2:
        return "root"
    try:
        prev_len = len(key)-2
        prev_key = key[0:prev_len]
        all_rows[key[0:prev_len]]
    except KeyError:
        raise custom_exceptions.InvalidKey("key %s does not have a parent key" , key)

    return prev_key

def check_correct_fields(row, database, table):

    for field in row.iterkeys():
        if not field.startswith("__") and\
               field not in database.tables[table].columns.iterkeys() and\
               field not in database.tables[table].relations.iterkeys() and\
               field <> "id":
            raise custom_exceptions.InvalidField("field %s not in table %s",
                                                 field, table)
def convert_unicode(value):
    if isinstance(value, basestring):
        return value.decode("utf8")
    return value

def string_key_parser(key_string):

    numbers = re.finditer("__[0-9]+__", key_string)

    key = []
    current_pos = 0
    for part in numbers:
        key.append(key_string[current_pos: part.start()])
        key.append(int(part.group(0)[2:-2]))
        current_pos = part.end() 
    key.append(key_string[current_pos:])
    return key

def get_keys_and_items_from_list(list):

    key_item_list = []
    for string_key in list:
        string_parsed = string_key_parser(string_key)
        key = tuple(string_parsed[:-1])
        item = string_parsed[-1]
        if key == ():
            key = "root"
        key_item_list.append([key, item])
    return key_item_list

def get_key_item_dict(key_item_list):

    key_item_dict = {}
    for key, item in key_item_list:
        if key == "root":
            key_item_dict.setdefault("root", {})[item] = None 
        else:
            key_item_dict.setdefault(tuple(key), {})[item] = None 
    return key_item_dict

def get_keys_from_list(key_item_list):

    all_rows = {}
    for key, item in key_item_list:
        if key != "root":
            all_rows[tuple(key)] = {}
        else:
            all_rows["root"] = {}

    return all_rows

def load_json_from_file(filename, database, table):

    with open(filename, mode = "rb+") as f:
        data = f.read()
        json_file = json.loads(data)
        for record in json_file:
            SingleRecord(database, table, record).load()

class ErrorLine(object):

    def __init__(self, line_number, line, error_dict):

        self.line_number =  line_number
        self.line =  line
        self.error_dict = error_dict

    def __repr__(self):

        return "line_number: %s, errors: %s" % (self.line_number, self.error_dict)

class ChunkStatus(object):

    def __init__(self, chunk, status, error_lines = None, error = None):

        self.chunk = chunk
        self.status = status
        self.error_lines =  error_lines or []
        self.error = error

        self.error_count = len(self.error_lines)
        self.length = chunk[1] - chunk[0]

    def __repr__(self):

        return "chunk: %s, status: %s, error: %s" % (self.chunk, self.status, self.error)

class FlatFile(object):

    def __init__(self, database, table, data, headers = None):

        self.data = data
        self.database = database
        self.table = table

        self.validation = True

        self.dialect = None
        self.total_lines = None

        self.parent_key = {}
        self.key_data = {}
        self.key_decendants = {}

        if not headers:
            self.headers = self.get_headers()
            self.has_header = True
        else:
            self.has_header = False
            self.headers = headers

        self.key_item_list = get_keys_and_items_from_list(self.headers)

        self.all_rows_template = get_keys_from_list(self.key_item_list)

        self.key_item_dict = get_key_item_dict(self.key_item_list)

        self.keys = self.all_rows_template.keys()

        self.key_data = self.make_key_data_dict()

        self.key_field_type_dict = self.key_field_dict()

        self.make_parent_key_dict()

        self.fields_correct = self.check_fields()

        self.get_all_decendants()
        
        self.keys.sort(lambda a, b : len(a) - len(b))

        self.status = []

    def key_field_dict(self):

        key_field_dict = {}

        for col_name, column in self.database.tables[self.table].columns.iteritems():
            key_field_dict[("root", ) + (col_name, )] = column.type

        for key, key_data in self.key_data.iteritems():
            table = key_data.node
            for col_name, column in self.database.tables[table].columns.iteritems():
                key_field_dict[key + (col_name, )] = column.type

        return key_field_dict
    

    def get_file(self):

        flat_file = open(self.data, mode = "rb")
        return flat_file

    def get_headers(self):

        flat_file = self.get_file()

        self.dialect = csv.Sniffer().sniff(flat_file.read(102400))

        flat_file.seek(0)

        first_line = csv.reader(flat_file, self.dialect).next()

        flat_file.close()

        return first_line

    def count_lines(self):

        if not self.total_lines:
            with open(self.data, mode = "rb") as flat_file:

                total_lines = 0

                if self.has_header:
                    flat_file.next()

                for line in flat_file:
                    total_lines += 1

                self.total_lines = total_lines

        return self.total_lines


    def set_dialect(self):

        if not self.dialect:
            with open(self.data, mode = "rb") as flat_file:
                self.dialect = csv.Sniffer().sniff(flat_file.read(10240))

    def make_chunks(self, chunk_size):

        total_lines = self.count_lines()

        chunks = []

        low_bound = 0
        up_bound = 0

        while True:
            up_bound = low_bound + chunk_size
            if up_bound >= total_lines:
                chunks.append([low_bound, total_lines])
                break
            else:
                chunks.append([low_bound, up_bound])
                low_bound = up_bound

        return chunks

    def load_chunk(self, chunk):

        session = self.database.Session()

        lower, upper = chunk

        error_lines = []

        with open(self.data, mode = "rb") as flat_file:

            csv_file = csv.reader(flat_file, self.dialect)

            if self.has_header:
                csv_file.next()

            for line_number, line in enumerate(csv_file):

                if line_number < lower:
                    continue
                if line_number >= upper:
                    break

                record = SingleRecord(self.database, self.table, line, self)

                record.get_all_obj(session)

                record.add_all_values_to_obj()

                try:
                    record.save_all_objs(session)
                except fe.Invalid, e:
                    error_lines.append(ErrorLine(line_number, line, e.error_dict))

        if error_lines:
            return ChunkStatus(chunk, "validation error", error_lines)
        try:
            session.commit()
            return ChunkStatus(chunk, "committed")
        except sa.orm.exc.ConcurrentModificationError, e:
            return ChunkStatus(chunk, "locking error", error = e)
        except Exception, e:
            return ChunkStatus(chunk, "unknown error", error = e)
        finally:
            session.close()


    def load(self, validation = True, load_multiprocess = False, batch = 50, messager = None):

        if not self.fields_correct:
            print "ERROR: fields do not match cannot load %s" % self.table
            return

        self.validation = validation

        self.messager = messager

        self.start_time = datetime.datetime.now()

        self.session = self.database.Session()
        
        total_lines = self.count_lines()

        chunks = self.make_chunks(batch)

        self.set_dialect()

        for chunk in chunks:
            if self.database.status == "terminated":
                break
            chunk_status = self.load_chunk(chunk)
            if chunk_status.error_lines:
                print chunk_status.error_lines
            if chunk_status.error:
                print chunk_status.error
            self.status.append(chunk_status)
            self.calculate_stats()

        return self.calculate_stats()


    def calculate_stats(self):

        completed = 0
        committed = 0
        validation_errors = 0
        other_errors = 0

        for chunk_status in self.status:
            completed += chunk_status.length
            if chunk_status.status == "validation error":
                validation_errors += chunk_status.error_count
            elif chunk_status.status == "committed":
                committed += chunk_status.length
            else:
                other_errors += chunk_status.length

        time, rate = self.get_rate(completed)

        message = "%s rows in %s seconds  %s rows/s with %s errors" % (completed,
                                   time, rate, other_errors + validation_errors)
        print message

        percent = completed*100/(self.total_lines or 1)

        if self.messager:
            self.messager.message(message, percent)

        return message

    

    def get_rate(self, completed):

        time = (datetime.datetime.now() - self.start_time).seconds
        try:
            rate = completed/time
        except ZeroDivisionError:
            rate = 'n/a'
        return time, rate

    def make_parent_key_dict(self):
        for key in self.keys:
            if key <> "root":
                self.parent_key[key] = get_parent_key(key, self.all_rows_template)
        return self.parent_key

    def make_key_data_dict(self):
        for key in self.keys:
            if key <> "root":
                self.key_data[key] = get_key_data(key, self.database, self.table)
        return self.key_data

    def check_fields(self):
        for key in self.keys:
            if key == "root":
                table = self.table
            else:
                table = self.key_data[key].node
            try:
                check_correct_fields(self.key_item_dict[key], self.database, table)
                return True
            except custom_exceptions.InvalidField:
                return False

    def get_all_decendants(self):

        for key in self.keys:
            decendants = []
            if key == "root":
                decendants = [other_key for other_key in self.keys if other_key != "root"]
            else:
                key_len = len(key)
                for other_key in self.keys:
                    if other_key[:key_len] == key and other_key <> key:
                        decendants.append(other_key)
            self.key_decendants[key] = decendants

    def create_all_rows(self, row):

        if len(row) != len(self.key_item_list):
            raise custom_exceptions.InvalidRow("length of data is not the same as defined length")
        all_rows = {}
        for key in self.all_rows_template.iterkeys():
            all_rows[key] = {}
        for index, key_item in enumerate(self.key_item_list):
            key, item = key_item
            if row[index]:
                all_rows[key][item] = convert_unicode(row[index])
        for key in self.keys:
            if key == "root":
                continue
            if not all_rows[key]:
                if not any([all_rows[other_key] for other_key in self.key_decendants[key]]):
                    all_rows.pop(key)
        return all_rows


class SingleRecord(object):

    def __init__(self, database, table, data = None, flat_file = None, all_rows = None):

        self.data = data
        self.database = database
        self.table = table
        self.all_rows = all_rows
        self.flat_file = flat_file

        if flat_file:
            self.all_rows = flat_file.create_all_rows(data)
            self.keys = self.all_rows.keys()
            self.keys.sort(lambda a, b : len(a) - len(b))
        else:
            if not self.all_rows:
                self.all_rows = {}
                self.process()
            self.keys = self.all_rows.keys()
            self.keys.sort(lambda a, b : len(a) - len(b))

        self.all_obj = {} 

    def load(self):

        self.session = self.database.Session()

        self.get_all_obj(self.session)

        self.add_all_values_to_obj()

        self.save_all_objs(self.session)

        self.session.commit()
        self.session.close()

    def make_obj(self, session):

        self.get_all_obj(session)
        self.add_all_values_to_obj()
        self.save_all_objs(session)

        return self.all_obj

    def get_key_info(self, key):

        if self.flat_file:
            edge = self.flat_file.key_data[key]
            ##FIXME this will fail if the import file specifies a child key that has no parent
            parent_key = self.flat_file.parent_key[key]
            relation_name = key[-2]
        else:
            edge = get_key_data(key, self.database, self.table)
            parent_key = get_parent_key(key, self.all_rows)
            relation_name = key[-2]

        return [edge.node, edge.join, parent_key, relation_name]

    def save_all_objs(self, session):

        invalid_msg = {}
        invalid_dict = {} 
        
        for key, obj in self.all_obj.iteritems():
            obj._from_load = True
            try:
                if self.flat_file and not self.flat_file.validation:
                    session.add_no_validate(obj)
                else:
                    session.add(obj)
            except fe.Invalid, e:
                invalid_msg[key] = e.msg.replace("\n", ", ")

                for col_name, error_list in e.error_dict.iteritems():
                    errors = []
                    if not error_list.error_list:
                        errors.append(e)
                    for error in error_list.error_list or []:
                        errors.append(error)

                    if key == "root":
                        key = (self.table, )

                    new_key = key + (col_name,)

                    invalid_dict[new_key] = errors

        if invalid_msg:
            if not self.flat_file:
                session.expunge_all()
            raise fe.Invalid("invalid object(s) are %s" % invalid_msg,
                             self.data, self, None, invalid_dict) 

    def add_values_to_obj(self, key):

        for name, value in self.all_rows[key].iteritems():
            if not name.startswith("__"):
                setattr(self.all_obj[key], name, value)
    
    def add_all_values_to_obj(self):

        self.add_values_to_obj("root")
        for key in self.keys:
            if key <> "root":
                self.add_values_to_obj(key)

    def get_all_obj(self, session):

        self.get_root_obj(session)
        for key in self.keys:
            if key <> "root":
                self.get_obj(key)

    def get_root_obj(self, session):

        row = self.all_rows["root"]

        if not self.flat_file:
            check_correct_fields(row, self.database, self.table)

        ##TODO cache pk_list for flat files
        pk_list = self.database.tables[self.table].primary_key_columns.keys()

        if "id" in row.keys():
            obj = session.query(self.database.get_class(self.table)).filter_by( id = row["id"]).first()
            if not obj:
                obj = self.database.get_instance(self.table)
        ##TODO incorrect need to check even if just one key is specified and error otherwise
        elif set(pk_list).intersection(set(row.keys())) == set(pk_list) and pk_list:
            try:
                pk_values = {}
                pk_list = self.database.tables[self.table].primary_key_columns.keys()
                for item in pk_list:
                    pk_values[item] = row[item]
                obj = session.query(self.database.get_class(self.table)).filter_by(**pk_values).one()
            except sqlalchemy.orm.exc.NoResultFound:
                obj = self.database.get_instance(self.table)
        else:
            obj = self.database.get_instance(self.table)

        self.all_obj["root"] = obj

        return obj
        

    def get_obj(self, key):

        table, join, parent_key, relation_name  = self.get_key_info(key)

        row = self.all_rows[key]

        if not self.flat_file:
            check_correct_fields(row, self.database, table)

        if "id" in row.keys():
            obj = self.get_obj_with_id(key, row)
            self.all_obj[key] = obj
            return obj

        ##TODO cache pk_list for flat files
        pk_list = self.database.tables[table].primary_key_columns.keys()
        ##TODO incorrect need to check even if just one key is specified and error otherwise
        if set(pk_list).intersection(set(row.keys())) == set(pk_list) and pk_list:
            obj = self.get_obj_with_pk(key, row)
            self.all_obj[key] = obj
            return obj

        ##TODO add a possibility to get objects by the order in their parents list
        return self.get_new_obj(key, row)

    def get_new_obj(self, key, row):

        table, join, parent_key, relation_name  = self.get_key_info(key)

        parents_obj_relation = getattr(self.all_obj[parent_key], relation_name)
        if join in ("onetoone", "manytoone"):
            if parents_obj_relation is not None:
                self.all_obj[key] = parents_obj_relation
                return parents_obj_relation
            obj = self.database.get_instance(table)
            setattr(self.all_obj[parent_key], relation_name, obj)
            self.all_obj[key] = obj
            return obj
        
        obj = self.database.get_instance(table)
        parents_obj_relation.append(obj)
        self.all_obj[key] = obj
        return obj

    def get_obj_with_pk(self, key, row):

        row_number = key[-1]
        table, join, parent_key, relation_name  = self.get_key_info(key)

        pk_values = {}
        pk_list = self.database.tables[table].primary_key_columns.keys()
        for item in pk_list:
            pk_values[item] = row[item]

        parents_obj_relation = getattr(self.all_obj[parent_key], relation_name)


        if join in ("onetoone", "manytoone"):
            if not parents_obj_relation:
                try:
                    obj = self.session.query(self.database.get_class(table)).filter_by(**pk_values).one()
                    setattr(self.all_obj[parent_key], relation_name, obj)
                    return obj
                except sqlalchemy.orm.exc.NoResultFound:
                    return self.get_new_obj(key, row)
            pk_current_values = {}
            for item in pk_list:
                pk_current_values[item] = getattr(parents_obj_relation, item)
            if pk_current_values != pk_values:
                raise custom_exceptions.InvalidData("""primary key value(s) %s in table %s
                                        either do(es) not exist or 
                                        is not associted with join"""
                                        % (pk_values, table))
            return parents_obj_relation

        if join in ("onetomany"):
            for obj in parents_obj_relation:
                pk_current_values = {}
                for item in pk_list:
                    pk_current_values[item] = getattr(obj, item)
                if pk_current_values == pk_values:
                    return obj
            raise custom_exceptions.InvalidData("primary key value(s) %s in table %s"
                                    "either do(es) not exist or" 
                                    "is not associted with join"
                                    % (pk_values, table))

    def get_obj_with_id(self, key, row):

        row_number = key[-1]
        table, join, parent_key, relation_name  = self.get_key_info(key)

        id = row["id"]

        parents_obj_relation = getattr(self.all_obj[parent_key], relation_name)
        if join in ("onetoone", "manytoone"):
            if not parents_obj_relation:
                try:
                    obj = self.session.query(self.database.get_class(table)).filter_by(id = id).one()
                    setattr(self.all_obj[parent_key], relation_name, obj)
                    return obj
                except sqlalchemy.orm.exc.NoResultFound:
                    raise custom_exceptions.InvalidData("id %s is not in "
                                                        "table %s"
                                                        % (id, table))
            if parents_obj_relation.id <> id:
                raise custom_exceptions.InvalidData("""id %s in table %s
                                        either does not exist or 
                                        is not associted with join"""
                                        % (id, table))
            return parents_obj_relation
        if join in ("onetomany"):
            # may be better doing a query here instead of iterating over object lists"

            for obj in parents_obj_relation:
                if obj.id == id:
                    return obj
            raise custom_exceptions.InvalidData("""id %s in table %s
                                        either does not exist or 
                                        is not associted with join"""
                                        % (id, table))

    def process(self):

        for n, v in self.data.iteritems():
            if not isinstance(v, dict) and not isinstance(v, list):
                self.all_rows.setdefault("root", {})[n] = convert_unicode(v)
            if isinstance(v, list):
                self.process_list([n], v)
            if isinstance(v, dict):
                self.process_dict([n], v)

    def process_list(self, names, list):
        
        for index, value in enumerate(list):
            if isinstance(value, dict):
                self.process_dict(names + [index], value, from_list = True)
    
    def process_dict(self, names, sub_dict, from_list = False):

        for n, v in sub_dict.iteritems():
            if not isinstance(v, dict) and not isinstance(v, list):
                if from_list:
                    self.all_rows.setdefault(tuple(names), {})[n] = convert_unicode(v)
                else:
                    self.all_rows.setdefault(tuple(names + [0]), {})[n] = convert_unicode(v)
            if isinstance(v, list):
                if from_list:
                    self.process_list(names + [n], v)
                else:
                    self.process_list(names + [0, n], v)
            if isinstance(v, dict):
                if from_list:
                    self.process_dict(names + [n], v)
                else:
                    self.process_dict(names + [0, n], v)
            
