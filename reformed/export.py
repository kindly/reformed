import util
import json


def multi_row_export(obj_list, database, log = False, id = False, modified = False):

    list = []
    for obj in obj_list:
        list.append(SingleObject(obj, database, log = False, id = False, modified = False).data)

    return list

def json_dump_all_from_table(session, table, database, file, style=None):

    dumpfile = open(file, mode= "w+")

    all_rows = session.query(database.get_class(table)).all()
    export = multi_row_export(all_rows, database)
    if style == 'compact':
        dumpfile.write(json.dumps(export, separators=(',', ':')))
    elif style == 'clear':
        dumpfile.write(json.dumps(export, sort_keys=True, indent=4))
    else:
        dumpfile.write(json.dumps(export))
    dumpfile.close()

    

class SingleObject(object):

    def __init__(self, obj, database, log = False, id = False, modified = False):

        self.obj = obj
        self.database = database
        self.table = util.get_table_from_instance(obj, database)
        self.paths = self.table.paths
        self.log = log
        self.id = id
        self.modified = modified

        self.next_keys = {}
        self.get_next_keys()

        self.data = self.make_single_row(obj, "root", self.table)

    def get_next_keys(self):

        self.next_keys["root"] = []
        for key in self.paths.iterkeys():
            self.next_keys[key] = []
            for otherkey in self.paths.iterkeys():
                if len(otherkey) == len(key) + 1 and otherkey[:len(key)] == key:
                    self.next_keys[key].append(otherkey)
            if len(key) == 1:
                self.next_keys["root"].append(key)

    def make_single_row(self, obj, current_key, current_table):

        row = {}


        if self.id:
            row["id"] = str(getattr(obj, "id"))
            for column in current_table.columns.iterkeys():
                if not self.modified and column in ("modified_by", "modified_date"):
                    continue
                cell = getattr(obj, column) 
                if cell:
                    row[column] = str(cell)
        else:
            for column in current_table.defined_columns.iterkeys():
                if not self.modified and column in ("modified_by", "modified_date"):
                    continue
                cell = getattr(obj, column) 
                if cell:
                    row[column] = str(cell)

        for key in self.next_keys[current_key]:
            if (not self.log and key[-1].startswith("_log_")) or key[-1].startswith("_entity"):
                continue
            list = self.make_list(obj, key)
            if list:
                row[key[-1]] = list

        return row

    def make_list(self, obj, key):

        list = []
        table, join, one_ways = self.paths[key]
        if join in ("onetoone", "manytoone"):
            new_obj = getattr(obj, key[-1])
            if new_obj:
                single_row = self.make_single_row(new_obj, key, self.database.tables[table])
                if single_row:
                    list.append(single_row)
        else:
            for new_obj in getattr(obj, key[-1]):
                if new_obj:
                    single_row = self.make_single_row(new_obj, key, self.database.tables[table])
                    if single_row:
                        list.append(single_row)
        return list

            
