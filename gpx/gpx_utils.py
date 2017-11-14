#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os

import chardet
import yaml
from shapely.geometry import Point, MultiPoint

config = load_config()

__LOG = logging.getLogger('gpx_utils')
__CODECS = ['ascii', 'iso-8859-2', 'iso-8859-1', 'iso-8859-3', 'iso-8859-4', 'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8', 'iso-8859-9', 'iso-8859-10', 'iso-8859-11', 'iso-8859-12', 'iso-8859-13', 'iso-8859-14', 'iso-8859-15', 'iso-8859-16', 'mac-latin2', 'big5', 'cp037', 'cp1006', 'cp1026', 'cp1140', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256', 'cp1257', 'cp1258', 'cp424', 'cp437', 'cp500', 'cp720', 'cp737', 'cp755', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'euc_jis-2004', 'gb18030', 'gb2312', 'gbk', 'hp-roman8', 'mac_arabic', 'mac_centeuro', 'mac_croatian', 'mac_cyrillic', 'mac_farsi', 'mac_greek', 'mac_iceland', 'mac_roman', 'mac_romanian', 'mac_turkish', 'palmos', 'ptcp154', 'tis_620', 'mbcs', 'utf-8']
__DEBUGGING = False
try:
    __NAME_LANGUAGES = config['languages']
except:
    __NAME_LANGUAGES = ['en', 'no', 'pt']


class BBox(object):
    def __init__(self, min_lat, min_lon, max_lat, max_lon):
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon

    def tuple(self):
        return self.min_lat, self.min_lon, self.max_lat, self.max_lon


def bbox_for_track(track):
    """
    Get the bounding box for the track.
    :param MultiPoint|Point track:
    :return:
    """
    return BBox(track.bounds[1], track.bounds[0], track.bounds[3], track.bounds[2])


def enforce_unicode(s):
    """
    :param s:
    :return unicode: Unicode string
    """
    #    logger.debug('clean(%s)', i)
    if isinstance(s, unicode):
        return s
    if not isinstance(s, str):
        return unicode(str(s))

    codec = 'utf-8'
    try:
        encoding = chardet.detect(s)
        codec = encoding['encoding']
        try:
            s = s.encode(codec).decode('utf8')
            __LOG.debug(u'enforce_unicode(i) Text identified as %s', codec)
        except Exception as e:
            __LOG.debug(u'enforce_unicode(i) failed to detect codec: %s' % e.message)
    except:
        pass
    __LOG.debug(u'enforce_unicode(i) codec is %s', codec)
    if isinstance(s, unicode):
        return s
    __LOG.debug(u'Need to run down codecList in enforce_unicode(i)')
    for codec in __CODECS:
        try:
            s = s.encode(codec).decode('utf8')
            break
        except:
            pass
    return unicode(s)


def deg2meter(deg):
    """
    :param float deg: Degrees.
    :return: Meters
    """
    return deg * (60.0 * 1852.0)


def meter2deg(meter):
    """
    :param float meter: Meters.
    :return float: Degrees.
    """
    return meter / (1852.0 * 60.0)


def swap(a, b):
    return b, a


def remove_duplicates(values):
    """
    :param [] values: list of values
    :return []: The same list without duplicated values
    """
    output = []
    seen = set()
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output


def test_object(track, obj):
    """
    :param track: The track to test.
    :param obj: The polygon object to test against.
    :return bool: If the track is within or interesects the object
    """
    if obj == None:
        return False
    if track.within(obj):
        return True
    if track.intersects(obj):
        return True
    return False


def get_name(tags):
    """
    :param dict tags: tags for the relation
    :return unicode: relation name
    """
    rel_name = None
    try:
        rel_name = tags['name:en']
    except KeyError:
        # Some does not have separate english and native name.
        pass

    if rel_name is None or rel_name is '':
        rel_name = tags['name']

    return enforce_unicode(rel_name)


def get_tags(tags):
    """
    :param dict tags: Tags dictionary from overpass data response.
    :return []: list of tags
    """
    out = []
    if __DEBUGGING:
        try:
            out.append(enforce_unicode(tags['admin_level']))
        except KeyError:
            pass
    try:
        out.append(enforce_unicode(tags['name']))
    except KeyError:
        pass

    for lang in __NAME_LANGUAGES:
        try:
            out.append(enforce_unicode(tags['name:%s' % lang]))
        except KeyError:
            pass
        try:
            out.append(enforce_unicode(tags['official_name:%s' % lang]))
        except KeyError:
            pass
        try:
            out.append(enforce_unicode(tags['alt_name:%s' % lang]))
        except KeyError:
            pass
        try:
            out.append(enforce_unicode(tags['long_name:%s' % lang]))
        except KeyError:
            pass

    try:
        out.append(enforce_unicode(tags['official_name']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['short_name']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['long_name']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['alt_name']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['loc_name']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['old_name']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['ISO3166-1']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['ISO3166-1:alpha2']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['ISO3166-1:alpha3']))
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['ISO3166-2']))
    except KeyError:
        pass
    try:
        is_in_all = enforce_unicode(tags['is_in'])
        for is_in in is_in_all.split(';'):
            out.append(is_in)
    except KeyError:
        pass
    try:
        out.append(enforce_unicode(tags['is_in:continent']))
    except KeyError:
        pass

    return out

def store_config(obj)
    config_file = '%s/.gpx_upload.yaml' % os.environ['HOME']
    try:
        with open(config_file, 'w') as f:
            f.write(yaml.dump(obj, Dumper=yaml.Dumper))
    except IOError:
        pass

def load_config():
    obj = {
        'cache_dir': '%s/.cache/gpx' % os.environ['HOME'],
        'enable_upload': True,
        'overpass_server': 'http://overpass-api.de/api/interpreter',
        'track_visibility': 'public',
        'languages': [ 'en' ],
    }
    config_file = '%s/.gpx_upload.yaml' % os.environ['HOME']
    try:
        with open(config_file, 'r') as f:
            loaded = yaml.load(f, Loader=yaml.Loader)
            for key in loaded.keys():
                obj[key] = loaded[key]
    except IOError:
        try:
            with open(config_file, 'w') as f:
                f.write(yaml.dump(obj, Dumper=yaml.Dumper))
        except IOError:
            pass
    return obj
