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
from sqlalchemy.sql.expression import ClauseElement
from columns import Column
from custom_exceptions import NoMetadataError, NoDatabaseError
import formencode
from formencode import validators
from validators import All, UnicodeString
from fields import Modified, ModifiedBySession, Integer
import fields
from util import get_paths, make_local_tables, create_table_path_list, create_table_path
import logging
import migrate.changeset
import datetime
from search import Search
from sqlalchemy.orm import column_property
from sqlalchemy.orm.interfaces import AttributeExtension

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
        self.current_order = 0
        self.primary_key = kw.get("primary_key", None)
        #persisted should be private
        self.persisted = kw.get("persisted", False)

        # table types
        self.entity = kw.get("entity", False)
        self.relationship = kw.get("relationship", False)
        self.lookup = kw.get("lookup", False)

        valid_entities = kw.get("valid_entities", "").strip().split(",")
        self.valid_entities = [] if valid_entities == [""] else valid_entities

        valid_entities1 = kw.get("valid_entities1", "").strip().split(",")
        self.valid_entities1 = [] if valid_entities1 == [""] else valid_entities1

        valid_entities2 = kw.get("valid_entities2", "").strip().split(",")
        self.valid_entities2 = [] if valid_entities2 == [""] else valid_entities2


        self.logged = kw.get("logged", True)
        self.validated = kw.get("validated", True)
        self.modified_date = kw.get("modified_date", True)
        self.unique_constraint = kw.get("unique_constraint", None)
        self.table_type = kw.get("table_type", "user")
        self.entity_relationship = kw.get("entity_relationship", False)
        self.title_field = kw.get("title_field", None)
        self.summary_fields = kw.get("summary_fields", None)
        self.summary = kw.get("summary", None)
        self.primary_key_list = []
        self.events = []
        self.initial_events = []
        if self.primary_key:
            self.primary_key_list = self.primary_key.split(",")
        self.unique_constraint_list  = []
        if self.unique_constraint:
            self.unique_constraint_list = [column_list.split(",")
                                           for column_list in
                                           self.unique_constraint.split(";")]

        for field in args:
            field._set_parent(self)

        if "_modified_date" not in self.fields.iterkeys() and self.modified_date:
            self.add_field(Integer("_version"))
            self.add_field(Modified("_modified_date"))
            self.add_field(ModifiedBySession("_modified_by" ))

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

    def __repr__(self):
        return "%s - %s" % (self.name, self.columns.keys())

    def persist(self, session):
        """This puts the information about the this objects parameters
        and its collection of fields into private database tables so that in future they
        no longer need to be explicitely defined"""

        for field_name in self.field_order:
            field = self.fields[field_name]
            if field.category in ("field", "multi_field", "internal"):
                self.current_order = self.current_order + 1
                field.order = self.current_order


        __table = self.database.tables["__table"].sa_class()
        __table.table_name = u"%s" % self.name
        __table.summary = self.summary
        session.add(__table)


        for name, param in self.kw.iteritems():
            __table_param = self.database.get_instance("__table_params")
            __table_param.item = u"%s" % name
            __table_param.value = u"%s" % str(param)
            __table.table_params.append(__table_param)
            session.add(__table_param)

        for field_name, field  in self.fields.iteritems():
            __field = self.database.tables["__field"].sa_class()
            __field.field_name = u"%s" % field_name
            __field.type = u"%s" % field.__class__.__name__
            if hasattr(field, "other"):
                __field.other = u"%s" % field.other
            if field.foreign_key_name:
                __field.foreign_key_name = u"%s" % field.foreign_key_name
            if field.order:
                __field.order = field.order
            __table.field.append(__field)
            session.add(__field)

            for name, param in field.kw.iteritems():
                __field_param = self.database.get_instance("__field_params")
                __field_param.item = u"%s" % name
                __field_param.value = u"%s" % str(param)
                __field.field_params.append(__field_param)
                session.add(__field_param)

        session._flush()
        self.table_id = __table.id

        for field in __table.field:
            self.fields[field.field_name].field_id = field.id

        self.persisted = True

    def add_foriegn_key_field(self):
        for column in self.foriegn_key_columns.values():
            original_col = column.original_column
            name = column.name
            if original_col == "id" and name not in self.defined_columns:
                relation = column.defined_relation
                field = relation.parent
                field.foreign_key_name = unicode(name)
                new_field = Integer(name, mandatory = field.many_side_not_null)
                self.add_field(new_field)
                if field.name in self.field_order:
                    self.field_order.pop()
                    pos = self.field_order.index(field.name)
                    self.field_order.insert(pos, name)


    def persist_foreign_key_columns(self, session):

        for column in self.foriegn_key_columns.values():
            original_col = column.original_column
            name = column.name
            if original_col == "id" and name not in self.defined_columns:
                relation = column.defined_relation
                field = relation.parent
                new_field = Integer(name, mandatory = field.many_side_not_null)

                self._add_field_no_persist(new_field)
                self._persist_extra_field(new_field, session)

                row = field.get_field_row_from_table(session)
                row.foreign_key_name = unicode(name)
                session.save(row)

    def add_relation(self, field, defer_update_sa = False):

        if not self.persisted:
            self._add_field_no_persist(field)
            return

        session = self.database.Session()
        try:
            self._add_field_no_persist(field)
            self._persist_extra_field(field, session)
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
                    session._flush()
                    fk_table.persist_foreign_key_columns(session)
                    col.create(fk_table.sa_table)

            for name, con in fk_table.foreign_key_constraints.iteritems():

                if self.database.engine.name == 'sqlite':
                    break

                fk_const = migrate.changeset.constraint.ForeignKeyConstraint(con[0],
                                                   con[1], name = name, table = fk_table.sa_table)

                if name == relation.foreign_key_constraint_name:
                    fk_const.create()


        except Exception, e:
            session.rollback()
            if field in self.fields:
                self.fields.pop(field.name)
            raise
        else:
            session._commit()
            if not defer_update_sa:
                self.database.load_from_persist(True)
        finally:
            session.close()
        return

    def delete_relation(self, field):

        if isinstance(field, basestring):
            field = self.fields[field]
        name, relation = field.relations.copy().popitem()

        session = self.database.Session()

        try:
            mandatory = True if relation.many_side_not_null else False
            fk_table = self.database[relation.foreign_key_table]
            pk_table = self.database[relation.primary_key_table]

            row = field.get_field_row_from_table(session)
            session.delete(row)

            session._flush()

            for name, con in fk_table.foreign_key_constraints.iteritems():

                #fk_const = sa.ForeignKeyConstraint([fk_table.sa_table.c[con[0][0]]],
                #                                   [pk_table.sa_table.c[con[1][0]]], name = name)

                fk_const = migrate.changeset.constraint.ForeignKeyConstraint(con[0],
                                                   con[1], name = name, table = fk_table.sa_table)

                if name == relation.foreign_key_constraint_name:
                    fk_const.drop()

            #for constraint in fk_table.sa_table.constraints:
            #    if constraint.name == relation.foreign_key_constraint_name:
            #        constraint.drop()

        except Exception, e:
            session.rollback()
            raise
        else:
            session._commit()
            self.database.load_from_persist(True)
        finally:
            session.close()

    def add_index(self, field, defer_update_sa = False):

        session = self.database.Session()
        try:
            self._add_field_no_persist(field)
            self._persist_extra_field(field, session)

            name, index = field.indexes.popitem()

            ind = [self.sa_table.columns[col.strip()] for col in index.fields.split(",")]
            if index.type == "unique":
                sa.Index(index.name, *ind, unique = True).create()
            else:
                sa.Index(index.name, *ind).create()

        except Exception, e:
            session.rollback()
            raise
        else:
            session._commit()
            self.database.load_from_persist(True)
        finally:
            session.close()

    def delete_index(self, index):

        if isinstance(index, basestring):
            field = self.fields[index]

        session = self.database.Session()
        try:
            row = field.get_field_row_from_table(session)
            session.delete(row)
            for sa_index in self.sa_table.indexes:
                if sa_index.name == field.name:
                    sa_index.drop()


        except Exception, e:
            session.rollback()
            raise
        else:
            session._commit()
            self.database.load_from_persist(True)
        finally:
            session.close()


    def add_field(self, field, defer_update_sa = False):
        """add a Field object to this Table"""
        if self.persisted == True:
            session = self.database.Session()
            field.check_table(self)
            try:
                self._add_field_no_persist(field)
                self._persist_extra_field(field, session)
                self._add_field_by_alter_table(field)
            except Exception, e:
                session.rollback()
                if field in self.fields:
                    self.fields.pop(field.name)
                raise
            else:
                session._commit()
                if not defer_update_sa:
                    self.database.update_sa(reload = True)
            finally:
                session.close()
            return

        else:
            self._add_field_no_persist(field)

    def rename_field(self, field, new_name):

        if self.database.engine.name == "sqlite":
            ##FIXME make better exception
            raise Exception("sqlite cannot alter fields")

        if isinstance(field, basestring):
            field = self.fields[field]

        session = self.database.Session()

        try:
            column = field.columns[field.column_order[0]] ##TODO make sure only 1 column in field
            row = field.get_field_row_from_table(session)
            row.field_name = u"%s" % new_name
            session.save(row)

            self.sa_table.c[column.name].alter(name = new_name)

            session._flush()

        except Exception, e:
            session.rollback()
            raise
        else:
            session._commit()
            self.database.load_from_persist(True)
        finally:
            session.close()

    def drop_field(self, field):

        if self.database.engine.name == "sqlite":
            ##FIXME make better exception
            raise Exception("sqlite cannot alter fields")

        if isinstance(field, basestring):
            field = self.fields[field]

        session = self.database.Session()

        try:
            row = field.get_field_row_from_table(session)
            session.delete(row)
            session._flush()

            query = Search(self.database,
                           "__field",
                           session,
                           "table_name = ? and order is ?",
                           values = [self.name, "not null"]).search()

            query.order_by(self.database["__field"].sa_class.order)


            for num, obj in enumerate(query.all()):
                obj.order = num + 1
                session.save(obj)


            session._flush()


            for column in field.columns.values():
                self.sa_table.c[column.name].drop()

        except Exception, e:
            session.rollback()
            raise
        else:
            session._commit()
            self.database.load_from_persist(True)
        finally:
            session.close()

    def alter_field(self, field, **kw):


        if isinstance(field, basestring):
            field = self.fields[field]

        if field.category <> "field":
            raise Exception(("only fields representing database"
                            "fields can be altered"))

        session = self.database.Session()

        try:
            field_type = kw.pop("type", None)

            row = field.get_field_row_from_table(session)

            new_kw = field.kw.copy()
            new_kw.update(kw)
            new_kw["order"] = field.order


            if field_type:
                if isinstance(field_type, basestring):
                    field_type = getattr(fields, field_type)
                new_field = field_type(field.name, **new_kw)
            else:
                new_field = field.__class__(field.name, **new_kw)

            _, column = new_field.columns.copy().popitem()

            sa_options = column.sa_options

            # sqlalchemy only accepts strings for server_defaults
            #if isinstance(column.type, sa.Unicode) and "default" in sa_options:
            #    if isinstance(sa_options["default"], basestring):
            #        default = sa_options.pop("default")
            #        sa_options["server_default"] = default


            for param in row.field_params:
                session.delete(param)

            for name, param in new_field.kw.iteritems():
                __field_param = self.database.get_instance("__field_params")
                __field_param.item = u"%s" % name
                __field_param.value = u"%s" % str(param)
                row.field_params.append(__field_param)
                session.add(__field_param)
            row.type = unicode(new_field.__class__.__name__)
            session.add(row)

            session._flush()

            col = self.sa_table.c[column.name]
            col.alter(sa.Column(column.name, column.type, **sa_options))

        except Exception, e:
            session.rollback()
            raise
        else:
            session._commit()
            self.database.load_from_persist(True)
        finally:
            session.close()







    def _add_field_no_persist(self, field):
        """add a Field object to this Table"""
        field._set_parent(self)

    def _add_field_by_alter_table(self, field):
        for name, column in field.columns.iteritems():
            col = sa.Column(name, column.type, **column.sa_options)
            col.create(self.sa_table)

    def _persist_extra_field(self, field, session):

        if field.category in ("field", "multi_field", "internal"):
            self.current_order = self.current_order + 1
            field.order = self.current_order

        __table = session.query(self.database.get_class("__table")).\
                                filter_by(table_name = u"%s" % self.name).one()

        __field = self.database.tables["__field"].sa_class()
        __field.field_name = u"%s" % field.name
        __field.type = u"%s" % field.__class__.__name__
        if hasattr(field, "other"):
            __field.other = u"%s" % field.other

        if field.foreign_key_name:
            __field.foreign_key_name = field.foreign_key_name

        if field.order:
            __field.order = field.order

        for name, param in field.kw.iteritems():
            __field_param = self.database.tables["__field_params"].sa_class()
            __field_param.item = u"%s" % name
            __field_param.value = u"%s" % str(param)
            __field.field_params.append(__field_param)
            session.add(__field_param)

        __table.field.append(__field)
        session.add(__field)

        session.add(__table)

        session._flush()

        for field in __table.field:
            self.fields[field.field_name].field_id = field.id

        return __field

    def get_table_row_from_table(self, session):

        sa_class = self.database["__table"].sa_class
        query = session.query(sa_class)
        result = query.filter(sa_class.id == self.table_id).one()
        return result

    @property
    def ordered_fields(self):

        fields = []

        for field in self.fields.values():
            if field.category in ("internal", "multi_field", "field"):
                fields.append(field)

        def sort_order(a, b):
            first = a.order or -1
            second = b.order or -1
            return first - second

        fields.sort(sort_order)

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
    def relation_attributes(self):
        """returns all the attributes names and accociated relation object
        that appear on the sqlalchemy object"""
        relation_attributes = {}
        for relations in self.tables_with_relations.values():
            for relation in relations:
                if relation.table is self:
                    relation_attributes[relation.name] = relation
                else:
                    relation_attributes[relation.sa_options["backref"]] = relation
        return relation_attributes

    @property
    def dependant_attributes(self):
        """attributes that would result in a null in the related table if
        object was removed"""

        dependant_attributes = {}
        for table, relations in self.tables_with_relations.iteritems():
            for relation in relations:
                if relation.table is self and relation.type <> "manytoone":
                    dependant_attributes[relation.name] = relation
                elif relation.table is not self and relation.type == "manytoone":
                    dependant_attributes[relation.sa_options["backref"]] = relation
        return dependant_attributes

    @property
    def dependant_tables(self):
        dependant_tables = []

        for table, relations in self.tables_with_relations.iteritems():
            for relation in relations:
                if relation.table is self and relation.type <> "manytoone":
                    dependant_tables.append(table[0])
                elif relation.table is not self and relation.type == "manytoone":
                    dependant_tables.append(table[0])
        return dependant_tables

    @property
    def parent_attributes(self):

        parent_attributes = {}
        for table, relations in self.tables_with_relations.iteritems():
            for relation in relations:
                if relation.table is self and relation.type == "manytoone":
                    parent_attributes[relation.name] = relation
                elif relation.table is not self and relation.type <> "manytoone":
                    parent_attributes[relation.sa_options["backref"]] = relation
        return parent_attributes

    @property
    def parent_columns_attributes(self):

        columns = {}
        for column_name, column in self.foriegn_key_columns.iteritems():
            if column.original_column <> "id":
                relation = column.defined_relation
                if relation.table is self and relation.type == "manytoone":
                    relation_attribute = relation.name
                else:
                    relation_attribute = relation.sa_options["backref"]

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

            ## sqlalchemy only accepts strings for server_defaults
            #if isinstance(column.type, sa.Unicode) and "default" in sa_options:
            #    if isinstance(sa_options["default"], basestring):
            #        default = sa_options.pop("default")
            #        sa_options["server_default"] = default

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

            @sa.orm.reconstructor
            def init_onload(self):
                self._table = table
                self._validated = False
                self._version_changed = False

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
            elif column.type == sa.DateTime:
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ConvertDate())
            elif column.type == sa.Boolean:
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ConvertBoolean())
            else:
                properties[col_name] = column_property(getattr(self.sa_table.c,col_name),
                                                         extension = ChangedAttributes())

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
                if relation == column.defined_relation and column.original_column == "id":
                    joined_columns.append([name, column.original_column])
            if not joined_columns:
                for name, col in other_rtable.foriegn_key_columns.iteritems():
                    if relation == col.defined_relation and col.original_column == "id":
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
                             properties = properties,
                             version_id_col = self.sa_table.c._version)

    def make_paths(self):

        if not self.paths:
            self.paths = get_paths(self.database.graph, self.name)

        if not self.local_tables:
            local_tables, one_to_many_tables = make_local_tables(self.paths)
            self.local_tables = local_tables
            self.one_to_many_tables = one_to_many_tables

            self.table_path_list = create_table_path_list(self.paths)
            self.table_path = create_table_path(self.table_path_list, self.name)

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
        # relationship attribute
        for column in self.foriegn_key_columns.itervalues():
            mand = not column.sa_options.get("nullable", True)
            relation = column.defined_relation
            table = relation.table
            if relation and mand and not table.name.startswith("_core_"):
                if relation.table is self:
                    attribute = relation.name
                else:
                    attribute = relation.sa_options["backref"].encode("ascii")

                validator = validators.FancyValidator()
                chained_validators.append(validators.RequireIfMissing(column.name, missing = attribute))

                schema_dict[attribute] = validator

        # many side mandatory validators
        for tab, relations in self.tables_with_relations.iteritems():
            for rel in relations:
                if not rel.many_side_mandatory:
                    continue
                table, pos = tab
                if rel.type in ("onetomany", "onetone") and pos == "here":
                    schema_dict[rel.name] = validators.FancyValidator(not_empty = True)
                if rel.type == "manytoone" and pos == "other":
                    schema_dict[rel.sa_options["backref"]] = validators.FancyValidator(not_empty = True)

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

        return formencode.Schema(allow_extra_fields = True,
                                 ignore_key_missing = True,
                                 **self.schema_dict)

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


    def logged_instance(self, instance):
        """this creates a copy of an instace of sa_class"""

        ##not used as sessionwrapper now does this
        logged_instance = self.database.tables["_log_" + self.name].sa_class()
        for name in self.columns.iterkeys():
            setattr(logged_instance, name, getattr(instance, name))
        setattr(logged_instance, self.name + "_logged", instance)
        return logged_instance

    def update_all_initial_events(self):

        session = self.database.Session()
        for field in self.fields.itervalues():
            try:
                event = field.event
            except AttributeError:
                continue
            if event.initial_event:
                try:
                    event.update_all(session)
                except AttributeError:
                    continue
        session.commit()
        session.close()

    def update_all_events(self):

        session = self.database.Session()
        for field in self.fields.itervalues():
            try:
                event = field.event
            except AttributeError:
                continue
            if not event.initial_event:
                event.update_all(session)
        session.commit()
        session.close()



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


class ConvertDate(AttributeExtension):

    def set(self, state, value, oldvalue, initator):

        if value == oldvalue:
            return value
        if not value:
            return None
        state.dict["_validated"] = False

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




