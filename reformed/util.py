JOINS_DEEP = 3


def swap_relations(relation_type):
    if relation_type == "onetomany":
        return "manytoone"
    if relation_type == "manytoone":
        return "onetomany"
    return "onetoone"

def get_next_relation(gr, node, path_dict, current_path = [], last_edge = ()):

    for edge in gr.out_edges(node, data = True):
        node1, node2, relation = edge
        if (node1, node2) != last_edge:
            new_path = current_path + [relation.name] 
            if len(new_path) > JOINS_DEEP*2:
                continue
            path_dict[tuple(new_path)] = [node2, relation.type]
            get_next_relation(gr, node2, path_dict, new_path, (node1,node2))
        
    for edge in gr.in_edges(node, data = True):
        node1, node2, relation = edge
        if (node1, node2) != last_edge:
            new_path = current_path + ["_%s" % node1] 
            if len(new_path) > JOINS_DEEP*2:
                continue
            path_dict[tuple(new_path)] = [node1, swap_relations(relation.type)]
            get_next_relation(gr, node1, path_dict, new_path, (node1,node2))

def get_paths(gr, table):

    path_dict = {}

    get_next_relation(gr, table, path_dict)

    return path_dict


