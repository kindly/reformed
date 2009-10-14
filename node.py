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


class Node(object):

    def __init__(self, data, last_node = None):
        self.out = []
        self.action = None
        self.next_node = None
        self.last_node = data.get('lastnode')
        self.data = data.get('data')
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

    """Node for simple table level elements"""
    table = "unknown"
    fields = []
    form_params =  {"form_type": "normal"}
     

    def call(self):
        if  self.command == 'view':
            self._view()
        elif self.command == 'save':
            self._save()
        elif self.command == 'list':
            self._list()
        elif self.command == 'delete':
            self._delete()


    def create_fields(self):

        fields = []
        for field in self.fields:
            row = {}
            row['name'] = field[0]
            row['type'] = field[1]
            row['title'] = field[2]
            row['params'] = {}
            fields.append(row)
        return fields


    def _view(self):
        id = self.data.get('__id')
        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        data = session.query(obj).filter_by(_core_entity_id = id).one()
        data_out = util.get_row_data_basic(data)
        data_out['__id'] = id
        data = {
            "form": {
                "fields":self.create_fields(), 
                "params":self.form_params
            },
            "data": data_out,
            "type": "form", 
        }
        self.out = data
        self.action = 'form'


    def _save(self):

        id = self.data.get('__id')
        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        data = session.query(obj).filter_by(_core_entity_id = id).one()
        data_out_array = util.create_data_dict(data)
        for field in self.fields:
            field_name = field[0]
            value = self.data.get(field_name)
            setattr(data, field_name, value)
        try:
            session.save_or_update(data)
            session.commit()
        except fe.Invalid, e:
            session.rollback()
            print "we fucked!", e.msg
            errors = {}
            for key, value in e.error_dict.items():
                errors[key] = value.msg
            print repr(errors)
            self.out = errors
            self.action = 'save_error'
        session.close()


    def _delete(self):

        id = self.data.get('__id')
        session = r.reformed.Session()
        obj = r.reformed.get_class(self.table)
        data = session.query(obj).filter_by(_core_entity_id = id).one()
        session.delete(data)
        session.commit()
        session.close()


    def _list(self):

        results = r.reformed.search(self.table)
        out = []
        for result in results:
            row = {"table": result["__table"],
                   "id": result["_core_entity.id"],
                   "title": "donkey %s" % result["_core_entity.id"]}
            out.append(row)

        self.out = out
        self.action = 'listing'
