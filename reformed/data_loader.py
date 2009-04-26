import networkx as nx
import custom_exceptions

class SingleRecord(object):

    def __init__(self, database, table, data):

        self.data = data
        self.database = database
        self.table = table

        self.all_obj = {}

        self.process()

        self.keys = self.all_obj.keys()

        self.keys.sort(lambda a, b : len(a) - len(b))

    def load(self):

        session = database.Session()

        for key in self.keys:
            continue


    def process(self):

        for n, v in self.data.iteritems():
            if not isinstance(v, dict) and not isinstance(v, list):
                self.all_obj.setdefault("root", {})[n] = v
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
                    self.all_obj.setdefault(tuple(names), {})[n] = v
                else:
                    self.all_obj.setdefault(tuple(names + [0]), {})[n] = v
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
            

def get_key_data(key, database, table):

    relations = key[::2]
    paths = database.tables[table].paths

    try:
        key_data = paths[relations]
    except KeyError:
        raise custom_exceptions.InvalidKey("key %s can not be used with %s table" , key, table)

    return key_data

def validate_key_against_all_obj(key, all_obj):

    if len(key) == 2:
        return
    try:
        prev_len = len(key)-2
        all_obj[key[0:prev_len]]
    except KeyError:
        raise custom_exceptions.InvalidKey("key %s does not have a parent key" , key)

def check_correct_fields(obj, database, table):

    for field in obj.iterkeys():
        if not field.startswith("__") and\
               field not in database.tables[table].columns.iterkeys() and\
               field <> "id":
            raise custom_exceptions.InvalidField("field %s not in table %s",
                                                 field, table)
                                                 


        














    
