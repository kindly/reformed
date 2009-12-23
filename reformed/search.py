from util import create_table_path_list, create_table_path
import custom_exceptions
import pyparsing 
from decimal import Decimal
import util
import datetime
from custom_exceptions import InvalidArgument
from datetime import timedelta
import sqlalchemy as sa
from sqlalchemy.orm import eagerload_all
from sqlalchemy.sql import not_, and_, or_

class Search(object):

    def __init__(self, database, table, session, *args, **kw):

        table_paths = database.tables[table].paths

        self.database = database
        self.table = table
        self.session = session
        self.rtable = database.tables[table]

        self.tables = kw.get("tables", [table])
        self.fields = kw.get("fields", None)

        self.base_tables = kw.get("base_tables", None)

        if self.fields:
            self.tables = util.split_table_fields(self.fields, table).keys()

        self.eager_tables = self.get_eager_tables(self.tables)

        self.table_paths_list = create_table_path_list(table_paths) 
        self.table_path = create_table_path(self.table_paths_list, self.table)

        self.aliased_name_path = {} 
        self.create_aliased_path()

        if self.base_tables:
            base_tables = [self.database.get_class(self.table)]
            base_tables.extend([self.database.get_class(table) for table in self.base_tables]) 
            self.search_base = self.session.query(*base_tables)
        else:
            self.search_base = self.session.query(self.database.get_class(self.table))

        if self.eager_tables:
            for eager_join in self.eager_tables:
                self.search_base = self.search_base.options(sa.orm.eagerload_all(eager_join))

        self.queries = []

        if args:
            if args[0]:
                self.add_query(*args, **kw)

    def get_eager_tables(self, table_list):

        local_tables = []

        for table in table_list:
            if table in self.rtable.local_tables:
                join_list = self.rtable.local_tables[table]
                local_tables.append(".".join(join_list))

        return local_tables


    def add_query(self, *args, **kw):

        exclude = kw.pop("exclude", False)

        named_args = kw.get("params", {})
        pos_args = kw.get("values", [])

        query = args[0]

        if not hasattr(query, "add_conditions"):
            if named_args or pos_args:
                query = QueryFromStringParam(self, *args, named_args = named_args,
                                                          pos_args = pos_args)
            else:
                query = QueryFromString(self, *args)

        self.queries.append([query, exclude])

    def search(self, exclude_mode = None):

        if len(self.queries) == 0:
            return self.search_base

        first_query = self.queries[0][0]

        if len(self.queries) == 1:
            ## if query contains a onetomany make the whole query a distinct
            for table in first_query.inner_joins.union(first_query.outer_joins):
                if table != self.table and table not in self.rtable.local_tables:
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
            if table != self.table and table not in self.rtable.local_tables:
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

    def create_aliased_path(self):
        
        for item in self.table_paths_list:
            key, table_name, relation, one_ways = item
            new_name = "_".join(one_ways + [table_name])
            self.aliased_name_path[new_name] = list(key)

