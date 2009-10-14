import formencode
from formencode.validators import *
_ = lambda s: s

class CheckNoOverlappingDates(FormValidator):

    min_date = "start_date"
    max_date = "end_date"
    __unpackargs__ = ('many_to_one_table',)

    messages = {
        'invalid': _("%s and %s overlap" % (min_date, max_date)),
        }

    def validate_python(self, field_dict, obj):

        table = obj._table

        relation_path = table.local_tables[self.many_to_one_table]

        parent_obj = obj
        for relation in relation_path:
            parent_obj = getattr(parent_obj, relation)

        parent_obj_table = parent_obj._table
        ## should get alias name not table name
        relation_back_path = parent_obj_table.one_to_many_tables[table.name]

        collection = parent_obj

        for relation in relation_back_path:
            collection = getattr(collection, relation)

        if not collection:
            return

        for num, obj in enumerate(collection):
            for num2, obj2 in enumerate(collection):
                if num >= num2:
                    continue
                if getattr(obj, self.min_date) <= getattr(obj2, self.max_date) and\
                   getattr(obj, self.max_date) >= getattr(obj2, self.min_date):
                    raise Invalid(self.message("invalid", obj), field_dict, obj)

class CheckNoTwoNulls(FormValidator):

    __unpackargs__ = ('many_to_one_table', 'field')

    messages = {
        'invalid': _("field has two nulls"),
        }

    def validate_python(self, field_dict, obj):

        table = obj._table

        relation_path = table.local_tables[self.many_to_one_table]

        parent_obj = obj
        for relation in relation_path:
            parent_obj = getattr(parent_obj, relation)

        parent_obj_table = parent_obj._table
        ## should get alias name not table name
        relation_back_path = parent_obj_table.one_to_many_tables[table.name]

        collection = parent_obj

        for relation in relation_back_path:
            collection = getattr(collection, relation)

        if not collection:
            return

        nulls = 0
        for obj in collection:
            if getattr(obj, self.field) is None:
                nulls = nulls +1
            if nulls == 2:
                raise Invalid(self.message("invalid", obj), field_dict, obj)


class CheckDefaultEmail(FormValidator):

    __unpackargs__ = ('many_to_one_table', 'field')

    messages = {
        'invalid': _("field has two nulls"),
        }

    def validate_python(self, field_dict, obj):

        table = obj._table

        relation_path = table.local_tables[self.many_to_one_table]

        parent_obj = obj
        for relation in relation_path:
            parent_obj = getattr(parent_obj, relation)

        parent_obj_table = parent_obj._table
        ## should get alias name not table name
        relation_back_path = parent_obj_table.one_to_many_tables[table.name]

        collection = parent_obj

        for relation in relation_back_path:
            collection = getattr(collection, relation)

        if not collection:
            return

        trues = 0
        for obj in collection:
            if getattr(obj, self.field) is True:
                trues = trues +1
        if trues <> 1:
            raise Invalid(self.message("invalid", obj), field_dict, obj)

class CheckInField(FancyValidator):

    __unpackargs__ = ('target',)

    filter_field = None

    filter_value = None

    messages = {
        'invalid': _("field %(field)s can not have value %(value)s"),
        }

    def validate_python(self, value, obj):


        session = obj._session
        database = obj._table.database
        self.table, self.field = self.target.split(".")

        target_class = database.tables[self.table].sa_class
        target_field = getattr(target_class, self.field)
        if self.filter_field:
            filter_field = getattr(target_class, self.filter_field)
            results = session.query(target_field).filter(filter_field == u"%s" % self.filter_value).all()
        else:
            results = session.query(getattr(target_class, self.field)).all()

        if value and (value,) not in results:
            raise Invalid(self.message("invalid", obj, field = self.field, value = value), value, obj)




