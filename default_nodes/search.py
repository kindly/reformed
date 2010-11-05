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
##   Copyright (c) 2008-2010 Toby Dacre & David Raznick
##

from node.node import TableNode
from node.form import form
from node.page_item import *



class Search(TableNode):


    listing = form(
        result_link('title', data_type = 'link', css = 'form_title'),
        info('summary', data_type = 'info'),
        form_type = "results",

    )


    def call(self, node_token, limit = 20):
        where = "primary_entity._core_entity.title like ?"
        node_data = node_token.get_node_data()
        query = node_data.get('q', '')
        limit = node_data.get_data_int('l', limit)
        values = ['%%%s%%' % query]
        self['listing'].list(node_token, limit, where = where, values = values)