class QueryFromString(object):

    def __init__(self, search, *args, **kw):

        self.search = search
        self.query = args[0]

        parser = self.parser()

        self.ast = parser.parseString(self.query)

        self.covering_ors = set()

        self.inner_joins = set()
        self.outer_joins = set()

        self.gather_joins(self.ast, False)

        self.gather_covering_ors(self.ast, False, False)

        if kw.get("test", False) == True:
            return

        self.where = self.convert_where(self.ast[0])


    def add_conditions(self, sa_query):

        for join in self.outer_joins.union(self.covering_ors):
            if join <> self.search.table:
                sa_query = sa_query.outerjoin(self.search.aliased_name_path[join])

        for join in self.inner_joins:
            if join <> self.search.table:
                sa_query = sa_query.join(self.search.aliased_name_path[join])

        sa_query = sa_query.filter(self.where)

        return sa_query

    def gather_covering_ors(self, node, notted, ored):

        for item in node:
            if item == "not":
                notted = not notted
            if item == "or" and not notted:
                ored = True
            if item == "and" and notted:
                ored = True

        for item in node:
            if isinstance(item, pyparsing.ParseResults) and item.table and ored:
                self.covering_ors.update([item.table])
                
            if isinstance(item, pyparsing.ParseResults):
                self.gather_covering_ors(item, notted, ored)

    def gather_joins(self, node, notted):

        for item in node:
            if item == "not":
                notted = not notted

        for item in node:
            if isinstance(item, pyparsing.ParseResults) and item.table:
                if item.operator in ("<", "<=") and not notted or\
                   item.operator not in ("<", "<=") and notted:
                    self.outer_joins.update([item.table])
                else:
                    self.inner_joins.update([item.table])

            if isinstance(item, pyparsing.ParseResults):
                self.gather_joins(item, notted)

    def convert_where(self, node):

        for item in node:
            to_not = True if item == "not" else False
            to_and = True if item == "and" else False
            to_or = True if item == "or" else False
            if any([to_not, to_and, to_or]):
                break


        if node.operator:
            if node.table:
                table_class = getattr(self.search.database.t,node.table)
            else:
                table_class = getattr(self.search.database.t,self.search.table)
            
            field = getattr(table_class, node.field)

            if node.operator == "<":
                return or_(field < node.value, table_class.id == None)
            if node.operator == "<=":
                return or_(field <= node.value, table_class.id == None)
            if node.operator == "<>":
                return or_(field <> node.value, table_class.id == None)
            if node.operator == "=":
                return and_( field == node.value, table_class.id <> None)
            if node.operator == ">":
                return and_(field > node.value, table_class.id <> None)
            if node.operator == ">=":
                return and_(field >= node.value, table_class.id <> None)
            if node.operator == "in":
                return and_(field.in_(list(node.value)), table_class.id <> None)
            if node.operator == "between":
                return and_(field.between(node.value, node.value2), table_class.id <> None)
            if node.operator == "like":
                return and_(field.ilike(node.value), table_class.id <> None)
            if node.operator == "is":
                return field == None
            if node.operator == "not":
                return field <> None

        if to_not:
            return not_(self.convert_where(node[1]))
        if to_or:
            ors = [self.convert_where(stat) for stat in node[0::2]]
            return or_(*ors)
        if to_and:
            ors = [self.convert_where(stat) for stat in node[0::2]]
            return and_(*ors)
    
        raise 
    

    def parser(self):
        
        Word = pyparsing.Word
        Literal = pyparsing.Literal
        Group = pyparsing.Group
        Combine = pyparsing.Combine
        nums = pyparsing.nums
        CaselessKeyword = pyparsing.CaselessKeyword

        attr = Word(pyparsing.alphanums + "_" )

        def convert_unicode(tok):
            return u"%s" % tok[0]


        string_value = Word(pyparsing.alphanums)
        iso_date = Word(nums, exact =4) + Literal("-") +\
                   Word(nums, exact =2) + Literal("-") + Word(nums, exact = 2)

        uk_date = Word(nums, exact = 2) + Literal("/") +\
                     Word(nums, exact = 2) + Literal("/") + Word(nums, exact = 4)

        def convert_iso(tok):
            return datetime.datetime.strptime(tok[0], "%Y-%m-%d")

        def convert_uk(tok):
            return datetime.datetime.strptime(tok[0], "%d/%m/%Y")

        def convert_now(tok):
            return datetime.datetime.now()

        def convert_now_diff(tok):

            if tok[3] == "days":
                timediff = timedelta(days = int(tok[1]+tok[2]))
            if tok[3] in ("mins", "minutes"):
                timediff = timedelta(minutes = int(tok[1]+tok[2]))
            if tok[3] == "hours":
                timediff = timedelta(hours = int(tok[1]+tok[2]))

            return datetime.datetime.now() + timediff

        now_diff = CaselessKeyword("now") + (Literal("+") | Literal("-")) + Word(pyparsing.nums) + \
                   (CaselessKeyword("days") | CaselessKeyword("mins") | CaselessKeyword("minutes") | CaselessKeyword("hours"))
        

        date = now_diff.setParseAction(convert_now_diff) |\
               pyparsing.CaselessKeyword("now").setParseAction(convert_now) |\
               Combine(iso_date).setParseAction(convert_iso) |\
               Combine(uk_date).setParseAction(convert_uk)

        def convert_decimal(tok):
            return Decimal(tok[0], 2)

        decimal = Combine(Word(nums) + Literal(".") + Word(nums, exact = 2)).setParseAction(convert_decimal)

        string_no_quote = Word(pyparsing.alphanums + "_").setParseAction(convert_unicode)


        def remove_quotes(str):
            return u"%s" % str[0][1:-1]

        value = date | decimal | Word(nums) | pyparsing.quotedString.setParseAction(remove_quotes) |string_no_quote

        objwithtable = attr.setResultsName("table") +\
                       Literal(".").suppress() +\
                       attr.setResultsName("field")
                        
        objnotable = attr.setResultsName("field")

        obj = objwithtable | objnotable

        is_ = pyparsing.CaselessKeyword("is")
        is_not = is_.suppress() + pyparsing.CaselessKeyword("not")

        null_comarison = (is_not | is_).setResultsName("operator") + pyparsing.CaselessKeyword("null").setResultsName("value")
        
        comparison = ((Literal("<>") | Literal("<=") | Literal("<") | Literal("=") | Literal(">=") |\
                       Literal(">")).setResultsName("operator") + \
                       value.setResultsName("value"))

        between = pyparsing.CaselessKeyword("between").setResultsName("operator") +\
                  value.setResultsName("value") +\
                  pyparsing.CaselessKeyword("and") +\
                  value.setResultsName("value2")


        like = pyparsing.CaselessKeyword("like").setResultsName("operator") +\
               value.setResultsName("value")


        in_ = pyparsing.CaselessKeyword("in").setResultsName("operator") +\
              (Literal("(").suppress() +\
              Group(pyparsing.delimitedList(value)).setResultsName("value") +\
              Literal(")").suppress())

        singlexpr =  pyparsing.Group( obj + (null_comarison|between|comparison|like|in_) )

        expression = pyparsing.StringStart() + pyparsing.operatorPrecedence(singlexpr,
                [
                ("not", 1, pyparsing.opAssoc.RIGHT),
                ("or",  2, pyparsing.opAssoc.LEFT),
                ("and", 2, pyparsing.opAssoc.LEFT),
                ]) + pyparsing.StringEnd()
        

        return expression


