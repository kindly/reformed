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

from node import Node
from form import form
from page_item import *


def make_menu(node_manager):

    node_manager.add_menu(dict(name = 'Help', title = 'Dev Help'))

class Menu(Node):

    main = form(
        
        text("""
## Menu Setup
             
Menu items are added as a dict and use the following keys

* `name` (optional) - The name of the menu item needed if sub menus are to be attached.
* `menu` (optional) - The name of the parent menu item to be added to.
* `title` - The title of the menu that the user will see.
* `node` (optional) - The node that will be called see later for details.
* `flags` (optional) - Any flags that the node will be called with if not supplied `u` flag is defaulted.
* `function` (optional) - The front end function to be called.
* `permissions` (optional) - The permissions needed to see this menu item.

The items are added in two places.  First the `make_menu()` function for the module is called by the NodeManager.
Second it is called for each node.  The function does not need to exist.

`node` - is the node that will be called when the menu option is selected.  The format is `node name[:command[:url data]]` __note__ no flags are given here if needed they can be supplied via the `flags` key. `$` can be as shorthand for the current node.

examples:

module example:

    def make_menu(node_manager):
        node_manager.add_menu(dict(name = 'Help', title = 'Dev Help'))

node example:

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'Help', title = 'Menu Setup', node = '$'))

             """),
    )


    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'Help', title = 'Menu Setup', node = '$'))

    def call(self, node_token):
        self['main'].show(node_token)
    
