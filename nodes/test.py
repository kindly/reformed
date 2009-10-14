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

from node import Node
from .reformed import reformed as r
from .reformed import util
import formencode as fe

class Text(Node):

    def call(self):
        data = {'html': 'goodbye'}
        self.out = data
        self.action = 'html'

class Donkey(Node):

    def call(self):
        if  self.command == 'view':
            self._view()
        elif self.command == 'save':
            self._save()
        elif self.command == 'list':
            self._list()

    def _view(self):
            id = self.data.get('id')
            session = r.reformed.Session()
            obj = r.reformed.get_class('donkey')
            data = session.query(obj).filter_by(_core_entity_id = id).all()[0]
            data_out = util.get_row_data_basic(data)
            data_out['__id'] = id
            data = {
            "form": {
                "fields": [
                    {
                        "params": {}, 
                        "type": "textbox", 
                        "name": "name", 
                        "title": "name:"
                    }, 
                    {
                        "params": {}, 
                        "type": "textbox", 
                        "name": "age", 
                        "title": "age:"
                    }
                ], 
                "params": {
                    "form_type": "normal", 
                    "form_object": "donkey"
                }
            },
            "data": data_out,
            "type": "form", 
            "id": "donkey"
        }
            self.out = data
            self.action = 'form'

    def _save(self):

            id = self.data.get('__id')
            session = r.reformed.Session()
            obj = r.reformed.get_class('donkey')
            data = session.query(obj).filter_by(_core_entity_id = id).all()[0]
            data_out_array = util.create_data_dict(data)
            setattr(data, 'name', self.data.get('name'))
            setattr(data, 'age', self.data.get('age'))
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

    def _list(self):

        search_table = "donkey"

        results = r.reformed.search(search_table)

        out = []

        for result in results:
            row = {"table": result["__table"],
                   "id": result["_core_entity.id"],
                   "title": "donkey %s" % result["_core_entity.id"]}
            out.append(row)

        self.out = out
        self.action = 'listing'
