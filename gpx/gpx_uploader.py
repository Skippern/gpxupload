import json
import logging
import os
import sys
import time

import requests

import gpx_utils

__LOG = logging.getLogger('gpx_uploader')
__ENABLE_UPLOAD = False
__UPLOAD_FAILURE_DELAY = 60
__UPLOAD_MAX_TRIES = 10
__TRACK_VISIBILITY = u'public'  # public, private, trackable, identifiable


def upload_gpx(gpx_file, tags, description):
    """
    :param str gpx_file: GPX file to upload
    :param str tags: String tags to annotate with.
    :param str description: Description of file content.
    :return:
    """
    user_name = os.environ.get('OSM_USER')
    if user_name is None:
        user_name = os.environ.get('MAPILLARY_EMAIL')
    if user_name is None:
        __LOG.critical(u'NO USERNAME SET FOR UPLOAD')
        print u'For upload to work, you need to set the environmental variables OSM_USER and OSM_PASSWORD'
        sys.exit(99)
    password = os.environ.get('OSM_PASSWORD')
    if password is None:
        password = os.environ.get('MAPILLARY_PASSWORD')
    if password is None:
        __LOG.critical(u'NO PASSWORD SET FOR UPLOAD')
        print u'For upload to work, you need to set the environmental variables OSM_USER and OSM_PASSWORD'
        sys.exit(99)
    send_tags = gpx_utils.enforce_unicode(tags.replace('.', '_'))

    payload = {u'description': description, u'tags': send_tags, u'visibility': __TRACK_VISIBILITY}

    if not __ENABLE_UPLOAD:
        __LOG.debug(u'Upload disabled!')
        print repr(payload)
        sys.exit(3)

    payload = json.loads(json.dumps(payload))
    try:
        url = 'http://www.openstreetmap.org/api/0.6/gpx/create'
        files = {u'file': open(gpx_file, 'rb')}
        r = None
        for i in range(1, __UPLOAD_MAX_TRIES + 1):
            try:
                r = requests.post(url, auth=(user_name, password), files=files, data=payload)
                break
            except requests.exceptions.ReadTimeout:
                pass
            except requests.exceptions.ConnectionError:
                pass
            if i >= __UPLOAD_MAX_TRIES:
                raise Exception(u'Too many attempts at uploading: max %d' % i)
            time.sleep(__UPLOAD_FAILURE_DELAY)
    except Exception as e:
        __LOG.fatal(u'Exception thrown in upload_gpx: %s' % e.message)
        raise Exception("", e)
    if r.status_code == 200:
        print u'Uploaded with success'
        __LOG.info(u'%s Upload completed with success', gpx_file)
        sys.exit(0)
    else:
        print u'Ended with status code: {0}'.format(r.status_code)
        print r.text
        __LOG.error(u'Upload unsuccessful, ended with status code: %s', r.status_code)
        __LOG.error(u'Message: %s', r.text)
        sys.exit(r.status_code)
