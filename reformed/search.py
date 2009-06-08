import sqlalchemy as sa
from util import JOINS_DEEP
import custom_exceptions
from sqlalchemy.sql import not_, and_, or_

class Search(object):

    def __init__(self, database, table, session):

        table_paths = database.tables[table].paths

        self.database = database
        self.table = table
        self.session = session

        self.t = QueryTableHolder()

        self.table_paths_list = [] 
        
        for k,v in table_paths.iteritems():
            self.table_paths_list.append([k, v[0], v[1]])


        self.table_paths_list.sort(self.sort_order)

        self.table_path = {}
        self.aliased_name_path = {} 

        self.create_path_and_holder()
        print self.table_path

        self.local_tables = {}

        self.create_local_tables()

        self.search_base = self.session.query(self.database.get_class(self.table))

        self.queries = []

    def sort_order(self, a, b):
        ## put relationships with entities in last then by depth. 
        ## This is to ensure most usable table is not numbered

        if "_entity" in a[0]:
            asize = len(a[0]) - JOINS_DEEP*2  
        else:
            asize = len(a[0])

        if "_entity" in b[0]:
            bsize = len(b[0]) - JOINS_DEEP*2
        else:
            bsize = len(b[0])
        
        return bsize-asize
        

    def add_query(self, *args, **kw):

        exclude = kw.pop("exclude", False)
        query = args[0]

        if not hasattr(query, "add_conditions"):
            query = SingleQuery(self, *args)

        self.queries.append([query, exclude])

    def search(self, exclude_mode = None):

        first_query = self.queries[0][0]
        print first_query.inner_joins.union(first_query.outer_joins)

        if len(self.queries) == 1:
            ## if query contains a onetomany make the whole query a distinct
            for table in first_query.inner_joins.union(first_query.outer_joins):
                if table != self.table and table not in self.local_tables[self.table]:
                    return first_query.add_conditions(self.search_base).distinct()
            return first_query.add_conditions(self.search_base)

        query_base = self.session.query(self.database.get_class(self.table).id)

        sa_queries = []
        for n, item in enumerate(self.queries):
            query, exclude = item
            if n == 0 and exclude:
                raise custom_exceptions.SearchError("can not exclude first query")
            new_query = query.add_conditions(query_base)
            sa_queries.append([new_query, exclude])

        current_unions = [] 
        current_excepts = [] 

        for n, item in enumerate(sa_queries):
            query, exclude = item
            if n == 0:
                main_subquery = query
                continue
            
            if exclude:
                current_excepts.append(query)
            else:
                current_unions.append(query)
            if len(current_unions) > 0 and len(current_excepts) > 0:
                if exclude:
                    main_subquery = main_subquery.union(*current_unions)
                    current_unions = []
                else:
                    main_subquery = self.exclude(main_subquery, current_excepts, exclude_mode)
                    current_excepts = [] 
        if current_unions:
            main_subquery = main_subquery.union(*current_unions)
        if current_excepts:
            main_subquery = self.exclude(main_subquery, current_excepts, exclude_mode)


        main_subquery = main_subquery.subquery()

        ### if first query has a one to many distict the query
        for table in first_query.inner_joins.union(first_query.outer_joins):
            if table != self.table and table not in self.local_tables[self.table]:
                return self.search_base.join((main_subquery, main_subquery.c.id == self.database.get_class(self.table).id)).distinct()
        return self.search_base.join((main_subquery, main_subquery.c.id == self.database.get_class(self.table).id))

            
    def exclude(self, query, current_excepts, exclude_mode):

        if exclude_mode == "except":
            return query.except_(*current_excepts)

        subqueries = []

        for subquery in current_excepts:
            subqueries.append(subquery.subquery())

        for subquery in subqueries:
            query = query.outerjoin((subquery, subquery.c.id == self.database.get_class(self.table).id))

        for subquery in subqueries:
            query = query.filter(subquery.c.id == None)

        return query

        

    def create_path_and_holder(self):
        
        table_count = {}
        table_count[self.table] = 1
        self.table_path[self.table] = "root"
        setattr(self.t, self.table, self.database.tables[self.table].sa_class) 

        for item in self.table_paths_list:
            key, table_name, relation = item
            table_count.setdefault(table_name, 0) 
            table_count[table_name] = table_count[table_name] + 1

            if table_count[table_name] == 1:
                setattr(self.t, table_name, self.database.tables[table_name].sa_class)
                self.table_path[table_name] = [list(key), relation]
                self.aliased_name_path[table_name] = list(key)
            if table_count[table_name] != 1:
                new_name = "%s_%s" % (table_name, str(table_count[table_name]))
                aliased_table = sa.orm.aliased(self.database.tables[table_name].sa_class)
                setattr(self.t, new_name, aliased_table)
                self.table_path[new_name] = [list(key), relation]
                aliased_name = (aliased_table.id == 1).get_children()[0].table.name
                self.aliased_name_path[aliased_name] = list(key)

    def create_local_tables(self):

        for table, value in self.table_path.iteritems():
            if value == "root":
                self.local_tables[self.table] = [self.table]
                self.subsiquant_relation_finder(self.table, "root")
                continue

            key, relation = value
            self.local_tables[table] = [table]
            self.previous_relation_finder(table, key, relation)
            self.subsiquant_relation_finder(table, key)

    def previous_relation_finder(self, table, current_key, relation):

        if relation == "manytoone":
            return
        if len(current_key) == 1:
            self.local_tables[table].append(self.table)
        for new_table, value in self.table_path.iteritems():
            if value == "root":
                continue
            key, relation = value
            if key == current_key[:-1]:
                self.local_tables[table].append(new_table)
                self.previous_relation_finder(table, current_key[:-1], relation)

    def subsiquant_relation_finder(self, table, current_key):

        for new_table, value in self.table_path.iteritems():
            if value == "root":
                continue
            key, relation = value
            if key[:-1] == current_key or (len(key) == 1 and current_key == "root"):
                if relation == "onetomany":
                    continue
                self.local_tables[table].append(new_table)
                self.subsiquant_relation_finder(table, key)

