JOINS_DEEP = 3
import data_loader
import formencode as fe


def swap_relations(relation_type):
    if relation_type == "onetomany":
        return "manytoone"
    if relation_type == "manytoone":
        return "onetomany"
    return "onetoone"

def get_next_relation(gr, node, path_dict, tables, current_path = [], last_edge = (), one_ways = []):
    
    for edge in gr.out_edges(node, data = True):
        node1, node2, relation = edge
        relation = relation["relation"]
        rtables = relation.table.database.tables
        if len(tables) > 1 and rtables[node2].entity and rtables[tables[-1]].name == "_core_entity" and rtables[tables[-2]].entity:
            continue
        if (node1, node2) != last_edge:
            new_path = current_path + [relation.name] 
            if len(new_path) > JOINS_DEEP*2:
                continue
            if relation.one_way:
                new_one_ways = one_ways + [node1]
            else:
                new_one_ways = one_ways
            path_dict[tuple(new_path)] = [node2, relation.type, new_one_ways]
            new_tables = tables + [node2]
            get_next_relation(gr, node2, path_dict, new_tables, new_path, (node1, node2), new_one_ways)
        
    for edge in gr.in_edges(node, data = True):
        node1, node2, relation = edge
        relation = relation["relation"]
        rtables = relation.table.database.tables
        if len(tables) > 1 and rtables[node1].entity and rtables[tables[-1]].name == "_core_entity" and rtables[tables[-2]].entity:
            continue
        if (node1, node2) != last_edge and not relation.one_way:
            backref = relation.sa_options.get("backref", "_%s" % node1)
            new_path = current_path + [backref] 
            if len(new_path) > JOINS_DEEP*2:
                continue
            path_dict[tuple(new_path)] = [node1, swap_relations(relation.type), one_ways]
            new_tables = tables + [node1]
            get_next_relation(gr, node1, path_dict, new_tables, new_path, (node1, node2), one_ways)

def get_paths(gr, table):

    path_dict = {}

    get_next_relation(gr, table, path_dict, [table])

    return path_dict

def get_local_tables(path_dict, one_to_many_tables, local_tables, current_pos):

    table, relation, one_ways = path_dict[current_pos]  
    new_name = "_".join(one_ways + [table])
    if relation in ("manytoone", "onetoone"):
        local_tables[new_name] = current_pos
    else:
        one_to_many_tables[new_name] = current_pos
        return

    for new_path, info in path_dict.iteritems():
        if len(current_pos)+1 == len(new_path) and list(new_path)[:len(current_pos)] == list(current_pos):
            get_local_tables(path_dict, one_to_many_tables, local_tables, new_path)


def make_local_tables(path_dict):

    local_tables = {}
    one_to_many_tables = {}
    
    for path, info in path_dict.iteritems():
        if len(path) == 1:
            get_local_tables(path_dict, one_to_many_tables, local_tables, path)

    return [local_tables, one_to_many_tables]


def table_path_sort_order(a, b):
    return len(a[0]) - len(b[0]) 

def create_table_path_list(path_dict):

    table_paths_list = [] 

    for k, v in path_dict.iteritems():
        table_paths_list.append([k, v[0], v[1], v[2]])

    table_paths_list.sort(table_path_sort_order)

    return table_paths_list
    

def create_table_path(table_path_list, table):

    table_path = {}

    table_path[table] = "root"

    for item in table_path_list:
        key, table_name, relation, one_ways = item
        new_name = "_".join(one_ways + [table_name])
        table_path[new_name] = [list(key), relation]

    return table_path

def get_fields_from_obj(obj):

    return obj._table.columns.keys()

def get_row_data(obj, keep_all = False):
    
    row_data = {}
    table = obj._table.name
    for field in get_fields_from_obj(obj):
        if field in ("modified_by", "modified_date", "id", "_core_entity_id") and not keep_all:
            continue
        row_data["%s.%s" % (table, field)] = getattr(obj, field)
    if keep_all:
        row_data["%s.id" % table] = obj.id
    return row_data

def create_data_dict(result):

    data = {}
    if hasattr(result, "_table"):
        data[result.id] = get_row_data(result) 
        return data

    for row in result:
        data[row.id] = get_row_data(row) 
    return data

def get_all_local_data(obj, allow_system = False, keep_all = False):

    row_data = {}
    table = obj._table
    database = table.database
    local_tables = table.local_tables
    row_data.update(get_row_data(obj, keep_all))

    for aliased_table_name, path in table.local_tables.iteritems():
        table_name = table.paths[path][0]
        if not allow_system:
            if table_name.startswith("_"):
                continue
        current_obj = obj
        for relation in path:
            current_obj = getattr(current_obj, relation)
            if not current_obj:
                current_obj = database.get_instance(table_name)
                break
        row_data.update(get_row_data(current_obj, keep_all))

    return row_data

def load_local_data(database, data):
    
    session = database.Session()

    table = data["__table"]
    rtable = database.tables[table]

    record = {}

    for key, value in data.iteritems():
        if key.startswith("__"):
            continue
        alias, field = key.split(".")
        if alias == table:
            path_key = "root"
        else:
            path_key = []
            for item in rtable.local_tables[alias]:
                path_key.extend([item,0])
            path_key = tuple(path_key)

        if isinstance(value, basestring):
            value = value.decode("utf8")

        record.setdefault(path_key, {})[field] = value
    try:
        data_loader.SingleRecord(database, table, all_rows = record).load() 
    except fe.Invalid, e:
        error_dict = {}
        invalid_msg = ""
        for key, invalid in e.error_dict.iteritems():
            new_key = key[::2]
            for field_name, sub_invalid in invalid.error_dict.iteritems():
                if key == "root":
                    new_table, one_ways = table, []
                else:
                    new_table, relation, one_ways = rtable.paths[new_key]
                error_dict["%s.%s" % ("_".join(one_ways + [new_table]),
                                        field_name)] = sub_invalid
            invalid_msg = invalid_msg + "\n" + invalid.msg  

        if error_dict:
            raise fe.Invalid(invalid_msg, data, record, None, error_dict) 
        

def get_table_from_instance(instance, database):

    return database.tables[instance.__class__.__name__]

