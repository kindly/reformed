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


class Text(Node):

    def call(self):
        data = {'html': 'goodbye'}
        self.out = data
        self.action = 'html'

class Donkey(Node):

    def call(self):
        if  self.command == 'view':
            id = self.data.get('id')
            session = r.reformed.Session()
            obj = r.reformed.get_class('donkey')
            data = session.query(obj).filter_by(id = id).all()[0]
            data_out = util.get_row_data(data)
            data_out['__id'] = id
            data = {
            "form": {
                "fields": [
                    {
                        "params": {}, 
                        "type": "textbox", 
                        "name": "donkey.name", 
                        "title": "name:"
                    }, 
                    {
                        "params": {}, 
                        "type": "textbox", 
                        "name": "donkey.age", 
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

        elif self.command == 'save':
            id = self.data.get('__id')
            session = r.reformed.Session()
            obj = r.reformed.get_class('donkey')
            data = session.query(obj).filter_by(id = id).all()[0]
            data_out_array = util.create_data_dict(data)
            setattr(data, 'name', self.data.get('donkey.name'))
            setattr(data, 'age', self.data.get('donkey.age'))
            session.save_or_update(data)
            session.commit()
