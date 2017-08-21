#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import sys
import time

import overpass
import requests

import gpx_utils

__LOG = logging.getLogger("gpx_loader")

# __SERVERS = []
# __SERVERS.append('http://overpass-api.de/api/interpreter')
# __SERVERS.append('http://overpass.osm.rambler.ru/cgi/interpreter')
# __SERVERS.append('http://api.openstreetmap.fr/oapi/interpreter')
# __SERVERS.append('http://overpass.osm.ch/api/interpreter')

# -- Server also runs several other services so only for light usage
# __SERVERS.append('http://overpass.openstreetmap.ie/api/')

# __SERVER = random.choice(__SERVERS)
__SERVER = 'http://overpass-api.de/api/interpreter'

# Delay between each retry on 'normal' failures.
__OVERPASS_RETRY_DELAY = 10
# Extra delay after an overload type failure.
__OVERPASS_OVERLOAD_DELAY = 60  # 5 * 60
# Maximum number of retries for each request.
__MAX_RETRIES = 10


def __get_from_overpass(search_string, last):
    """

    :param str search_string: The overlass QL string.
    :param bool last: If this is the last try.
    :return: The json result or None if failed.
    """
    delay = __OVERPASS_RETRY_DELAY
    try:
        api = overpass.API(timeout=900, endpoint=__SERVER)
        result = api.Get(search_string, responseformat='json')
        if result is not None:
            # print repr(result)
            # Hack to ensure JSON object correctness????
            result = json.loads(json.dumps(result))

            elements = result['elements']
            if len(elements) < 1:
                __LOG.debug(u'__get_from_overpass: json in get_data contains empty ["elements"]!')
            return result
        __LOG.error(u'__get_from_overpass: API returned None')

    except overpass.errors.OverpassSyntaxError as e:
        __LOG.fatal(u'__get_from_overpass: OverpassSyntaxError: %s' % e.message)
        sys.exit(125)
    except overpass.errors.ServerRuntimeError as e:
        __LOG.error(u'__get_from_overpass: ServerRuntimeError: %s' % e.message)
    except overpass.errors.UnknownOverpassError as e:
        __LOG.error(u'__get_from_overpass: UnknownOverpassError: %s' % e.message)
    except overpass.errors.TimeoutError as e:
        __LOG.error(u'__get_from_overpass: TimeoutError: %s' % e.message)
    except overpass.errors.MultipleRequestsError as e:
        __LOG.error(u'__get_from_overpass: MultipleRequestsError: %s' % e.message)
        delay = __OVERPASS_OVERLOAD_DELAY
    except overpass.errors.ServerLoadError as e:
        __LOG.error(u'__get_from_overpass: ServerLoadError: %s' % e.message)
        delay = __OVERPASS_OVERLOAD_DELAY
    except requests.exceptions.ConnectionError as e:
        __LOG.error(u'__get_from_overpass: ConnectionError: %s' % e.message)
    except TypeError as e:
        __LOG.fatal(u'__get_from_overpass: json.TypeError: %s' % e.message)
        sys.exit(124)
    except ValueError as e:
        __LOG.fatal(u'__get_from_overpass: No Valid JSON Loaded (json.ValueError): %s' % e.message)
        sys.exit(123)
    except KeyError as e:
        __LOG.fatal(u'__get_from_overpass: json in get_data does not contain ["elements"]: %s' % e.message)
        sys.exit(122)

    if not last:
        __LOG.debug(u'__get_from_overpass: Waiting for retry in %s seconds' % delay)
        time.sleep(delay)
    return None


def get_data(search_string):
    """
    :param str|unicode search_string:
    :return dict: JSON data dictionary
    """
    __LOG.info(u'get_data: %s' % search_string)
    for i in range(1, __MAX_RETRIES + 1):
        data = __get_from_overpass(search_string, i >= __MAX_RETRIES)
        if data is not None:
            return data
    raise Exception(u'Max overpass retries overload')


def get_relations_in_bbox(min_lat, min_long, max_lat, max_long, level=2):
    """
    Load boundaries within the bounding box of the given level.

    :param float min_lat: Min latitude
    :param float min_long: Min longitude
    :param float max_lat: Max latitude
    :param float max_long: Max longitude
    :param int level: The administrative level boundaries to load.
    :return: The shape returned.
    """
    if min_lat == max_lat:
        __LOG.error(u'get_relations_in_bbox: Latitude %s equal %s - EXPANDING', str(min_lat), str(max_lat))
        min_lat = min_lat - 0.0000001
        max_lat = max_lat + 0.0000001
    if min_long == max_long:
        __LOG.error(u'get_relations_in_bbox: Longitude %s equal %s - EXPANDING', str(min_long), str(max_long))
        min_long = min_long - 0.0000001
        max_long = max_long + 0.0000001
    if min_lat > max_lat:
        __LOG.error(u'get_relations_in_bbox: Latitude %s greater than %s - SWAPPING', str(min_lat), str(max_lat))
        min_lat, max_lat = gpx_utils.swap(min_lat, max_lat)
    if min_long > max_long:
        __LOG.error(u'get_relations_in_bbox: Longitude %s greater than %s - SWAPPING', str(min_long), str(max_long))
        min_long, max_long = gpx_utils.swap(min_long, max_long)
    search_string = (
        'relation' +
        '["type"="boundary"]' +
        '["boundary"="administrative"]' +
        ('["admin_level"="%d"]' % level) +
        ('(%s,%s,%s,%s);' % (min_lat, min_long, max_lat, max_long)) +
        'out ids;')
    return get_data(search_string)


def get_relations_in_object(obj_id, admin_level):
    area_id = obj_id + 3600000000
    search_string = (
        ('relation(area:%s)' % area_id) +
        '["type"="boundary"]' +
        '["boundary"="administrative"]' +
        ('["admin_level"="%d"];' % admin_level) +
        'out ids;')
    return get_data(search_string)


def get_geometry_for_relation(relation_id, level):
    """
    :param int relation_id: The relation ID.
    :param int level: The admin level.
    :return: The shape returned.
    """
    area_id = relation_id + 3600000000
    # search_string = ('is_in;relation' +
    #                  '["type"="boundary"]' +
    #                  '["boundary"="administrative"]' +
    #                  ('["admin_level"="%s"]' % level) +
    #                  ('(%s);' % relation_id) +
    #                  'out tags;')
    search_string = (('relation(area:%s)' % area_id) +
                     '["type"="boundary"]' +
                     '["boundary"="administrative"]' +
                     ('["admin_level"="%s"] -> ._;' % level) +
                     'way(r:"outer") + way(r:"inner");' +
                     'out geom;')
    return get_data(search_string)