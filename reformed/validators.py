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




class All(formencode.compound.CompoundValidator):

    """
    This class is a copy of formencodes All validator but makes a new exception
    with a list of errors (in the error_list property) instead of just raising the
    first found error."""

    def __repr__(self):
        return '<All %s>' % self.validators

    def attempt_convert(self, value, state, validate):

        validators = self.validators

        error_list = []

        for validator in validators:
            try:
                validate(validator, value, state)
            except Invalid, e:
                error_list.append(e)

        if error_list:
            invalid = Invalid("\n".join([error.msg for error in error_list]), value, state)
            invalid.error_list = error_list
            raise invalid

        return value


    def with_validator(self, validator):
        """
        Adds the validator (or list of validators) to a copy of
        this validator.
        """
        new = self.validators[:]
        if isinstance(validator, list) or isinstance(validator, tuple):
            new.extend(validator)
        else:
            new.append(validator)
        return self.__class__(*new, **{'if_invalid': self.if_invalid})

    def join(cls, *validators):
        """
        Joins several validators together as a single validator,
        filtering out None and trying to keep `All` validators from
        being nested (which isn't needed).
        """
        validators = filter(lambda v: v and v is not Identity, validators)
        if not validators:
            return Identity
        if len(validators) == 1:
            return validators[0]
        elif isinstance(validators[0], All):
            return validators[0].with_validator(validators[1:])
        else:
            return cls(*validators)
    join = classmethod(join)

    def if_missing__get(self):
        for validator in self.validators:
            v = validator.if_missing
            return v

    if_missing = property(if_missing__get)

    def not_empty__get(self):
        not_empty = False
        for validator in self.validators:
            not_empty = not_empty or getattr(validator, 'not_empty', False)
        return not_empty
    not_empty = property(not_empty__get)

    def is_empty(self, value):
        # sub-validators should handle emptiness.
        return False


class UnicodeString(UnicodeString):

    not_empty_string = None

    messages = {
        'badEncoding' : _("Invalid data or incorrect encoding"),
        'emptyString' : _("Field must not be blank"),
    }

    def is_empty(self, value):
        return value is None

    def _to_python(self, value, state):

        value = super(UnicodeString, self)._to_python(value, state)
        if self.not_empty_string and value == '':
            raise Invalid(self.message("emptyString", state), value, state)

        

class RequireIfMissing(FormValidator):

    """
    missing changed for being falsey to be being actually missing
    """

    # Field that potentially is required:
    required = None
    # If this field is missing, then it is required:
    missing = None
    # If this field is present, then it is required:
    present = None
    __unpackargs__ = ('required',)

    def _to_python(self, value_dict, state):
        is_required = False
        if self.missing and value_dict.get(self.missing) is None:
            is_required = True
        if self.present and value_dict.get(self.present):
            is_required = True
        if is_required and value_dict.get(self.required) is None:
            raise Invalid('You must give a value for %s' % self.required,
                          value_dict, state,
                          error_dict={self.required: Invalid(self.message(
                              'empty', state), value_dict, state)})
        return value_dict

RequireIfPresent = RequireIfMissing

