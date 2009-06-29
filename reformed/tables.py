##   This file is part of Reformed.
##
##   Reformed is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License version 2 as 
##   published by the Free Software Foundation.
##
##   Reformed is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with Reformed.  If not, see <http://www.gnu.org/licenses/>.
##
##   -----------------------------------------------------------------
##	
##   Reformed
##   Copyright (c) 2008-2009 Toby Dacre & David Raznick
##	
##	tables.py
##	======
##	
##	This file contains the reformed Table class. A Table is 
##  collection of Field objects and the Table objects uses these to make
##  make a real database table and store the metadata in private tables in
##  the database.

import sqlalchemy as sa
from sqlalchemy.orm import mapper
from columns import Column
from custom_exceptions import NoMetadataError, NoDatabaseError
import formencode
from formencode import validators
from fields import Modified, Integer
from util import get_paths, make_local_tables
import logging
import migrate.changeset

LOGGER = logging.getLogger('reformed.main')

class Table(object):
    """ this holds metadata relating to a database table.  It also
    contains methods to create a sqlalchemy Table,Mapper and Class."""
    
    
    def __init__(self, name, *args , **kw):
        """ 
        name:  name of the table
        primary_key:   a comma delimited string stating what field
                       should act as a primary key.
        logged: Boolean stating if the table should be logged
        modified_date: Boolean stating if the table should have a last 
                       modified date
        index:  a semicolon (;) delimited list of the columns to be indexed
        unique_constraint : a semicolon delimeited list of colums with a 
                           unique constraint
        *args :  All the Field objects this table has.
        """
        self.name = name
        self.kw = kw
        self.table_id = kw.get("table_id", None)
        self.field_list = args
        self.fields = {}
        self.field_order = []
        self.primary_key = kw.get("primary_key", None)
        #persisted should be private
        self.persisted = kw.get("persisted", False)
        self.entity = kw.get("entity", False)
        self.logged = kw.get("logged", True)
        self.modified_date = kw.get("modified_date", True)
        self.index = kw.get("index", None)
        self.unique_constraint = kw.get("unique_constraint", None)
        self.entity_relationship = kw.get("entity_relationship", False)
        self.primary_key_list = []
        if self.primary_key:
            self.primary_key_list = self.primary_key.split(",")
        self.index_list  = []
        if self.index:
            self.index_list = [column_list.split(",") for column_list in
                               self.index.split(";")]
        self.unique_constraint_list  = []
        if self.unique_constraint:
            self.unique_constraint_list = [column_list.split(",") 
                                           for column_list in
                                           self.unique_constraint.split(";")]

        for fields in args:
            fields._set_parent(self)

        if "modified_date" not in self.fields.iterkeys() and self.modified_date:
            self.add_field(Modified("modified_date"))
            self.add_field(Integer("modified_by" , default = 1))

        #sqlalchemy objects
        self.sa_table = None
        self.sa_class = None
        self.mapper = None
        self.paths = None
        self.local_tables = None
        self.one_to_many_tables = None

    def persist(self):
        """This puts the information about the this objects parameters 
        and its collection of fields into private database tables so that in future they
        no longer need to be explicitely defined"""
                
        session = self.database.Session()
        __table = self.database.tables["__table"].sa_class()
        __table.table_name = u"%s" % self.name


        for name, param in self.kw.iteritems():
            __table_param = self.database.get_instance("__table_params")
            __table_param.item = u"%s" % name
            __table_param.value = u"%s" % str(param) 
            __table.table_params.append(__table_param)

        for field_name, field  in self.fields.iteritems():
            __field = self.database.tables["__field"].sa_class()
            __field.field_name = u"%s" % field_name
            __field.type = u"%s" % field.__class__.__name__
            if hasattr(field, "other"):
                __field.other = u"%s" % field.other
            
            for name, param in field.kw.iteritems():
                __field_param = self.database.get_instance("__field_params")
                __field_param.item = u"%s" % name
                __field_param.value = u"%s" % str(param) 
                __field.field_params.append(__field_param)

            __table.field.append(__field)

        session.add(__table)
        session.commit()
        self.table_id = __table.id
        self.persisted = True
        session.close()

    def add_field(self, field):
        """add a Field object to this Table"""
        if self.persisted == True:
            field.check_table(self)
            self._add_field_by_alter_table(field)
            self._persist_extra_field(field)
            self._add_field_no_persist(field)
            self.database.update_sa(reload = True)

        else:
            self._add_field_no_persist(field)

    def _add_field_no_persist(self, field):
        """add a Field object to this Table"""
        field._set_parent(self)

    def _add_field_by_alter_table(self, field):
        for name, column in field.columns.iteritems():
            col = sa.Column(name, column.type, **column.sa_options)
            col.create(self.sa_table)

    def _persist_extra_field(self, field):

        session = self.database.Session()
        __table = session.query(self.database.get_class("__table")).\
                                filter_by(table_name = u"%s" % self.name).one()
        __field = self.database.tables["__field"].sa_class()
        __field.field_name = u"%s" % field.name
        __field.type = u"%s" % field.__class__.__name__
        if hasattr(field, "other"):
            __field.other = u"%s" % field.other
        
        for name, param in field.kw.iteritems():
            __field_param = self.database.tables["__field_params"].sa_class()
            __field_param.item = u"%s" % name
            __field_param.value = u"%s" % str(param) 
            __field.field_params.append(__field_param)

        __table.field.append(__field)

        session.add(__table)
        session.commit()
        session.close()

    @property    
    def items(self):
        """gathers all columns and relations defined in this table"""
        items = {}
        for fields in self.fields.itervalues():
            for name, item in fields.items.iteritems():
                items[name] = item
        return items

    @property    
    def defined_columns(self):
        """gathers all columns defined in this table"""
        columns = {}
        for field in self.fields.itervalues():
            for name, column in field.columns.iteritems():
                columns[name] = column
        return columns

    @property
    def defined_columns_order(self):
        column_order = []
        for field in self.field_order:
            for column in self.fields[field].column_order:
                column_order.append(column)
        return column_order

    @property    
    def columns(self):
        """gathers all columns this table has whether defined here on in
        another tables relation"""
        columns = {}
        for field in self.fields.itervalues():
            for name, column in field.columns.iteritems():
                columns[name] = column
        try:
            for name, column in self.foriegn_key_columns.iteritems():
                columns[name] = column
        except NoDatabaseError:
            pass
        return columns

  
    def add_relations(self):   # this is not a property for an optimisation
        """gathers all relations defined in this table"""
        relations = {}
        for field in self.fields.itervalues():
            for name, relation in field.relations.iteritems():
                relations[name] = relation
        self.relations = relations

    @property
    def primary_key_columns(self):
        """gathers all primary key columns in this table"""
        columns = {}
        if self.primary_key:
            for name, column in self.columns.iteritems():
                if name in self.primary_key_list:
                    columns[name] = column
        return columns

    @property
    def defined_non_primary_key_columns(self):
        """gathers all non primary key columns in this table"""
        columns = {}
        for name, column in self.defined_columns.iteritems():
            if name not in self.primary_key_list:
                columns[name] = column
        return columns

    def check_database(self):
        """checks if this table is part of a Database object"""
        if not hasattr(self, "database"):
            raise NoDatabaseError,\
                  "Table %s has not been assigned a database" % self.name

    def _set_parent(self, database):
        """adds this table to a database object"""
        database.tables[self.name]=self
        database.add_relations()
        self.database = database

    @property    
    def tables_with_relations(self):
        """returns a dictionary of all related tables and the relation object
        that was defined that related them"""
        self.check_database()
        return self.database.tables_with_relations(self)

    @property    
    def foriegn_key_columns(self):
        """gathers the extra columns in this table that are needed as the tables
        are related. i.e if this table is the many side of a one to many
        relationship it will return the primary key on the "one"
        side"""

        
        self.check_database()
        database = self.database
        columns={}
        ##  could be made simpler
        for tab, rel in self.tables_with_relations.iteritems():
            table, pos = tab
            #use pos
            if (rel.type == "onetomany" and self.name == rel.other) or\
              (rel.type == "onetoone" and self.name == rel.other) or\
              (rel.type == "manytoone" and self.name == rel.table.name):
                if database.tables[table].primary_key_columns:
                    table = database.tables[table]
                    for name, column in table.primary_key_columns.items():
                        new_col = Column(column.type,
                                         name=name,
                                         mandatory = rel.many_side_mandatory,
                                         defined_relation= rel,
                                         original_column= name) 
                        columns[name] = new_col
                else:
                    if table+"_id" not in columns:
                        columns[table+'_id'] = Column(sa.Integer,
                                                       name = table+'_id',
                                                       defined_relation= rel,
                                                       original_column= "id")
                    else:
                        columns[table+'_id2'] = Column(sa.Integer,
                                                       name = table+'_id2',
                                                       defined_relation= rel,
                                                       original_column= "id")
        return columns


    @property
    def foreign_key_constraints(self):

        """gathers a dictionary of all the foreign key columns in this table
        with their related primary key colums.  The key is the other table name
        and the values are a pair of linked lists by their index.  The first list
        has the foriegn key columns in this table and the second the accocited
        primary key columns the the related tabel"""

        fk_constraints = {}
        self.check_database()
        ##  could be made simpler
        for tab, rel in self.tables_with_relations.iteritems():
            table, pos = tab
            other_table_columns=[]
            this_table_columns=[]
            for name, column in self.foriegn_key_columns.iteritems():
                if column.defined_relation == rel:
                    other_table_columns.append("%s.%s"%\
                                               (table, column.original_column))
                    this_table_columns.append(name)
            if other_table_columns:
                fk_constraints[(table, rel.name)] = [this_table_columns,
                                                    other_table_columns]
        return fk_constraints

    def make_sa_table(self):
        """makes a sqlalchemy table object and stores it in the 
        attribute sa_table"""
        #make sure table is not already made
        if self.sa_table:
            return
        self.check_database()
        if not self.database.metadata:
            raise NoMetadataError("table not assigned a metadata")
        sa_table = sa.Table(self.name, self.database.metadata)
        sa_table.append_column(sa.Column("id", sa.Integer, primary_key = True))
        for name, column in self.foriegn_key_columns.iteritems():
            sa_options = column.sa_options
            sa_table.append_column(sa.Column(name, column.type, **sa_options))
        defined_columns = self.defined_columns
        for column in self.defined_columns_order:
            name = column
            column = defined_columns[column]
            sa_options = column.sa_options
            sa_table.append_column(sa.Column(name, column.type, **sa_options))
        if self.primary_key_list:
            primary_keys = tuple(self.primary_key_list)
            sa_table.append_constraint(sa.UniqueConstraint(*primary_keys))
        if self.foreign_key_constraints:
            for con in self.foreign_key_constraints.itervalues():
                sa_table.append_constraint(sa.ForeignKeyConstraint(con[0],
                                                                   con[1]))
        if self.index_list:
            for index in self.index_list:
                ind = [sa_table.columns[col] for col in index]
                name = "_".join(index)
                sa_table.append_constraint(sa.Index(name, *ind))
        if self.unique_constraint_list:
            for constraint in self.unique_constraint_list:
                sa_table.append_constraint(sa.UniqueConstraint(*constraint))
        self.sa_table = sa_table
   
    def make_sa_class(self):
        """makes a class to be mapped and stores it in the attribute sa_class"""
        #make sure class is not already made
        if self.sa_class:
            return
        table = self
        class sa_class(object):
            def __init__(self):
                self._table = table

            @sa.orm.reconstructor
            def init_onload(self):
                self._table = table
                

        sa_class.__name__ = self.name
        self.sa_class = sa_class

    def sa_mapper(self):
        """runs sqlalchemy mapper to map the sa_table to sa_class and stores  
        the mapper object in the 'mapper' attribute"""
        #make sure mapping has not been done
        if self.mapper:
            return

        properties ={}
        for relation in self.relations.itervalues():
            sa_options = relation.sa_options
            other_rtable = self.database.tables[relation.other]
            other_table = other_rtable.sa_table
            other_class = self.database.tables[relation.other].sa_class
            order_by = self._make_sa_order_by_list(relation, other_table)
            if order_by:
                sa_options["order_by"] = order_by
            if "backref" not in sa_options:
                sa_options["backref"] = "_%s"% self.name

            joined_columns = []

            for name, column in self.foriegn_key_columns.iteritems():
                if relation == column.defined_relation:
                    joined_columns.append([name, column.original_column])
            if not joined_columns:
                joined_columns.extend([[a, a] for a in self.primary_key_list])
            if not joined_columns:
                for name, col in other_rtable.foriegn_key_columns.iteritems():
                    if relation == col.defined_relation:
                        joined_columns.append([col.original_column, name])

            join_conditions = [] 
            for col1, col2 in joined_columns:
                join_conditions.append(getattr(self.sa_table.c, col1) ==\
                                       getattr(other_table.c, col2))

            sa_options["primaryjoin"] = sa.sql.and_(*join_conditions)
            
            properties[relation.name] = sa.orm.relation(other_class,
                                                    **sa_options)

        self.mapper = mapper(self.sa_class,
                             self.sa_table,
                             properties = properties)
    
    def make_paths(self):

        if not self.paths:
            self.paths = get_paths(self.database.graph, self.name)

        if not self.local_tables:
            local_tables, one_to_many_tables = make_local_tables(self.paths)
            self.local_tables = local_tables
            self.one_to_many_tables = one_to_many_tables

    
    def _make_sa_order_by_list(self, relation, other_table):

        order_by = [] 
        if relation.order_by_list:
            for col in relation.order_by_list:
                if col[1] == 'desc':
                    order_by.append(getattr(other_table.c, col[0]).desc())
                else:
                    order_by.append(getattr(other_table.c, col[0]))
        return order_by
 
    def validation_from_field_types(self, column):
        formencode_all = formencode.All()
        validators = formencode_all.validators
        col_type = column.type
        #TODO do not make mand when forighn key column
        mand = not column.sa_options.get("nullable", True)
        val = formencode.validators
        if col_type is sa.Unicode or isinstance(col_type, sa.Unicode):
            if hasattr(col_type, 'length'):
                if col_type.length:
                    max = col_type.length
                else:
                    max = 100
            else:
                max = 100
            validators.append(val.UnicodeString(max = max,
                                                not_empty = mand))
        elif col_type is sa.Integer or isinstance(col_type, sa.Integer):
            validators.append(val.Int(not_empty = mand))
        elif col_type is sa.Numeric or isinstance(col_type, sa.Numeric):
            validators.append(val.Number(not_empty = mand))
        elif col_type is sa.DateTime or isinstance(col_type, sa.DateTime):
            validators.append(val.DateValidator(not_empty = mand))
        elif col_type is sa.Boolean or isinstance(col_type, sa.Boolean):
            validators.append(val.Bool(not_empty = mand))
        elif col_type is sa.Binary or isinstance(col_type, sa.Binary):
            validators.append(val.FancyValidator(not_empty = mand))
        return formencode_all

    @property
    def validation_schema(self):
        """Gathers all the validation dictionarys from all the Field Objects
        and a makes a formencode Schema out of them"""
        schema_dict = {}

        for column in self.columns.itervalues():
            schema_dict[column.name] = self.validation_from_field_types(column)
            if column.validation:
                if column.validation.startswith("__"):
                    validator = validators.Regex(column.validation[2:])
                else:
                    validator = getattr(validators, column.validation)()
                schema_dict[column.name].validators.append(validator)

        for field in self.fields.itervalues():
            if hasattr(field, "validation"):
                for name, validation in field.validation.iteritems():
                    schema_dict[name].validators.append(validation)

        return formencode.Schema(allow_extra_fields =True,
                                 ignore_key_missing = True,
                                 **schema_dict)
    
    def validate(self, instance):
        """this validates an instance of sa_class with the schema defined
        by this tables Field objects"""
        
        validation_dict = {}
        for name in self.columns.iterkeys():
            validation_dict[name] = getattr(instance, name)

        return self.validation_schema.to_python(validation_dict)
    
    def logged_instance(self, instance):
        """this creates a copy of an instace of sa_class"""
        
        ##not used as sessionwrapper now does this
        logged_instance = self.database.tables["_log_" + self.name].sa_class()
        for name in self.columns.iterkeys():
            setattr(logged_instance, name, getattr(instance, name))
        return logged_instance

    

