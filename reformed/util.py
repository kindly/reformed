JOINS_DEEP = 3


def swap_relations(relation_type):
    if relation_type == "onetomany":
        return "manytoone"
    if relation_type == "manytoone":
        return "onetomany"
    return "onetoone"

def get_next_relation(gr, node, path_dict, tables, current_path = [], last_edge = (), one_ways = []):
    
    for edge in gr.out_edges(node, data = True):
        node1, node2, relation = edge
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
            get_next_relation(gr, node2, path_dict, new_tables, new_path, (node1,node2), new_one_ways)
        
    for edge in gr.in_edges(node, data = True):
        node1, node2, relation = edge
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
            get_next_relation(gr, node1, path_dict, new_tables, new_path, (node1,node2), one_ways)

def get_paths(gr, table):

    path_dict = {}

    get_next_relation(gr, table, path_dict, [table])

    return path_dict

def table_path_sort_order(a,b):
    return len(a[0]) - len(b[0]) 

def create_table_path_list(path_dict):

    table_paths_list = [] 

    for k,v in path_dict.iteritems():
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

def get_row_data(obj):
    
    row_data = {}
    table = obj._table.name
    for field in get_fields_from_obj(obj):
        if field in ("modified_by", "modified_date", "id", "_core_entity_id"):
            continue
        row_data["%s.%s" % (table, field)] = getattr(obj, field)
    return row_data

def create_data_dict(result):

    data = {}
    if hasattr(result, "_table"):
        data[result.id] = get_row_data(result) 
        return data

    for row in result:
        data[row.id] = get_row_data(row) 
    return data




    
def get_table_from_instance(instance, database):

    return database.tables[instance.__class__.__name__]