class SingleQuery(object):

    def __init__(self, search, *args):

        self.search = search
        self.query = args[0]

        if not hasattr(self.query, "inner_joins"):
            self.query = Conjunction(*args)

        self.inner_joins = self.query.inner_joins
        self.outer_joins = self.query.outer_joins
        self.gather_covering_ors()
        self.where = self.process_query(self.query)
        root_class = self.search.database.tables[self.search.table].sa_class

        
    def add_conditions(self, sa_query):

        for join in self.outer_joins:
            if join <> self.search.table:
                sa_query = sa_query.outerjoin(self.search.aliased_name_path[join])

        for join in self.inner_joins:
            if join <> self.search.table:
                sa_query = sa_query.join(self.search.aliased_name_path[join])

        sa_query = sa_query.filter(self.where)

        return sa_query

    def gather_covering_ors(self):
        
        ors = [] 
             
        def recurse_query(conjunction, ors):

            if conjunction.type == "or":
                ors.append(conjunction)
            for statement in conjunction.processed_propersitions:
                if hasattr(statement, "processed_propersitions"):
                    recurse_query(statement, ors)

        recurse_query(self.query, ors)

        for conj in ors:
            if len(conj.tables_covered_by_this) > 1:
                for table in conj.tables_covered_by_this:
                    self.outer_joins.update([table])

    def process_query(self, conjunction):

        statement_list = []
        if conjunction.type == "or":
            conj = or_
        else:
            conj = and_

        for statement in conjunction.processed_propersitions:
            if hasattr(statement, "processed_propersitions"):
                sub_statement = self.process_query(statement)
                statement_list.append(sub_statement)
            else:
                statement_list.append(statement)
        
        return conj(*statement_list)
                    


            

