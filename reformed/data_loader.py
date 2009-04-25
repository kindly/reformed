import networkx as nx

class SingleRecord(object):

    def __init__(self, database, table, data):

        self.data = data
        self.database = database
        self.table = table
        
        self.all_fields = {}

        self.all_obj = {}

        self.key_info = {}

        self.process()

    def process(self):

        for n, v in self.data.iteritems():
            if not isinstance(v, dict) and not isinstance(v, list):
                self.all_fields[(n, )] = v
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
                    self.all_fields[tuple(names + [n])] = v
                    self.all_obj.setdefault(tuple(names), {})[n] = v
                else:
                    self.all_fields[tuple(names + [0,n])] = v
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
            

def get_all_paths(database, table):

    graph = database.make_graph()

    all_paths = []

    for edge in graph.edges(table, Data = True):
        node1, node2, relation = edge
        if node1 == table:
            if relation.type == "onetomany":
                all_paths.append([[relation.name, "many"], node2])
            if relation.type == "onetoone":
                all_paths.append([[relation.name, "one"], node2])
            if relation.type == "manytoone":
                all_paths.append([[relation.name, "one"], node2])
        if node2 == table:
            if relation.type == "onetomany":
                all_paths.append([["_%s" % node1, "one"], node1])
            if relation.type == "onetoone":
                all_paths.append([["_%s" % node1, "one"], node1])
            if relation.type == "manytoone":
                all_paths.append([["_%s" % node1, "many"], node1])
            
            

    



class KeyInfo(object):

    def __init__(self, key, database, table):

        self.key = key
        self.database = record.database
        self.table = record.table

        #FIXME make sure graph only drawn once
        self.graph = database.make_graph()

        self.edges = []

        self.get_edges()

        self.table = self.edges[-1].table
        self.parent_key = self.get_parent_key()

    def get_edges(self):

        for index, item in enumerate(self.key):
            if index % 2 == 1:
                continue
            if index == 0:
                for edge in self.graph.edges(self.table.name, Data = True):
                    node1, node2, relation = edge
                    if item == relation.name:
                        self.edges.append(KeyEdge(edge, self.table.name))
                        continue
                raise BadKeyError("relation %s not found from table %s" %
                                                            (item, self.key))
            else:
                for edge in self.graph.edges(self.edges[-1].table, Data = True):
                    node1, node2, relation = edge
                    if item == relation.name:
                        self.edges.append(KeyEdge(edge, self.table.name))
                        continue
                raise BadKeyError("relation %s not found from table %s" %
                                                            (item, self.key))

class KeyEdge(object):

    def __init__(self, edge, table_old):

        self.edge = edge
        self.table_old = table_old
        self.node1, self.node2, self.relation = edge
        self.table = self.other_node()
        
    def other_node(self):
        if self.table_old == node1:
            return node2
        else:
            return node1





