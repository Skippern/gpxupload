import json
import logging
import os
import sys
import time

import requests

__LOG = logging.getLogger('gpx_store')
__ENABLE_UPLOAD = False
__UPLOAD_FAILURE_DELAY = 60
__UPLOAD_MAX_TRIES = 10
__TRACK_VISIBILITY = u"public" # public, private, trackable, identifiable


def upload_gpx(gpx_file, tags, description):
    """
    :param str gpx_file: GPX file to upload
    :param str tags: String tags to annotate with.
    :param str description: Description of file content.
    :return:
    """
    user_name = os.environ.get("OSM_USER")
    if user_name is None:
        user_name = os.environ.get("MAPILLARY_EMAIL")
    if user_name is None:
        __LOG.critical("NO USERNAME SET FOR UPLOAD")
        print "For upload to work, you need to set the environmental variables OSM_USER and OSM_PASSWORD"
        sys.exit(99)
    password = os.environ.get("OSM_PASSWORD")
    if password is None:
        password = os.environ.get("MAPILLARY_PASSWORD")
    if password is None:
        __LOG.critical("NO PASSWORD SET FOR UPLOAD")
        print "For upload to work, you need to set the environmental variables OSM_USER and OSM_PASSWORD"
        sys.exit(99)
    send_tags = tags.replace(".", "_")
    try:
        send_tags = send_tags.encode('utf-8')
    except:
        pass
    try:
        send_tags = unicode(send_tags)
    except:
        pass
    payload = {u"description": description, u"tags": send_tags, u"visibility": __TRACK_VISIBILITY}

    if not __ENABLE_UPLOAD:
        __LOG.debug("Upload disabled!")
        print repr(payload)
        sys.exit(3)

    payload = json.loads(json.dumps(payload))
    try:
        url = "http://www.openstreetmap.org/api/0.6/gpx/create"
        files = {u'file': open(gpx_file, 'rb')}
        r = None
        i = 1
        while r is None:
            if i > __UPLOAD_MAX_TRIES:
                raise Exception("Too many attempts at uploading: %d" % (i - 1))
            try:
                r = requests.post(url, auth=(user_name, password), files=files, data=payload)
            except requests.exceptions.ReadTimeout as e:
                time.sleep(__UPLOAD_FAILURE_DELAY)
            except requests.exceptions.ConnectionError as e:
                time.sleep(__UPLOAD_FAILURE_DELAY)
    except Exception as e:
        __LOG.fatal("Exception thrown in upload_gpx: %s" % e.message)
        raise Exception("", e)
    if r.status_code == 200:
        print "Uploaded with success"
        __LOG.info("%s Upload completed with success", gpx_file)
        sys.exit(0)
    else:
        print "Ended with status code: {0}".format(r.status_code)
        print r.text
        __LOG.error("Upload unsuccessful, ended with status code: %s", r.status_code)
        __LOG.error("Message: %s", r.text)
        sys.exit(r.status_code)
