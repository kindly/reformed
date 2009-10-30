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

import reformed.reformed as r
import reformed.util as util
import formencode as fe
import sqlalchemy as sa

class Node(object):

    def __init__(self, data, node_name, last_node = None):
        self.out = []
        self.name = node_name
        self.action = None
        self.next_node = None
        self.next_data = None
        self.last_node = data.get('lastnode')
        self.data = data.get('data')
        if type(self.data).__name__ != 'dict':
            self.data = {}
        self.command = data.get('command')

        if self.last_node == self.__class__.__name__:
            self.first_call = False
        else:
            self.first_call = True
        print '~~~~ NODE DATA ~~~~'
        print 'command:', self.command
        print 'last node:', self.last_node
        print 'first call:', self.first_call
        print 'data:', self.data
        print '~' * 19

    def initialise(self):
        """called first when the node is used"""
        pass

    def call(self):
        """called when the node is first used"""
        pass

    def finalise(self):
        """called last when node is used"""
        pass


class TableNode(Node):

    """Node for table level elements"""
    table = "unknown"
    fields = []
    form_params =  {"form_type": "normal"}
    list_title = 'item %s'

    subforms = {}
    subform_data = {}

    first_run = True



    def __init__(self, *args, **kw):
        super(TableNode, self).__init__(*args, **kw)
        if self.__class__.first_run:
            self.__class__.first_run = False
            print 'first run'
            self.setup_forms()

    def setup_forms(self):
        for field in self.fields:
            if field[1] == 'subform':
                name = field[2]
                subform = self.__class__.subforms.get(name)
                data = create_form_data(subform.get('fields'), subform.get('params'))
                data['form']['parent_id'] =  subform.get('parent_id')
                data['form']['child_id'] =  subform.get('child_id')
                self.__class__.subform_data[name] = data
                field.append(data)           

    def call(self):
        if  self.command == 'view':
            self.view()
        elif self.command == 'save':
            self.save()
        elif self.command == 'list':
            self.list()
        elif self.command == 'delete':
            self.delete()
        elif self.command == 'new':
            self.new()


    def save_record_rows(self, session, table, fields, data, join_fields):
        for row_data in data:
            row_id = row_data.get('id', 0)
            root = row_data.get('__root')
            if row_id:
                filter = {'id' : row_id}
            else:
                filter = {}
            self.save_record(session, table, fields, row_data, filter, root = root, join_fields = join_fields)

    def save_record(self, session, table, fields, data, filter, root, join_fields = []):
        print 'table %s' % table
        print 'fields %s' % fields
        errors = None

        try:
            if filter:
                print 'existing record'
                obj = r.reformed.get_class(table)
                record_data = session.query(obj).filter_by(**filter).one()
            else:
                print 'new record'
                record_data = r.reformed.get_instance(table)
            for field in fields:
                field_name = field[0]
                field_type = field[1]
                if field_name != 'id' and field_type != 'subform':
                    value = data.get(field_name)
                    print '%s = %s' % (field_name, value)
                    setattr(record_data, field_name, value)
            for field_name in join_fields:
                    value = data.get(field_name)
                    print 'join: %s = %s' % (field_name, value)
                    setattr(record_data, field_name, value)
            try:
                session.save_or_update(record_data)
                session.commit()
                self.saved.append([root, record_data.id])
            except fe.Invalid, e:
                session.rollback()
                print "failed to save\n%s" % e.msg
                errors = {}
                for key, value in e.error_dict.items():
                    errors[key] = value.msg
                print repr(errors)
                self.errors[root] = errors
        except sa.orm.exc.NoResultFound:
            self.errors[root] = 'record not found'

    def save(self):

        self.saved = []
        self.errors = {}

        session = r.reformed.Session()
        id = self.data.get('id')
        root = self.data.get('__root')
        if id:
            filter = {'id' : id}
        else:
            filter = {}

        self.save_record(session, self.table, self.fields, self.data, filter, root)

        # FIXME how do we deal with save errors more cleverly?
        # need to think about possible behaviours we want
        # and add some 'failed save' options
        if not self.errors:
            for subform_name in self.subforms.keys():
                subform_data = self.data.get(subform_name)
                if subform_data:
                    subform = self.subforms.get(subform_name)
                    table = subform.get('table')
                    fields = subform.get('fields')
                    # do we have a joining field?
                    child_id = subform.get('child_id')
                    if child_id:
                        join_fields= [child_id]
                    self.save_record_rows(session, table, fields, subform_data, join_fields)

        session.close()

        # output data
        out = {}
        if self.errors:
            out['errors'] = self.errors
        if self.saved:
            out['saved'] = self.saved

        self.out = out
        self.action = 'save'


    def new(self):

        data_out = {}
        data = create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'


    def view(self):
        id = self.data.get('id')
        if id:
            filter = {'id' : id}
        else:
            id = self.data.get('__id')
            filter = {'_core_entity_id' : id}

        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        try:
            data = session.query(obj).filter_by(**filter).one()
            data_out = util.get_row_data(data, keep_all = False, basic = True)
            data_out['id'] = data.id
            people_id = data.id
        except sa.orm.exc.NoResultFound:
            data_out = {}
            people_id = 0

        for subform_name in self.subforms.keys():
            print 'subforrm', subform_name
            print self.subforms
            subform = self.subforms.get(subform_name)
            subform_parent_id = subform.get('parent_id')
            subform_parent_value = getattr(data, subform_parent_id)
            subform_data = self.subform_data.get(subform_name)
            data_out[subform_name] = self.subform(session, subform, subform_data, subform_parent_value)

        data = create_form_data(self.fields, self.form_params, data_out)
        self.out = data
        self.action = 'form'
        session.close()

    def delete(self):

        id = self.data.get('__id')
        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        try:
            data = session.query(obj).filter_by(_core_entity_id = id).one()
            session.delete(data)
            session.commit()
            self.next_node = self.name
            self.next_data = {'command': 'list'}
        except sa.orm.exc.NoResultFound:
            errors = {'~': 'record not found'}
            self.out = errors
            self.action = 'delete_error'
        session.close()


    def list(self, limit=20):
        results = r.reformed.search('_core_entity', "%s.id >0" % self.table, limit=limit)
        out = []
        for result in results:
            row = {"table": self.table,
                   "id": result["_core_entity.id"],
                   "title": result["_core_entity.title"],
                   "summary": result["_core_entity.summary"]}
            out.append(row)

        self.out = out
        self.action = 'listing'


    def subform(self, session, subform, form_data, parent_value):

        table = subform.get('table')
        child_id = subform.get('child_id')
        obj = r.reformed.get_class(table)
        filter = {child_id : parent_value}
        try:
            data = session.query(obj).filter_by(**filter).all()
            out = util.create_data_array(data, keep_all=False, basic=True)
        except sa.orm.exc.NoResultFound:
            out = {}
        return out





def create_fields(fields_list):

    fields = []
    for field in fields_list:
        row = {}
        row['name'] = field[0]
        row['type'] = field[1]
        row['title'] = field[2]
        if len(field) > 3:
            row['params'] = field[3]
        fields.append(row)
    return fields



def create_form_data(fields, params=None, data=None):
    out = {
        "form": {
            "fields":create_fields(fields)
        },
        "type": "form",
    }
    if data:
        out['data'] = data
    if params:
        out['form']['params'] = params
    return out

def validate_data(data, field, validator):
    try:
        return validator().to_python(data.get(field))
    except:
        return None

def validate_data_full(data, validators):
    validated_data = {}
    for (field, validator) in validators:
        validated_data[field] = validate_data(data, field, validator)
    return validated_data