class Expression(object):

    def __init__(self, val, pos, tok):

        self.pos = pos
        self.tok = tok[0]
        self.val = val

        self.table = self.tok.table
        self.field = self.tok.field

        if self.table:
            self.field_name = "%s.%s" % (self.table, self.field)
        else:
            self.field_name = self.field


        self.operator = tok[0].operator

        self.params = []


        if self.operator == "in":
            for value in self.tok.value:
                self.convert_value(value)
        elif self.operator == "between":
            self.convert_value(self.tok.value)
            self.convert_value(self.tok.value2)
        else:
            self.convert_value(self.tok.value)

        self.param_values = [None] * len(self.params)

    def convert_value(self, value):

        if value.name:
            self.params.append(value.name)
        elif value.positional:
            self.params.append("?")
        else:
            self.params.append(self.field_name)

    def make_sa_expression(self, database, root_table):

        self.database = database
        self.root_table = root_table

        if self.table:
            self.table_class = getattr(database.t, self.table)
        else:
            self.table_class = getattr(database.t, root_table)

        rtable = self.table_class()._table

        if self.field == "id":
            self.type = sa.Integer
        else:
            self.type = rtable.columns[self.field].type

        self.parsed_values = []

        self.parse_values()

        field = getattr(self.table_class, self.field)
        table_class = self.table_class

        val = self.parsed_values

        if self.operator == "<":
            return or_(field < val[0], table_class.id == None)
        if self.operator == "<=":
            return or_(field <= val[0], table_class.id == None)
        if self.operator == "<>":
            return or_(field <> val[0], table_class.id == None)
        if self.operator == "=":
            return and_( field == val[0], table_class.id <> None)
        if self.operator == ">":
            return and_(field > val[0], table_class.id <> None)
        if self.operator == ">=":
            return and_(field >= val[0], table_class.id <> None)
        if self.operator == "in":
            return and_(field.in_(list(val)), table_class.id <> None)
        if self.operator == "between":
            return and_(field.between(val[0], val[1]), table_class.id <> None)
        if self.operator == "like":
            return and_(field.ilike(val[0]), table_class.id <> None)
        if self.operator == "is" and val[0]:
            return field == None
        if self.operator == "is" and not val[0]:
            return field <> None

    def parse_values(self):

        for value in self.param_values:
            parsed_value = self.parse_value(value)
            self.parsed_values.append(parsed_value)

    def parse_value(self, value):

        if self.operator == "is":
            if value.lower().strip() == "null":
                return True
            if value.lower().strip().replace(" ", "")  == "notnull":
                return False
            raise InvalidArgument("is arguement has to be either"
                                  "'null' or 'not null'")

        if self.type == sa.Integer:
            return int(value)

        if self.type == sa.Unicode or isinstance(self.type, sa.Unicode):
            return u"%s" % value

        if self.type == sa.Boolean:

            if isinstance(value, bool):
                return value
            if isinstance(value, int):
                return bool(value)
            if value.lower() in ("false", "0"):
                return False
            elif value.lower() in ("true", "1"):
                return True

        if self.type == sa.DateTime:
            return self.parse_date(value)

        if self.type == sa.Numeric:
            return Decimal(str(value))

        raise Exception("type %s not allowed in query" % self.type)



    def parse_date(self, value):

        if isinstance(value, datetime.datetime):
            return value

        return self.date_parser().parseString(value)[0]


    def date_parser(self):

        Word = pyparsing.Word
        Literal = pyparsing.CaselessLiteral
        Combine = pyparsing.Combine
        CaselessKeyword = pyparsing.CaselessKeyword
        nums = pyparsing.nums

        iso_date_partial = Word(nums, exact =4) + Literal("-") +\
                   Word(nums, exact =2) + Literal("-") + Word(nums, exact = 2)

        iso_date_full = iso_date_partial + Literal("T") + Word(nums, exact = 2)\
                + Literal(":") + Word(nums, exact = 2) + Literal(":") + Word(nums, exact = 2) + Literal("Z")

        def convert_iso_partial(tok):
            return datetime.datetime.strptime(tok[0], "%Y-%m-%d")

        def convert_iso_full(tok):
            return datetime.datetime.strptime(tok[0], "%Y-%m-%dT%H:%M:%SZ")

        def convert_now(tok):
            return datetime.datetime.now()

        def convert_now_diff(tok):

            if tok[3] == "days":
                timediff = timedelta(days = int(tok[1]+tok[2]))
            if tok[3] in ("mins", "minutes"):
                timediff = timedelta(minutes = int(tok[1]+tok[2]))
            if tok[3] == "hours":
                timediff = timedelta(hours = int(tok[1]+tok[2]))

            return datetime.datetime.now() + timediff

        now_diff = CaselessKeyword("now") + (Literal("+") | Literal("-")) + Word(pyparsing.nums) + \
                   (CaselessKeyword("days") | CaselessKeyword("mins") | CaselessKeyword("minutes") | CaselessKeyword("hours"))
        

        date = now_diff.setParseAction(convert_now_diff) |\
               pyparsing.CaselessKeyword("now").setParseAction(convert_now) |\
               Combine(iso_date_full).setParseAction(convert_iso_full) |\
               Combine(iso_date_partial).setParseAction(convert_iso_partial) 

        return date


