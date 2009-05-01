import networkx as nx
import custom_exceptions
import sqlalchemy
import logging

logger = logging.getLogger('reformed.main')

def get_key_data(key, database, table):

    relations = key[::2]
    paths = database.tables[table].paths

    try:
        key_data = paths[relations]
    except KeyError:
        raise custom_exceptions.InvalidKey("key %s can not be used with %s table" , key, table)

    return key_data

def get_parent_key(key, all_rows):

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
                                                 
class SingleRecord(object):

    def __init__(self, database, table, data):

        self.data = data
        self.database = database
        self.table = table

        self.all_rows = {}
        self.all_obj = {} 

        self.process()

        self.keys = self.all_rows.keys()

        self.keys.sort(lambda a, b : len(a) - len(b))


    def load(self):

        self.session = self.database.Session()

    def get_all_obj(self):

        self.get_root_obj()
        for key in self.keys:
            if key <> "root":
                self.get_obj(key)

    def get_root_obj(self):

        self.session = self.database.Session()


        row = self.all_rows["root"]

        check_correct_fields(row, self.database, self.table)

        pk_list = self.database.tables[self.table].primary_key_columns.keys()

        if "id" in row.keys():
            obj = self.session.query(self.database.get_class(self.table)).filter_by( id = row["id"]).one()
        ##TODO incorrect need to check even if just one key is specified and error otherwise
        elif set(pk_list).intersection(set(row.keys())) == set(pk_list) and pk_list:
            try:
                pk_values = {}
                pk_list = self.database.tables[self.table].primary_key_columns.keys()
                for item in pk_list:
                    pk_values[item] = row[item]
                print pk_values
                obj = self.session.query(self.database.get_class(self.table)).filter_by(**pk_values).one()
            except sqlalchemy.orm.exc.NoResultFound:
                obj = self.database.get_instance(self.table)
        else:
            obj = self.database.get_instance(self.table)

        self.all_obj["root"] = obj

        return obj
        

    def get_obj(self, key):

        table, join = get_key_data(key, self.database, self.table)
        parent_key = get_parent_key(key, self.all_rows)
        relation_name = key[-2]

        row = self.all_rows[key]

        check_correct_fields(row, self.database, table)

        if "id" in row.keys():
            obj = self.get_obj_with_id(key, row)
            self.all_obj[key] = obj
            return obj

        pk_list = self.database.tables[table].primary_key_columns.keys()
        ##TODO incorrect need to check even if just one key is specified and error otherwise
        if set(pk_list).intersection(set(row.keys())) == set(pk_list) and pk_list:
            obj = self.get_obj_with_pk(key, row)
            self.all_obj[key] = obj
            return obj

        ##TODO add a possibility to get objects by the order in their parents list

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
        table, join = get_key_data(key, self.database, self.table)
        row_number = key[-1]
        relation_name = key[-2]
        parent_key = get_parent_key(key, self.all_rows)


        pk_values = {}
        pk_list = self.database.tables[table].primary_key_columns.keys()
        for item in pk_list:
            pk_values[item] = row[item]

        parents_obj_relation = getattr(self.all_obj[parent_key], relation_name)

        if join in ("onetoone", "manytoone"):
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
            raise custom_exceptions.InvalidData("""primary key value(s) %s in table %s
                                    either do(es) not exist or 
                                    is not associted with join"""
                                    % (pk_values, table))

    def get_obj_with_id(self, key, row):

        table, join = get_key_data(key, self.database, self.table)
        row_number = key[-1]
        relation_name = key[-2]
        parent_key = get_parent_key(key, self.all_rows)

        id = row["id"]

        parents_obj_relation = getattr(self.all_obj[parent_key], relation_name)
        if join in ("onetoone", "manytoone"):
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
                self.all_rows.setdefault("root", {})[n] = v
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
                    self.all_rows.setdefault(tuple(names), {})[n] = v
                else:
                    self.all_rows.setdefault(tuple(names + [0]), {})[n] = v
            if isinstance(v, list):
                if from_list:
                    self.process_list(names + [n], v)
                else:
                    self.process_list(names + [0,n], v)
            if isinstance(v, dict):
                if from_list:
                    self.process_dict(names + [n], v)
                else:
                    self.process_dict(names + [0,n], v)
            
