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
import os
import tempfile
import hashlib
import cgi
import time #FIXME testing only
import json
import mimetypes

import reformed.util
from global_session import global_session
r =  global_session.database

# set defaults
from predefine import sysinfo, permission
sysinfo("file_uploads>dir_depth", 2, "How many levels of directories for uploaded files")
sysinfo("file_uploads>root_directory", 'files', "Root directory for uploaded files, relative to the application directory")

permission("FileUploader", u'File uploader', u'can upload files to the server')
permission("FileUploaderLargeFiles", u'Large files', u'can upload files large files to the server')

# upload exceptions
class UploadDuplicateReference(AttributeError):
    pass

class UploadUnknownReference(AttributeError):
    pass

class UploadNoFileUploads(AttributeError):
    pass


def create_file_path(filename, id):

    """Create a name for the file based on it's id and origional extension
    create a 'random' path if needed to balance file system"""

    num_levels =  r.sys_info['file_uploads>fake_save']
    (null, ext) = os.path.splitext(filename)
    file_id = str(id) + ext

    hash = hashlib.sha224(filename + file_id).hexdigest()[:num_levels * 2]
    path = ''
    for i in xrange(num_levels):
        path = os.path.join(hash[i * 2 : (i + 1) * 2], path)

    return (path, file_id)



def fileupload_status(environ, start_response):
    
    """Return the status of a file upload"""

    reference = environ['QUERY_STRING']
    # we need a unique user reference
    # for now this will do but it does not safely allow for more than one tab
    # maybe if the references are random enough we can prevent clashes
    # need to think how to do this better

    http_session = global_session.session
    if not http_session.has_key('file_uploads'):
        raise UploadNoFileUploads

    if not http_session['file_uploads'].has_key(reference):
        raise UploadUnknownReference

    result = http_session['file_uploads'][reference]
    out = dict(bytes_left = result['bytes_left'], bytes = result['bytes'], completed = result['complete'])

    # TODO if completed kill reference from database

    start_response('200 OK', [('Content-Type', 'text/html')])
    return [json.dumps(out, sort_keys=False, separators=(',',':'))]


def fileupload(environ, start_response):

    """upload the file from the user and log the upload status
    so it can be retrieved by another thread"""

    # We log the status of the upload in the database
    # each upload needs a user supplied reference to track the
    # upload.  It has to be supplied by the client as it will
    # be used to track the upload.
    # we also need a unique key for the user's application session
    # that is for each browser tab.  I'm not sure this can be done
    # so per browser is possible but not AFAIK for a tab.
    

    save = False # disable/enable saving for testing
    min_update_interval = 1 # in seconds

    data = environ['wsgi.input']
    reference = environ['QUERY_STRING']
    length = int(environ['CONTENT_LENGTH'])

    http_session = global_session.session
    # create file_uploads hash if doesn't exist
    if not http_session.has_key('file_uploads'):
        http_session['file_uploads'] = {}

    if http_session['file_uploads'].has_key(reference):
        raise UploadDuplicateReference

    http_session['file_uploads'][reference] = {}
    status = http_session['file_uploads'][reference]

    status['complete'] = False
    status['bytes_left'] = length
    status['bytes'] = length
  
    http_session.persist()


    # We now chunk through the data.  If we try to read more data than is sent
    # then we will hang till we eventually timeout
    # this is risk as far as DoS is concerned but limiting the number of uploads per
    # user etc would help mitigate it.
    # we read the data and save it into a temporary file.
    bytes_left = length
    temp = tempfile.TemporaryFile(mode = 'w+b')

    size = 1024 # the block size for reading

    while bytes_left:
        if size > bytes_left:
            size = bytes_left
        chunk = data.read(size)
        bytes_left -= size
        temp.write(chunk)
        status['bytes_left'] = bytes_left
        http_session.persist()
        # FIXME testing slowdown remove
        time.sleep(0.01)

    # ? do we need a flush here.
    # I think proberbly not as we are just reading the file again
    # but it can stay for now.
    temp.flush()
    # upload has completed
    # return to start of file and then feed this to the cgi.FieldStorage
    temp.seek(0)
    formdata = cgi.FieldStorage(fp=temp,
                        environ=environ,
                        keep_blank_values=1)

    session = r.Session()
    root = reformed.util.get_dir()
    # find all files and save them
    for field in formdata:
        item = formdata[field]
        if item.filename:
            # add file data to database
            # We need to know the id of the file before we actually save it.
            # as we use the id in the filename and also for creating the path
            obj = r.get_instance('upload')
            obj.filename = item.filename
            session.add(obj)
            session.commit()
            (path, file_id) = create_file_path(item.filename, obj.id)
            # save the file in the correct location
            dir = os.path.join(root, r.sys_info['file_uploads>root_directory'], path)
            if not os.path.exists(dir):
                os.makedirs(dir)
            full_path = os.path.join(dir, file_id)
            f = open(full_path, 'wb')
            while True:
                chunk = item.file.read(4096)
                if not chunk:
                    break
                f.write(chunk)
            f.close()
            # update the data for the file
            mimetype = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'
            obj.mimetype = mimetype
            stat = os.stat(full_path)
            size = str(stat.st_size)
            obj.size = size
            path = os.path.join(path, file_id)
            obj.path = path
            session.add(obj)
            session.commit()

    status['complete'] = True
    status['bytes_left'] = 0
  
    http_session.persist()
   
    session.close()
            
    start_response('200 OK', [('Content-Type', 'text/html')])
    return ['moo']

