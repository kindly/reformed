import networkx as nx
import custom_exceptions

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

        

    def set_root_obj(self):

        row = self.all_rows["root"]

        check_correct_fields(row, self.database, self.table)

        if id in row.keys():
            obj = self.session.query(self.database.get_class(self.table)).get(id)
        else:
            obj = self.database.get_class(self.table)

        self.all_obj["root"] = obj

    def get_obj(self, key):

        table, join = get_key_data(key, self.database, self.table)
        row_number = key[-1]
        relation_name = key[-1]
        parent_key = get_parent_key(key, self.all_rows)
        
        row = self.all_rows[key]

        check_correct_fields(row, self.database, table)

        if "id" in row.keys():
            id = row[id]
            obj = self.session.query(self.database.get_class(table)).get(id)
            if key == "root":
                return obj
            if join in ("onetoone", "manytoone"):
                if getattr(all_obj[parent_key], relation_name).id <> id:
                    raise custom_exceptions.InvalidData("no")


            
                        



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
            
