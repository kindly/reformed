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

class Node1(Node):

    def call1(self):
        print "call"
        self.next_node = 'test.Node4'

    def call2(self):
        print "return"

class Node2(Node):

    def call1(self):
        print "call2"
        self.next_node = 'test.Node2'
    def call2(self):
        print "return2"
        self.out.append('moo')

class Node3(Node):

    def call1(self):
        session = r.reformed.Session()
        obj = r.reformed.get_class('donkey')
        data = session.query(obj).filter_by(id = 5).all()[0]
        data_out_array = util.create_data_dict(data)
        print repr(data_out_array)
        setattr(data, 'age', 72)
        session.save_or_update(data)
        session.commit()

class Node4(Node):

    def call1(self):
        data = {'html': 'hello'}
        self.out = data
        self.action = 'html'

class Node5(Node):

    def call1(self):
        data = {'html': 'goodbye'}
        self.out = data
        self.action = 'html'

class Node6(Node):

    def call1(self):
        if self.command == 'a':
            data = {'html': 'moo'}
            self.out = data
            self.action = 'html'
        elif self.command == 'b':
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
                    },
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
            "data": {
                "__id": 1,
                "donkey.age": 5, 
                "donkey.name": "feddy100"
            }, 
            "type": "form", 
            "id": "donkey"
        }
            self.out = data
            self.action = 'form'
        elif self.command == 'c':
            data = {
            "form": {
                "fields": [
                    {
                        "params": {}, 
                        "type": "textbox", 
                        "name": "donkey.name", 
                        "title": "name:"
                    }
                ], 
                "params": {
                    "form_type": "normal", 
                    "form_object": "donkey"
                }
            }, 
            "type": "form", 
            "id": "donkey"
        }
            self.out = data
            self.action = 'form'
#        {
#            "data": {
#                "1": {
#                    "donkey.age": null, 
#                    "donkey.name": "feddy100"
#                }
#            }, 
#            "object": "donkey", 
#            "type": "data"
#        }, 
