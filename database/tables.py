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
import logging
import datetime

import migrate.changeset
import sqlalchemy as sa
from sqlalchemy.orm import mapper
from sqlalchemy.sql.expression import ClauseElement
import formencode
from formencode import validators
from sqlalchemy.orm import column_property, backref
from sqlalchemy.orm.interfaces import AttributeExtension
from sqlalchemy.sql import text

from ZODB.PersistentMapping import PersistentMapping
from ZODB.PersistentList import PersistentList
import transaction

import fshp
from columns import Column
from custom_exceptions import NoMetadataError, NoDatabaseError
from validators import All, UnicodeString, RequireIfMissing
from fields import Modified, ModifiedBySession, Integer
import fields
from util import get_paths, make_local_tables, create_table_path_list, create_table_path
from util import OrderedDict, SchemaLock

log = logging.getLogger('rebase.application.database')

class Table(object):
    """ this holds metadata relating to a database table.  It also
    contains methods to create a sqlalchemy Table,Mapper and Class."""

    modifiable_kw = ["quiet", "lookup", "table_class", "primary_entities",
                    "secondary_entities", "logged", "validated",
                    "table_type", "title_field", "description_field",
                     "summary_fields", "summary", "default_node",
                    "valid_info_tables"]

    restricted_kw = ["table_id", "field_order", "persisted",
                     "primary_key", "entity", "relation", "info_table",
                     "modified_by", "modified_date", "version", "entity_relationship"]



    def __init__(self, name, *args , **kw):
        """
        name:  name of the table
        primary_key:   a comma delimited string stating what field
                       should act as a primary key.
        logged: Boolean stating if the table should be logged
        modified_by: Boolean stating if the table should have a last
                       modified by
        *args :  All the Field objects this table has.
        """

        self.all_kw = set(self.modifiable_kw + self.restricted_kw)
        self.all_updatable_kw = set(self.modifiable_kw)
        assert set(kw.keys()) - self.all_kw == set()

        self.name = name
        self.kw = kw
        self.args = args
        self.table_id = kw.get("table_id", None)
        self.field_list = []
        self.fields = OrderedDict()
        self.field_order = kw.get("field_order", [])
        self.current_order = 0
        self.primary_key = kw.get("primary_key", None)
        #persisted should be private
        self.persisted = kw.get("persisted", False)
        self.quiet = kw.get("quiet", False)

        # table types
        self.entity = kw.get("entity", False)
        self.relation = kw.get("relation", False)
        self.lookup = kw.get("lookup", False)
        self.info_table = kw.get("info_table", False)
        self.table_class = kw.get("table_class")

        ## for relaion tables
        primary_entities = kw.get("primary_entities")
        if primary_entities :
            self.primary_entities = primary_entities.strip().split(",")

        secondary_entities = kw.get("secondary_entities")
        if secondary_entities:
            self.secondary_entities = secondary_entities.strip().split(",")


        ## for entity or relation tables
        valid_info_tables = kw.get("valid_info_tables")
        if valid_info_tables:
            self.valid_info_tables = valid_info_tables.split()
        else:
            self.valid_info_tables = []

        ## for info tables to be populated
        self.valid_core_types = []

        self.max_field_id = 0

        self.logged = kw.get("logged", True)
        self.validated = kw.get("validated", True)

        self.modified_date = kw.get("modified_date", True)
        self.modified_by = kw.get("modified_by", True)
        self.version = kw.get("version", True)

        self.table_type = kw.get("table_type", "user")

        self.title_field = kw.get("title_field", None)
        self.description_field = kw.get("description_field", None)
        self.summary_fields = kw.get("summary_fields", None)
        self.summary = kw.get("summary", None)
        self.default_node = kw.get("default_node", None)

        self.primary_key_list = []

        if self.primary_key:
            self.primary_key_list = self.primary_key.split(",")

        self.events = dict(new = [],
                           delete = [],
                           change = [])

        for field in args:
            field._set_parent(self)

        if "_version" not in self.fields and self.version:
            self.add_field(Integer("_version"))
        if "_modified_date" not in self.fields and self.modified_date:
            self.add_field(Modified("_modified_date"))
        if "_modified_by" not in self.fields and self.modified_by:
            self.add_field(ModifiedBySession("_modified_by"))

        self.foriegn_key_columns_current = None
        #sqlalchemy objects
        self.sa_table = None
        self.sa_class = None
        self.mapper = None
        self.paths = None
        self.local_tables = None
        self.one_to_many_tables = None
        self.table_path_list = None
        self.table_path = None
        self.schema_dict = None
        self.schema = None

        self.columns_cache = None

    def code_repr(self):
        header = "Table('%s',\n    " % self.name
        footer = "\n)"
        field_list = [field.code_repr() for field in
                      sorted(self.field_list, key = lambda x:x.field_id)]
        fields_repr = ",\n    ".join(field_list)
        kw_repr = ""
        kw_list = ["%s = %s" % (i[0], repr(i[1])) for i in self.kw.items()]
        if self.kw:
            kw_repr = ",\n    " + ",\n    ".join(sorted(kw_list))

        return header + fields_repr + kw_repr + footer

    def __repr__(self):
        return "%s - %s" % (self.name, self.columns.keys())

    def set_kw(self, key, value):

        if key not in self.all_updatable_kw:
            raise ValueError("%s not allowed to be added or modified" % key)

        with SchemaLock(self.database) as file_lock:
            setattr(self, key, value)
            self.kw[key] = value
            file_lock.export()


    def add_foreign_key_columns(self):

        for column in self.foriegn_key_columns.values():
            original_col = column.original_column
            name = column.name
            if original_col == "id" and name not in self.defined_columns:
                relation = column.defined_relation
                field = relation.parent
                new_field = Integer(name, mandatory = relation.many_side_not_null,
                                    default = relation.many_side_default,
                                    onupdate = relation.many_side_onupdate)

                self._add_field_no_persist(new_field)
                field.kw["foreign_key_name"] = name
                field.foreign_key_name = name


    def add_relation(self, field):

        #TODO make into more general add relation, currently
        #only works if both tables are already persisted
        if not self.persisted:
            self._add_field_no_persist(field)
            return

        with SchemaLock(self.database) as file_lock:
            self._add_field_no_persist(field)

            self.database.add_relations()
            name, relation = field.relations.copy().popitem()
            fk_table = self.database[relation.foreign_key_table]
            pk_table = self.database[relation.primary_key_table]

            for name, column in fk_table.foriegn_key_columns.iteritems():
                if column.defined_relation.parent == field:
                    sa_options = column.sa_options
                    ## sqlite rubbish
                    if self.database.engine.name == 'sqlite':
                        sa_options["server_default"] = "null"
                    col = sa.Column(name, column.type, **sa_options)
                    fk_table.add_foreign_key_columns()
                    file_lock.export(uuid = True)
                    print "hererer"
                    col.create(fk_table.sa_table)

            for name, con in fk_table.foreign_key_constraints.iteritems():

                if self.database.engine.name == 'sqlite':
                    break

                fk_const = migrate.changeset.constraint.ForeignKeyConstraint(con[0],
                                                   con[1], name = name, table = fk_table.sa_table)

                if name == relation.foreign_key_constraint_name:
                    fk_const.create()
            file_lock.export()
            self.database.load_from_persist(True)

    def delete_relation(self, field):

        if isinstance(field, basestring):
            field = self.fields[field]
        name, relation = field.relations.copy().popitem()

        with SchemaLock(self.database) as file_lock:

            mandatory = True if relation.many_side_not_null else False
            fk_table = self.database[relation.foreign_key_table]
            pk_table = self.database[relation.primary_key_table]

            field.table.fields.pop(field.name)
            file_lock.export(uuid = True)

            for name, con in fk_table.foreign_key_constraints.iteritems():

                fk_const = migrate.changeset.constraint.ForeignKeyConstraint(con[0],
                                                   con[1], name = name, table = fk_table.sa_table)

                if name == relation.foreign_key_constraint_name:
                    fk_const.drop()
            file_lock.export()
            self.database.load_from_persist(True)


    def add_index(self, field, defer_update_sa = False):

        with SchemaLock(self.database) as file_lock:
            self._add_field_no_persist(field)
            file_lock.export(uuid = True)

            name, index = field.indexes.popitem()

            ind = [self.sa_table.columns[col.strip()] for col in index.fields.split(",")]
            if index.type == "unique":
                sa.Index(index.name, *ind, unique = True).create()
            else:
                sa.Index(index.name, *ind).create()

            file_lock.export()
            self.database.load_from_persist(True)

    def delete_index(self, field):

        if isinstance(field, basestring):
            field = self.fields[field]

        with SchemaLock(self.database) as file_lock:

            field.table.fields.pop(field.name)
            file_lock.export(uuid = True)

            for sa_index in self.sa_table.indexes:
                if sa_index.name == field.name:
                    sa_index.drop()

            file_lock.export()

            self.database.load_from_persist(True)

    def add_field(self, field, defer_update_sa = False):
        """add a Field object to this Table"""
        if self.persisted == True:

            with SchemaLock(self.database) as file_lock:
                self._add_field_no_persist(field)
                file_lock.export(uuid = True)
                self._add_field_by_alter_table(field)
                file_lock.export()
                self.database.load_from_persist(True)

        else:
            self._add_field_no_persist(field)

    def add_event(self, event):

        self.add_field(event)

    def rename_field(self, field, new_name):

        if self.database.engine.name == "sqlite":
            ##FIXME make better exception
            raise Exception("sqlite cannot alter fields")

        if isinstance(field, basestring):
            field = self.fields[field]

        with SchemaLock(self.database) as file_lock:

            field.name = new_name

            column = field.columns[field.column_order[0]] ##TODO make sure only 1 column in field
            file_lock.export(uuid = True)
            self.sa_table.c[column.name].alter(name = new_name)

            file_lock.export()
            self.database.load_from_persist(True)

    def drop_field(self, field):

        if self.database.engine.name == "sqlite":
            ##FIXME make better exception
            raise Exception("sqlite cannot alter fields")

        if isinstance(field, basestring):
            field = self.fields[field]

        with SchemaLock(self.database) as file_lock:

            self.fields.pop(field.name)
            file_lock.export(uuid = True)

            for column in field.columns.values():
                self.sa_table.c[column.name].drop()

            file_lock.export()
            self.database.load_from_persist(True)


    def alter_field(self, field, **kw):


        if isinstance(field, basestring):
            field = self.fields[field]

        if field.category <> "field":
            raise Exception(("only fields representing database"
                            "fields can be altered"))

        connection = self.database.db.open()

        with SchemaLock(self.database) as file_lock:

            field_type = kw.pop("type", None)

            field.kw.update(kw)

            if field_type:
                if isinstance(field_type, basestring):
                    field_type = getattr(fields, field_type)
                new_field = field_type(field.name, **field.kw)
            else:
                new_field = field.__class__(field.name, **field.kw)

            _, column = new_field.columns.copy().popitem()

            self.fields[field.name] = new_field

            file_lock.export(uuid = True)
            sa_options = column.sa_options

            col = self.sa_table.c[column.name]
            col.alter(sa.Column(column.name, column.type, **sa_options))
            file_lock.export()

            self.database.load_from_persist(True)

    def _add_field_no_persist(self, field):
        """add a Field object to this Table"""
        field._set_parent(self)

    def _add_field_by_alter_table(self, field):
        for name, column in field.columns.iteritems():
            col = sa.Column(name, column.type, **column.sa_options)
            col.create(self.sa_table)

    @property
    def ordered_fields(self):

        fields = []

        for field in self.field_order:
            rfield = self.fields[field]
            if rfield.category in ("internal", "multi_field", "field"):
                fields.append(rfield)
        return fields

    @property
    def ordered_user_fields(self):

        return filter(lambda f: f.category.endswith("field"),
                      self.ordered_fields)

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
    def indexes(self):
        """gathers all columns defined in this table"""
        columns = {}
        for field in self.fields.itervalues():
            for name, column in field.indexes.iteritems():
                columns[name] = column
        return columns

    @property
    def constraints(self):
        """gathers all columns defined in this table"""
        columns = {}
        for field in self.fields.itervalues():
            for name, column in field.constraints.iteritems():
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
        if self.columns_cache:
            return self.columns_cache
        columns = {}
        try:
            for field in self.fields.itervalues():
                for name, column in field.columns.iteritems():
                    if name in self.foriegn_key_columns:
                        continue
                    columns[name] = column
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
                ##special rename of backref
                backref = relation.sa_options.get("backref")
                if backref:
                    new_name = backref.replace("?", self.name)
                    relation.sa_options["backref"] = new_name



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
        if not self.table_id:
            new_id = database.max_table_id + 1
            self.table_id = new_id
            self.kw["table_id"] = new_id
            database.max_table_id = new_id
        else:
            database.max_table_id = max(database.max_table_id, self.table_id)

        database.tables[self.name]=self
        database.add_relations()
        self.database = database
        self.add_events()

    def add_events(self):

        for event in self.field_list:
            if hasattr(event, "_set_actions"):
                event._set_actions(self)

    @property
    def tables_with_relations(self):
        """returns a dictionary of all related tables and the relation object
        that was defined that related them"""
        self.check_database()
        return self.database.tables_with_relations(self)


    @property
    def relation_attributes(self):
        """returns all the attributes names and accociated relation object
        that appear on the sqlalchemy object"""
        relation_attributes = {}
        for relations in self.tables_with_relations.values():
            for relation in relations:
                if relation.table is self:
                    relation_attributes[relation.name] = relation
                else:
                    backref = relation.sa_options["backref"]
                    if backref:
                        relation_attributes[backref] = relation

        return relation_attributes

    @property
    def dependant_attributes(self):
        """attributes that would result in a null in the related table if
        object was removed"""

        dependant_attributes = {}
        for table, relations in self.tables_with_relations.iteritems():
            for relation in relations:
                if relation.table is self and relation.original_type not in ("manytoone", "onetoone"):
                    dependant_attributes[relation.name] = relation
                elif relation.table is not self and relation.original_type in ("manytoone", "onetoone"):
                    backref = relation.sa_options["backref"]
                    if backref:
                        dependant_attributes[backref] = relation
        return dependant_attributes

    @property
    def dependant_tables(self):
        dependant_tables = []

        for table, relations in self.tables_with_relations.iteritems():
            for relation in relations:
                if relation.table is self and relation.original_type not in ("manytoone", "onetoone"):
                    dependant_tables.append(table[0])
                elif relation.table is not self and relation.original_type in ("manytoone", "onetoone"):
                    dependant_tables.append(table[0])
        return dependant_tables

    @property
    def parent_attributes(self):

        parent_attributes = {}
        for table, relations in self.tables_with_relations.iteritems():
            for relation in relations:
                if relation.table is self and relation.original_type in ("manytoone", "onetoone"):
                    parent_attributes[relation.name] = relation
                elif relation.table is not self and relation.original_type not in ("manytoone", "onetoone"):
                    backref = relation.sa_options["backref"]
                    if backref:
                        parent_attributes[backref] = relation
        return parent_attributes

    @property
    def parent_columns_attributes(self):

        columns = {}
        for column_name, column in self.foriegn_key_columns.iteritems():
            if column.original_column <> "id":
                relation = column.defined_relation
                if relation.table is self and relation.original_type in ("manytoone", "onetoone"):
                    relation_attribute = relation.name
                else:
                    relation_attribute = relation.sa_options["backref"]

                if relation_attribute:
                    columns[column_name] = relation_attribute
        return columns



    @property
    def foriegn_key_columns(self):
        """gathers the extra columns in this table that are needed as the tables
        are related. i.e if this table is the many side of a one to many
        relationship it will return the primary key on the "one"
        side"""

        if self.foriegn_key_columns_current:
            return self.foriegn_key_columns_current

        self.check_database()
        database = self.database
        columns={}
        ##  could be made simpler
        for tab, relations in self.tables_with_relations.iteritems():
            table, pos = tab
            for rel in relations:
                if rel.foreign_key_table == self.name:
                    if database.tables[table].primary_key_columns:
                        rtable = database.tables[table]
                        for name, column in rtable.primary_key_columns.items():
                            new_col = Column(column.type,
                                             name=name,
                                             mandatory = rel.many_side_not_null,
                                             defined_relation = rel,
                                             original_column = name)
                            columns[name] = new_col

                    if rel.foreign_key_name and rel.foreign_key_name not in self.defined_columns:
                        columns[rel.foreign_key_name] = Column(sa.Integer,
                                                       name = rel.foreign_key_name,
                                                       mandatory = rel.many_side_not_null,
                                                       defined_relation= rel,
                                                       original_column= "id")
                    elif rel.foreign_key_name:
                        column = self.defined_columns[rel.foreign_key_name]
                        column.defined_relation = rel
                        column.original_column = "id"
                        columns[rel.foreign_key_name] = column

                    elif table+"_id" not in columns:
                        columns[table +'_id'] = Column(sa.Integer,
                                                       name = table +'_id',
                                                       mandatory = rel.many_side_not_null,
                                                       defined_relation= rel,
                                                       original_column= "id")
                        rel.foreign_key_name = rel.foreign_key_name or table + '_id'
                    else:
                        columns[table +'_id2'] = Column(sa.Integer,
                                                       name = table +'_id2',
                                                       mandatory = rel.many_side_not_null,
                                                       defined_relation= rel,
                                                       original_column= "id")
                        rel.foreign_key_name = rel.foreign_key_name or table + '_id2'

        self.foriegn_key_columns_current = columns

        return columns

    @property
    def foreign_key_constraints(self):

        """gathers a dictionary of all the foreign key columns for use in defining
        foreign key constraints in createing sqlalchemy tables"""

        fk_constraints = {}
        self.check_database()
        ##  could be made simpler
        for tab, relations in self.tables_with_relations.iteritems():
            table, pos = tab
            ## not allowed self joining constraints
            if table == self.name:
                continue
            for rel in relations:
                other_table_columns=[]
                this_table_columns=[]
                for name, column in self.foriegn_key_columns.iteritems():
                    if column.defined_relation == rel and column.original_column == "id":
                        other_table_columns.append("%s.%s"%\
                                                   (table, column.original_column))
                        this_table_columns.append(name)
                if other_table_columns:
                    fk_constraints[rel.foreign_key_constraint_name] = [this_table_columns,
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

        if self.database.engine.name == 'postgres':
            statement = text("coalesce((select max(id) from (select * from public.%s) inner_table),0) + 1" % self.name)
            sa_table.append_column(sa.Column("id", sa.Integer, primary_key = True, server_default = statement))
        else:
            sa_table.append_column(sa.Column("id", sa.Integer, primary_key = True))

        for name, column in self.foriegn_key_columns.iteritems():
            sa_options = column.sa_options
            sa_table.append_column(sa.Column(name, column.type, **sa_options))
        defined_columns = self.defined_columns
        for column in self.defined_columns_order:
            if column in self.foriegn_key_columns:
                continue
            name = column
            column = defined_columns[column]
            sa_options = column.sa_options

            sa_table.append_column(sa.Column(name, column.type, **sa_options))

        if self.foreign_key_constraints:
            for name, con in self.foreign_key_constraints.iteritems():
                fk_const = sa.ForeignKeyConstraint(con[0], con[1], name = name)
                sa_table.append_constraint(fk_const)

        for name, index in self.indexes.iteritems():
            ind = [sa_table.columns[col.strip()] for col in index.fields.split(",")]
            if index.type == "unique":
                sa.Index(name, *ind, unique = True)
            else:
                sa.Index(name, *ind)

        for name, constr in self.constraints.iteritems():
            con = [col.strip() for col in constr.fields.split(",")]
            sa_table.append_constraint(sa.UniqueConstraint(*con, name = name))

        self.sa_table = sa_table

    def make_sa_class(self):
        """makes a class to be mapped and stores it in the attribute sa_class"""
        #make sure class is not already made
        if self.sa_class:
            return
        table = self
        class SaClass(object):
            def __init__(self):
                self._table = table
                self._validated = False
                self._version_changed = False
                self._new = True

            @sa.orm.reconstructor
            def init_onload(self):
                self._table = table
                self._validated = True
                self._version_changed = False
                self._new = False

            def __repr__(self):

                return "_table: %s, id: %s, %s" % (self._table.name, self.id, ", ".join(["%s: %s" %
                                         (field, getattr(self, field)) for
                                          field in self._table.columns])
                                         )


        SaClass.__name__ = self.name.encode("ascii")
        self.sa_class = SaClass

    def sa_mapper(self):
        """runs sqlalchemy mapper to map the sa_table to sa_class and stores
        the mapper object in the 'mapper' attribute"""
        #make sure mapping has not been done
        if self.mapper:
            return

        properties ={}
        for col_name, column in self.columns.iteritems():
            if column.name == "_version":
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = VersionChange())
            elif column.parent and column.parent.type == "Password":
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ConvertPassword())
            elif column.type == sa.DateTime:
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ConvertDate())
            ##FIXME do we want to keep this as date?
            elif column.type == sa.Date:
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ConvertDate())
            elif column.type == sa.Boolean:
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ConvertBoolean())
            elif column.type == sa.Integer:
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ConvertInteger())
            elif column.type == sa.Unicode or isinstance(column.type, sa.Unicode):
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ConvertUnicode())
            else:
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ChangedAttributes())

        for relation in self.relations.itervalues():
            sa_options = relation.sa_options
            other_rtable = self.database.tables[relation.other]
            other_table = other_rtable.sa_table
            other_class = self.database.tables[relation.other].sa_class
            if "backref" not in sa_options:
                sa_options["backref"] = "_%s"% self.name
            if sa_options["backref"]:
                new_backref = sa_options["backref"].replace("?", self.name)
                sa_options["backref"] = new_backref

            ##copy as if update_sa is run will try to add backref
            sa_options = sa_options.copy()
            if relation.original_type == "onetoone":
                backref_string = sa_options["backref"]
                if backref_string:
                    sa_options["backref"] = backref(backref_string, uselist = False)


            if sa_options["backref"] is False:
                sa_options.pop("backref")

            joined_columns = []
            foriegn_key_columns = []


            for name, column in self.foriegn_key_columns.iteritems():
                if relation == column.defined_relation and column.original_column == "id":
                    joined_columns.append([name, column.original_column])
                    foriegn_key_columns.append(getattr(self.sa_table.c, name))
            if not joined_columns:
                for name, col in other_rtable.foriegn_key_columns.iteritems():
                    if relation == col.defined_relation and col.original_column == "id":
                        joined_columns.append([col.original_column, name])
                        foriegn_key_columns.append(getattr(other_table.c, name))

            join_conditions = []
            for col1, col2 in joined_columns:
                join_conditions.append(getattr(self.sa_table.c, col1) ==\
                                       getattr(other_table.c, col2))

            sa_options["primaryjoin"] = sa.sql.and_(*join_conditions)
            sa_options["foreign_keys"] = foriegn_key_columns
            sa_options["cascade"] = "none"

            properties[relation.name] = sa.orm.relation(other_class,
                                                    **sa_options)

        mapper_kw = dict(properties = properties)
        if self.version:
            mapper_kw["version_id_col"] = self.sa_table.c._version


        self.mapper = mapper(self.sa_class,
                             self.sa_table,
                             **mapper_kw)

    def make_paths(self):

        if not self.paths:
            self.paths = get_paths(self.database.graph, self.name)

        if not self.local_tables:
            local_tables, one_to_many_tables = make_local_tables(self.paths)
            self.local_tables = local_tables
            self.one_to_many_tables = one_to_many_tables

            self.table_path_list = create_table_path_list(self.paths)
            self.table_path = create_table_path(self.table_path_list, self.name)


    def get_edge(self, table_name):

        if ">" in table_name:
            path = tuple(table_name.split(">")[:-1])
            return self.paths[path]

        return self.table_path[table_name]

    def get_path(self, table_name):

        return self.get_edge(table_name).path

    def get_table_from_field(self, field_name):

        return ".".join(field_name.split(".")[:-1])

    def get_edge_from_field(self, field_name):

        if field_name.count("."):
            table = self.get_table_from_field(field_name)
            return self.get_edge(table)

    def get_path_from_field(self, field_name):

        return self.get_edge_from_field(field_name).path


    def validation_from_field_types(self, column):
        formencode_all = All()
        validators = formencode_all.validators
        col_type = column.type
        mand = not column.sa_options.get("nullable", True)
        if column.defined_relation:
            mand = False

        val = formencode.validators
        if column.validate == False:
            pass
        elif col_type is sa.Unicode or isinstance(col_type, sa.Unicode):
            if hasattr(col_type, 'length'):
                if col_type.length:
                    max = col_type.length
                else:
                    max = 100
            else:
                max = 100
            not_empty_string = column.mandatory
            validators.append(UnicodeString(max = max,
                                            not_empty = mand,
                                            not_empty_string = not_empty_string))
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

    def make_schema_dict(self):

        schema_dict = {}
        chained_validators = []

        # gets from column definition
        for column in self.columns.itervalues():
            schema_dict[column.name] = self.validation_from_field_types(column)
            if column.validation:
                if column.validation.startswith("__"):
                    validator = validators.Regex(column.validation[2:])
                else:
                    validator = getattr(validators, column.validation)()
                schema_dict[column.name].validators.append(validator)

        # gets from field definition
        for field in self.fields.itervalues():
            if hasattr(field, "validation"):
                for name, validation in field.validation.iteritems():
                    schema_dict[name].validators.append(validation)
            # chained validaors
            if hasattr(field, "chained_validator"):
                if isinstance(field.chained_validator, list):
                    chained_validators.extend(field.chained_validator)
                else:
                    chained_validators.append(field.chained_validator)

        # Non nullable foriegn keys are validated on the
        # relationship attribute for relationships with attributes
        for column in self.foriegn_key_columns.itervalues():
            mand = not column.sa_options.get("nullable", True)
            relation = column.defined_relation
            table = relation.table
            if relation and mand and not table.name.startswith("_core_"):
                if relation.table is self:
                    attribute = relation.name
                else:
                    attribute = relation.sa_options["backref"]


                if attribute:
                    validator = validators.FancyValidator()
                    chained_validators.append(RequireIfMissing(column.name, missing = attribute))
                    schema_dict[attribute] = validator
                else:
                    validation = validators.FancyValidator(not_empty = True)
                    schema_dict[column.name].validators.append(validation)


        # many side mandatory validators
        for tab, relations in self.tables_with_relations.iteritems():
            for rel in relations:
                if not rel.many_side_mandatory:
                    continue
                table, pos = tab
                if rel.original_type in ("onetomany", "onetooneother") and pos == "here":
                    schema_dict[rel.name] = validators.FancyValidator(not_empty = True)
                if rel.original_type in ("manytoone", "onetoone")  and pos == "other":
                    backref = rel.sa_options["backref"]
                    if backref:
                        validator = validators.FancyValidator(not_empty = True)
                        schema_dict[backref] = validator

        if chained_validators:
            schema_dict["chained_validators"] = chained_validators


        self.schema_dict = schema_dict

    @property
    def schema_info(self):

        schema = {}

        for key, value in self.schema_dict.iteritems():
            if key == "chained_validators":
                continue
            if not isinstance(value, All):
                continue
            all_info = []


            for validator in value.validators:
                validator_info = {}

                validator_info["type"] = validator.__class__.__name__

                for name, attrib in validator.__dict__.iteritems():
                    if name in ('declarative_count', 'inputEncoding', 'outputEncoding'):
                        continue
                    if name.startswith("_"):
                        continue
                    validator_info[name] = attrib

                all_info.append(validator_info)

            schema[key] = all_info

        return schema


    @property
    def validation_schema(self):
        """Gathers all the validation dictionarys from all the Field Objects
        and a makes a formencode Schema out of them"""
        if self.schema:
            return self.schema
        self.schema = formencode.Schema(allow_extra_fields = True,
                                 ignore_key_missing = True,
                                 **self.schema_dict)

        return self.schema

    def validate(self, instance, session):
        """this validates an instance of sa_class with the schema defined
        by this tables Field objects"""

        validation_dict = {}
        for name in self.schema_dict.iterkeys():
            if name == "chained_validators":
                continue
            validation_dict[name] = getattr(instance, name)
        instance._session = session

        if not self.validated:
            return {}

        return self.validation_schema.to_python(validation_dict, instance)



