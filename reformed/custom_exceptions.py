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
##	custom_exceptions.py
##	======
##	
##	This file contains the added exception classes needed by reformed

class NoDatabaseError(AttributeError):
    pass
class RelationError(AttributeError):
    pass
class NoMetadataError(AttributeError):
    pass
class NoFieldError(AttributeError):
    pass
class DuplicateTableError(AttributeError):
    pass
class NoTableAddError(AttributeError):
    pass
class NoTableError(AttributeError):
    pass
class InvalidKey(AttributeError):
    pass
class InvalidRow(AttributeError):
    pass
class InvalidField(AttributeError):
    pass
class InvalidData(AttributeError):
    pass
class DatabaseInvalid(AttributeError):
    def __init__(self, msg, list):
        self.msg = msg
        self.list = list

    def __str__(self):
        return str(self.msg) 

    def __repr__(self):
        return str(self.msg) 
