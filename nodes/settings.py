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

from global_session import global_session

def initialise():
    # set defaults

    sysinfo = global_session.application.predefine.sysinfo
    permission = global_session.application.predefine.permission
    user_group = global_session.application.predefine.user_group
    
    sysinfo("file_uploads>dir_depth", 1, "How many levels of directories for uploaded files")
    sysinfo("file_uploads>root_directory", 'files', "Root directory for uploaded files, relative to the application directory")
    sysinfo("file_uploads>max_file_size", 100000, "Maximum file size for uploaded files (in bytes)")
    
    permission(u"FileUploader", u'File uploader', u'can upload files to the server')
    permission(u"FileUploaderLargeFiles", u'Large files', u'can upload files large files to the server')
    
    # sys admin user_group
    user_group(u'fileuploaders', u'File Uploaders', permissions = ['FileUploader'])
