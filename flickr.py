import urllib2, urllib
import hashlib
import xml.dom.minidom
import os
import os.path
import sys

from optparse import OptionParser

# settings
image_directory = '/stuff/reformed_images'

flicker_api_key = 'fbad3a2cc12fb075d561aa5c0e59160c'
flicker_secret = '421df03390636152'

def flicker_get_xml(method, sent_params = {}):

    params = sent_params.copy()

    # add method and api key
    params['method'] = method
    params['api_key'] = flicker_api_key
    params['per_page'] = 500

    # images only
    params['content_type'] = 1

    # create signature
    signer = flicker_secret
    for key in sorted(params.keys()):
        signer = '%s%s%s' % (signer, key, params[key])
    hash = hashlib.md5()
    hash.update(signer)
    signature = hash.hexdigest()
    
    # build url
    encoded_params = urllib.urlencode(params)
    url = 'http://api.flickr.com/services/rest/?%s&api_sig=%s' % (encoded_params, signature)
    
    xml_data = urllib2.urlopen(url)
    if xml_data:
        return '\n'.join(xml_data)
    else:
        return None

def flicker_get_group_id(group):
    # get xml
    params = dict(text = group)
    xml_data = flicker_get_xml('flickr.groups.search', params)
    # process xml
    dom = xml.dom.minidom.parseString(xml_data)
    groups = dom.getElementsByTagName('group')

    group_id = groups[0].getAttribute('nsid')
    return group_id



def flicker_grab_pics(xml_data, image_count, tag):
    dom = xml.dom.minidom.parseString(xml_data)
    photos = dom.getElementsByTagName('photo')

    # make image directory if needed
    if not os.path.exists(image_directory):
        os.makedirs(image_directory)

    data_file_path = os.path.join(image_directory, image_data_file)

    data_file = open(data_file_path, 'a')
    count = 0

    for photo in photos:
        title = photo.getAttribute('title')
        farm = photo.getAttribute('farm')
        secret = photo.getAttribute('secret')
        id = photo.getAttribute('id')
        server = photo.getAttribute('server')
        if not id:
            # sometimes we get a dud record
            continue

        photo_url = 'http://farm%s.static.flickr.com/%s/%s_%s.jpg' % (farm, server, id, secret)
        # download the image
        image_data = urllib2.urlopen(photo_url)
        image_file_path = os.path.join(image_directory, '%s.jpg' % id)
        image_file = open(image_file_path, 'wb')
        for line in image_data:
            image_file.write(line)
        image_file.close()


        # write data file info
        print title
        try:
            data_file.write(u'%s.jpg|%s|%s\n' % (id, tag, title))
        except UnicodeEncodeError:
            # title had unicode issues
            data_file.write(u'%s.jpg|%s|unicode_error\n' % (id, tag))

        count += 1
        print '%s %s' % (count, title)
        if count > image_count:
            break

    # close data file
    data_file.close()


def get_images(image_count, category = 'general', group = None, search = None):

    params = {}
    if group:
        group_id = flicker_get_group_id(group)
        params['group_id'] = group_id
    if search:
        params['text'] = search

    if params:
        service = 'flickr.photos.search'
    else:
        service = 'flickr.interestingness.getList'

    flicker_xml = flicker_get_xml(service, params)
    flicker_grab_pics(flicker_xml, image_count, category)


def clear_image_dir():
    print 'purging images'
    shutil.rmtree(image_directory)




#clear_image_dir()
#get_images(10)
get_images(100, category = 'men', group = 'man portrait')
#get_images(100, category = 'women', group = 'Female Face ~CloseUps')