class ChangedAttributes(AttributeExtension):

    def set(self, state, value, oldvalue, initator):

        if value != oldvalue:
            state.dict["_validated"] = False

        return value

class VersionChange(AttributeExtension):

    def set(self, state, value, oldvalue, initator):


        state.dict["_version_changed"] = True

        if isinstance(value, int):
            return value
        if value:
            return int(value)

        return value

class ConvertUnicode(AttributeExtension):

    def set(self, state, value, oldvalue, initator):

        if value == oldvalue:
            return value

        state.dict["_validated"] = False

        if value is None:
            return None

        if isinstance(value, ClauseElement):
            return value

        return value.decode("utf-8")


class ConvertDate(AttributeExtension):

    def set(self, state, value, oldvalue, initator):

        if value == oldvalue:
            return value
        state.dict["_validated"] = False
        if not value:
            return None

        if isinstance(value, ClauseElement):
            return value

        if isinstance(value, datetime.datetime):
            return value

        # handle dates with and without microseconds
        # currently Javascript likes to keep the milliseconds
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')

class ConvertBoolean(AttributeExtension):

    def set(self, state, value, oldvalue, initator):

        if value == oldvalue or not value:
            return value
        state.dict["_validated"] = False

        if isinstance(value, bool):
            return value

        if value.lower() in ("false", "0"):
            return False
        elif value.lower() in ("true", "1"):
            return True
        else:
            raise AttributeError("field needs to be a boolean")


class ConvertInteger(AttributeExtension):

    def set(self, state, value, oldvalue, initator):

        if value == oldvalue:
            return value
        state.dict["_validated"] = False
        if not value:
            return None

        if isinstance(value, ClauseElement):
            return value

        try:
            return int(value)
        except ValueError:
            return value

class ConvertPassword(AttributeExtension):

    def set(self, state, value, oldvalue, initator):

        if value == oldvalue:
            return value
        if not value:
            return None
        state.dict["_validated"] = False

        if state.dict.get("_from_load"):
            return value

        return fshp.crypt(value).decode("utf-8")
