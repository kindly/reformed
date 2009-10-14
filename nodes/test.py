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

from node import TableNode


#class Text(Node):
#
#    def call(self):
#        data = {'html': 'goodbye'}
#        self.out = data
#        self.action = 'html'

class Donkey(TableNode):

    table = "donkey"
    fields = [
        ['name', 'textbox', 'name:'],
        ['age', 'textbox', 'age:']
    ]
    list_title = 'donkey %s'
     
class People(TableNode):

    table = "people"
    fields = [
        ['name', 'textbox', 'name:'],
        ['address_line_1', 'textbox', 'address:'],
        ['postcode', 'textbox', 'postcode:']
    ]
    list_title = 'person %s'