class Conjunction(object):

    def __init__(self, *args, **kw):

        self.propersitions = args
        self.processed_propersitions = []
        self.printable_propersitions = []
        self.type = kw.pop("type", "and")
        self.notted = kw.pop("notted", False)
        covering_ors = kw.pop("ors", [])
        if self.type == "or":
            self.covering_ors = covering_ors + [self]
        else:
            self.covering_ors = covering_ors + []
        self.tables_covered_by_this = set()
        self.inner_joins = kw.pop("inner_joins", set())
        self.outer_joins = kw.pop("outer_joins", set())

        self.process_propersitions()

    def process_propersitions(self):

        for enum ,prop in enumerate(self.propersitions):
            if isinstance(prop, list):
                if enum != 0 and str(self.propersitions[enum - 1]) == "not":
                    notted = not self.notted
                    type = self.swap_or_and("and", notted)
                elif enum not in (0,1) and str((self.propersitions[enum - 1]) == "or")\
                                       and str(self.propersitions[enum -2]) == "not":
                    notted = not self.notted
                    type = self.swap_or_and("or", notted)
                elif enum != 0 and (str(self.propersitions[enum - 1]) == "or"):
                    notted = self.notted
                    type = self.swap_or_and("or", notted)
                else:
                    notted = self.notted
                    type = self.swap_or_and("and", notted)
                new_conjunction =Conjunction(*prop, 
                                             type = type,
                                             notted = notted,
                                             ors = self.covering_ors,
                                             inner_joins = self.inner_joins,
                                             outer_joins = self.outer_joins)
                self.processed_propersitions.append(new_conjunction)
                self.printable_propersitions.append(str(new_conjunction))

            elif hasattr(prop, "_table"):
                table = (prop.id == 1).get_children()[0].table.name
                if enum <> 0 and str(self.propersitions[enum -1]) == "not":
                    notted = not self.notted
                else:
                    notted = self.notted
                if notted:
                    self.processed_propersitions.append(prop.id == None)
                    self.printable_propersitions.append((notted,table,"eq"))
                    self.outer_joins.update([table])
                else:
                    self.processed_propersitions.append(prop.id != None)
                    self.printable_propersitions.append((notted,table,"ne"))
                    self.inner_joins.update([table])
                self.update_covering_ors(self.covering_ors, table)

            elif hasattr(prop, "operator"):
                operator_name = prop.operator.__name__
                column = prop.get_children()[0]
                table = column.table.name
                column_name = column.name
                if enum <> 0 and str(self.propersitions[enum -1]) == "not":
                    notted = not self.notted
                else:
                    notted = self.notted
                if notted and operator_name in ("eq", "gt", "ge", "in_op", "between_op", "like_op" , "ilike_op"):
                    self.processed_propersitions.append(or_(not_(prop), column == None))
                    self.outer_joins.update([table])
                if notted and operator_name in ("lt", "le", "ne"):
                    self.processed_propersitions.append(not_(prop))
                    self.inner_joins.update([table])
                if not notted and operator_name in ("eq", "gt", "ge", "in_op", "between_op", "like_op" , "ilike_op"):
                    self.processed_propersitions.append(prop)
                    self.inner_joins.update([table])
                if not notted and operator_name in ("lt", "le", "ne"):
                    self.processed_propersitions.append(or_(prop, column == None))
                    self.outer_joins.update([table])
                    
                self.update_covering_ors(self.covering_ors, table)
                self.printable_propersitions.append((notted, column_name, operator_name))
    
    def swap_or_and(self, prop, swap):
        if swap:
            if prop == "or":
                return "and"
            if prop == "and":
                return "or"
        return prop

    def __repr__(self):
        if self.notted == True:
            notted = " not"
        else:
            notted = ""
        cond = self.type + notted
        return "%s <%s>" % (cond, ", ".join([str(prop) for prop in self.printable_propersitions]))

    def __str__(self):
        return self.__repr__()

    def update_covering_ors(self, covering_ors, table):
        for conj in covering_ors:
            conj.tables_covered_by_this.update([table])

                
class QueryTableHolder(object):
    pass