class QueryFromStringParam(object):

    def __init__(self, search, *args, **kw):

        self.search = search
        self.query = args[0]

        self.query = args[0]

        parser = self.parser()

        self.ast = parser.parseString(self.query)

        self.expressions = []
        self.gather_expressions(self.ast)

        self.expressions.sort(lambda a, b: a.pos - b.pos) 


        self.pos_args = kw.get("pos_args", [])
        self.named_args = kw.get("named_args", {})


        if kw.get("test", False):
            return

        self.add_positional(self.pos_args) 
        self.add_named(self.named_args)

        if not self.search:
            return

        self.covering_ors = set()

        self.inner_joins = set()
        self.outer_joins = set()

        self.gather_joins(self.ast, False)
        self.gather_covering_ors(self.ast, False, False)

        self.where = self.convert_where(self.ast[0])


    def add_conditions(self, sa_query):

        for join in self.outer_joins.union(self.covering_ors):
            if join <> self.search.table:
                sa_query = sa_query.outerjoin(self.search.aliased_name_path[join])

        for join in self.inner_joins:
            if join <> self.search.table:
                sa_query = sa_query.join(self.search.aliased_name_path[join])

        sa_query = sa_query.filter(self.where)

        return sa_query

    def gather_covering_ors(self, node, notted, ored):

        for item in node:
            if item == "not":
                notted = not notted
            if item == "or" and not notted:
                ored = True
            if item == "and" and notted:
                ored = True

        for item in node:
            if isinstance(item, Expression) and item.table and ored:
                self.covering_ors.update([item.table])
                
            if isinstance(item, pyparsing.ParseResults):
                self.gather_covering_ors(item, notted, ored)

    def gather_joins(self, node, notted):

        for item in node:
            if item == "not":
                notted = not notted

        for item in node:
            if isinstance(item, Expression) and item.table:
                if item.operator in ("<", "<=") and not notted or\
                   item.operator not in ("<", "<=") and notted:
                    self.outer_joins.update([item.table])
                else:
                    self.inner_joins.update([item.table])

            if isinstance(item, pyparsing.ParseResults):
                self.gather_joins(item, notted)

    def convert_where(self, node):

        if isinstance(node, Expression):
            return node.make_sa_expression(self.search.database, self.search.table)

        for item in node:
            to_not = True if item == "not" else False
            to_and = True if item == "and" else False
            to_or = True if item == "or" else False
            if any([to_not, to_and, to_or]):
                break

        if to_not:
            return not_(self.convert_where(node[1]))
        if to_or:
            ors = [self.convert_where(stat) for stat in node[0::2]]
            return or_(*ors)
        if to_and:
            ors = [self.convert_where(stat) for stat in node[0::2]]
            return and_(*ors)
    
        raise 

    def exprssion_obj_maker(self, tok, pos, val):

        return Expression(tok, pos, val)

    
    def gather_expressions(self, node):

        for item in node:
            if isinstance(item, pyparsing.ParseResults):
                self.gather_expressions(item)
            if isinstance(item, Expression):
                self.expressions.append(item)

    def add_positional(self, arg_list):

        arg_list = arg_list[:]

        for expression in self.expressions:
            for num, arg in enumerate(expression.params):
                if arg == "?":
                    try:
                        value = arg_list.pop(0)
                        expression.param_values[num] = value
                    except IndexError, e:
                        raise IndexError("Not enough positional args")

        if arg_list:
            raise IndexError("Too many positional args")

    def add_named(self, arg_dict):

        for expression in self.expressions:
            for num, arg in enumerate(expression.params):
                if arg not in ("?"):
                    try:
                        value = arg_dict[arg]
                        expression.param_values[num] = value
                    except KeyError, e:
                        raise KeyError("%s argument not in param dict" % arg)

    def parser(self):

        Word = pyparsing.Word
        Literal = pyparsing.Literal
        Group = pyparsing.Group
        Combine = pyparsing.Combine
        nums = pyparsing.nums
        CaselessKeyword = pyparsing.CaselessKeyword

        attr = Word(pyparsing.alphanums + "_" )
        name = Word(pyparsing.alphanums + "_" )


        objwithtable = attr.setResultsName("table") +\
                       Literal(".").suppress() +\
                       attr.setResultsName("field")
                        
        objnotable = attr.setResultsName("field")

        obj = objwithtable | objnotable

        named_param = Literal("{") + name.setResultsName("name") + Literal("}")
        assumed_named_param = Literal("{") + Literal("}")
        positional_param = Literal("?").setResultsName("positional")


        value = Group(named_param | assumed_named_param | positional_param)



        is_ = pyparsing.CaselessKeyword("is")

        null_comarison = is_.setResultsName("operator") + value.setResultsName("value")
        
        comparison = ((Literal("<>") | Literal("<=") | Literal("<") | Literal("=") | Literal(">=") |\
                       Literal(">")).setResultsName("operator") + \
                       value.setResultsName("value"))

        between = pyparsing.CaselessKeyword("between").setResultsName("operator") +\
                  value.setResultsName("value") +\
                  pyparsing.CaselessKeyword("and") +\
                  value.setResultsName("value2")


        like = pyparsing.CaselessKeyword("like").setResultsName("operator") +\
               value.setResultsName("value")


        in_ = pyparsing.CaselessKeyword("in").setResultsName("operator") +\
              (Literal("(").suppress() +\
              Group(pyparsing.delimitedList(value)).setResultsName("value") +\
              Literal(")").suppress())

        singlexpr =  pyparsing.Group( obj + (null_comarison|between|comparison|like|in_)).setParseAction(self.exprssion_obj_maker)

        expression = pyparsing.StringStart() + pyparsing.operatorPrecedence(singlexpr,
                [
                ("not", 1, pyparsing.opAssoc.RIGHT),
                ("or",  2, pyparsing.opAssoc.LEFT),
                ("and", 2, pyparsing.opAssoc.LEFT),
                ]) + pyparsing.StringEnd()
        

        return expression
