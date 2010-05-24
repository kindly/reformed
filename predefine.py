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


class Predefine(object):

    def __init__(self, application):
        self.cached_data = {}
        self.application = application
        self.database = application.database

    def sysinfo(self, key, value, description = '', force = False):
        """add/update system infomation and return the current value for the given key"""
        return self.application.register_info(key, value, description, force)



    def permission(self, code, name, description = u''):
        data = dict(name = name,
                    description = description)
        self.add_data("permission", "permission", code, data)

    def user_group(self, group_name, name, description = u'', permissions = []):
        data = dict(name = name,
                    description = description,
                    created_by = 1,
                    _modified_by = 1,
                    active = True)
        id = self.add_data("user_group", "groupname", group_name, data)
        if id and permissions:
            self.add_permissions_to_user_group(id, permissions)

    def add_permissions_to_user_group(self, user_group_id, permissions):
        self.build_data_cache("permission", "permission")
        for permission in permissions:
            try:
                permission_id = self.cached_data["permission"][permission]
            except KeyError:
                raise
            # add row
            new_row = self.database.get_instance("user_group_permission")
            setattr(new_row, 'user_group_id', user_group_id)
            setattr(new_row, 'permission_id', permission_id)
            session = self.database.Session()
            session.add(new_row)
            session.commit()
            session.close()


    def code_type(self, code_type, name, description = u''):
        data = dict(description = description,
                    created_by = 1,
                    _modified_by = 1,
                    name = name)
        self.add_data("code_type", "code_type", code_type, data)

    def code(self, code, code_type, name, description = u''):
        if 'code_type' not in self.database.tables:
            print 'code_type table does not exist cannot add code'
            return
        data = dict(description = description,
                    created_by = 1,
                    code_type = code_type,
                    _modified_by = 1,
                    name = name,
                    active = True)
        self.add_data("code", "name", code, data)


    def build_data_cache(self, table, key_field):
        if table not in self.database.tables:
            print 'Table <%s> does not exist cannot add data <%s>' % (table, key_data)
            raise #FIXME what exception?
        # cache data if we don't have it already
        if table not in self.cached_data:
            self.cached_data[table] = {}
            values = self.database.search(table, fields = [key_field, 'id']).data
            for record in values:
                self.cached_data[table][record[key_field]] = record['id']


    def add_data(self, table, key_field, key_data, data):
        """check data exists in the database, add it if not there"""

        self.build_data_cache(table, key_field)

        if key_data not in self.cached_data[table]:
            # not in database, add data
            new_row = self.database.get_instance(table)
            setattr(new_row, key_field, key_data)

            for key, value in data.iteritems():
                setattr(new_row, key, value)

            session = self.database.Session()
            session.add(new_row)
            session.commit()
            inserted_id = new_row.id
            session.close()
            print 'add %s to %s' % (key_data, table)
            # add to cache
            self.cached_data[table][key_data] = inserted_id

        # return id for key_data
        return self.cached_data[table][key_data]
