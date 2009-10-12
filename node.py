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


