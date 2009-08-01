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
