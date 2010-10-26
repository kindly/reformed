
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

import os.path

from node.node import JobNode, Node
from node.form import form
from node.page_item import *
from web.global_session import global_session

def make_menu(node_manager):
    node_manager.add_menu(dict(name = 'Debug', menu = 'Admin', title = 'Debug', index = 10))
    node_manager.add_menu(dict(menu = 'Debug', title = 'History', function = 'debug_history'))
    node_manager.add_menu(dict(menu = 'Debug', title = 'Form info', function = 'debug_form_info'))
    node_manager.add_menu(dict(menu = 'Debug', title = 'HTML', function = 'debug_html'))
    node_manager.add_menu(dict(menu = 'Debug', title = 'Test drive', function = 'debug_test_drive_next'))
    node_manager.add_menu(dict(menu = 'Debug', title = 'Test drive2', node = 'debug.TestFile'))

class TestFile(Node):

    def call(self, node_token):
        f = open(os.path.join(global_session.application.application_folder, 'testfile.json'))
        data = f.read()
        node_token.function('debug_test_drive_script', data)
