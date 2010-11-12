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

from node.node import TableNode, Node, AutoForm
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

class Page(Node):
    main = form(
        info('body'),
        read_only = True,
    )

    def call(self, node_token):
        node_data = node_token.get_node_data()
        page = node_data.get('page')
        if page:
            query = {"page": page}
        else:
            core_id = node_data.get('__id')
            if core_id:
                query = {"_core_id": core_id}

        data = r.search("page",
                           query,
                           ).data
        print data
        if not data:
            data = [dict(body = '**Sorry**, no page found')]
            title = 'Page not found'
        else:
            title = data[0].get('title')
            node_token.set_layout_buttons([['Edit', 'search.EditPage:edit?__id=%s' % data[0].get('_core_id')]])
            # set bookmark
            node_token.bookmark = dict(
                table_name = 'page',
                _core_id = data[0].get('_core_id')
            )
        self['main'].show(node_token, data[0])
        node_token.set_layout_title(title)


class EditPage(TableNode):

    listing = form(
        result_link('title'),
        result_link_list([['Edit', '$:edit'],
                            ['Delete', '@$:_delete'],]),
        form_type = "results",
        layout_title = "results",
    )

    main = form(
        input('page'),
        input('title'),
        wmd('body'),
        table = "page", #FIXME should get this from the node
    )
    table = "page"

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'Admin', title = 'Pages', node = '$:list'))
