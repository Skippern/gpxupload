#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import os
import sys
from xml.etree import ElementTree

from fastkml import kml, styles
from shapely import wkb, geos
from shapely.geometry import Point, MultiPoint
from shapely.geometry.base import BaseGeometry

import gpx_utils

__LOG = logging.getLogger('gpx_store')


cache_dir = os.environ['HOME'] + '/.cache/gpx'


def init_cache():
    for i in range(2, 11):
        for t in ['geos', 'tags', 'rels']:
            d = '%s/%s/%s' % (cache_dir, t, i)
            try:
                os.makedirs(d)
            except OSError:
                pass


def clear_cache(types = None):
    if types is None:
        types = ['geos', 'tags', 'rels']
    init_cache()
    for t in types:
        for lvl in range(2, 11):
            d = '%s/%s/%s' % (cache_dir, t, lvl)
            for f in os.listdir(d):
                os.remove('%s/%s' % (d, f))


def __mk_track(track_points):
    if len(track_points) > 1:
        return MultiPoint(track_points)
    elif len(track_points) == 1:
        return Point(track_points[0])
    else:
        __LOG.critical(u'Selected GPX have no valid track points')
        print u'Selected GPX have no valid track points'
        sys.exit(404)


def load_gpx(filename):
    """
    :param filename: The file to load the track for.
    :return [Point|MultiPoint], BBox:
            The point or line read from the GPX track file.
            And the bounding box as a 4-tuple.
    """
    __LOG.debug(u'Opening GPX file: %s' % filename)
    try:
        with open(filename, 'r') as gpx_file:
            tree = ElementTree.parse(gpx_file)
            root = tree.getroot()
    except IOError as e:
        __LOG.error(u'Failed to read %s: %s' % (filename, e.message))
        raise e

    tracks = []

    for trk in root.findall('{http://www.topografix.com/GPX/1/1}trk'):
        for seg in trk.findall('{http://www.topografix.com/GPX/1/1}trkseg'):
            track_points = []
            for point in seg.findall('{http://www.topografix.com/GPX/1/1}trkpt'):
                trk_pt = ([float(point.get('lon')), float(point.get('lat'))])
                track_points.append(trk_pt)
            tracks.append(__mk_track(track_points))

    for trk in root.findall('{http://www.topografix.com/GPX/1/0}trk'):
        for seg in trk.findall('{http://www.topografix.com/GPX/1/0}trkseg'):
            track_points = []
            for point in seg.findall('{http://www.topografix.com/GPX/1/0}trkpt'):
                trk_pt = ([float(point.get('lon')), float(point.get('lat'))])
                track_points.append(trk_pt)
            tracks.append(__mk_track(track_points))

    return tracks


def load_wkb(obj_id, admin_level, name=None):
    """
    Load a shape object from persistent store. See 'obj_to_store'.

    :param int obj_id: The object ID to load.
    :param int admin_level: The subdir to load from (usually the administrative level).
    :param str name: The name of the object if known.
    :return: The loaded shape.
    """
    filename = '%s/geos/%s/%s.wkb' % (cache_dir, admin_level, obj_id)

    __LOG.debug(u'load_wkb: storing (%s/%s) -> %s' % (admin_level, obj_id, filename))
    try:
        with open(filename) as in_file:
            obj = wkb.loads(in_file.read())
        __LOG.info(u'load_wkb: loaded a %s with size: %s', obj.geom_type, obj.area)
        if obj.geom_type is 'Polygon' or obj.geom_type is 'MultiPolygon':
            __LOG.info(u'Retrieved Polygon for %s (%s/%s) from WKB, with area: %s',
                       gpx_utils.enforce_unicode(name), admin_level, obj_id, obj.area)
        else:
            __LOG.error(u'WKB not returning Polygon shape')
            return None
        if obj.area > 64800:
            __LOG.fatal(u'ObjectSizeError!!!')
            __LOG.fatal(u'%s/%s (%s) is too huge!' % (admin_level, obj_id, name))
            print
            print u'ObjectSizeError!!!'
            print u'%s/%s (%s) is too huge!' % (admin_level, obj_id, name)
            print
            sys.exit(127)
        elif obj.area == 0:
            __LOG.fatal(u'ObjectSizeError!!!')
            __LOG.fatal(u'%s/%s (%s) have no size.' % (admin_level, obj_id, name))
            print
            print u'ObjectSizeError!!!'
            print u'%s/%s (%s) have no size.' % (admin_level, obj_id, name)
            print
            sys.exit(126)
        return obj
    except IOError:
        # no such file, that is OK.
        return None
    except geos.ReadingError as e:
        __LOG.error(u'load_wkb: failed with ReadingError: %s' % e.message)
    except Exception as e:
        __LOG.error(u'load_wkb: failed with Exception: %s' % e.message)
    return None


def store_wkb(obj, obj_id, admin_level):
    """
    Store a shape object in a way that makes it easy to reload and use for matching etc.

    :param BaseGeometry obj: The shape to store.
    :param int obj_id: The object ID to store the shape under.
    :param int admin_level: The subdir (usually the administrative level)
    :return: None
    """
    filename = '%s/geos/%s/%s.wkb' % (cache_dir, admin_level, obj_id)

    __LOG.info(u'store_wkb: storing a %s with size: %s ', obj.geom_type, obj.area)
    with open(filename, 'w') as out_file:
        out_file.write(wkb.dumps(obj))
        out_file.close()
    __LOG.debug(u'store_wkb: store successful (%s/%s) -> %s' % (admin_level, obj_id, filename))


def load_rels(obj_id, obj_level, admin_level):
    filename = '%s/rels/%s/%s_%s.json' % (cache_dir, obj_level, obj_id, admin_level)
    try:
        with open(filename, 'r') as in_file:
            return json.loads(in_file.read())
    except IOError:
        # no such file.
        return None


def store_rels(rels, obj_id, obj_level, admin_level):
    filename = '%s/rels/%s/%s_%s.json' % (cache_dir, obj_level, obj_id, admin_level)
    with open(filename, 'w') as out_file:
        out_file.write(json.dumps(rels, sort_keys=True, indent=2))
        out_file.write('\n')
        out_file.flush()


def load_tags(obj_id, admin_level):
    filename = '%s/tags/%s/%s.json' % (cache_dir, admin_level, obj_id)
    try:
        with open(filename, 'r') as in_file:
            return json.loads(in_file.read())
    except IOError:
        # no such file.
        return None


def store_tags(tags, obj_id, admin_level):
    filename = '%s/tags/%s/%s.json' % (cache_dir, admin_level, obj_id)
    with open(filename, 'w') as out_file:
        out_file.write(json.dumps(tags, sort_keys=True, indent=2))
        out_file.write('\n')
        out_file.flush()


def store_kml(obj, obj_id, admin_level, name=u'unknown'):
    """
    Store a shapely geometry object as a KML file.

    :param BaseGeometry obj: The object to store
    :param int obj_id: The object ID of region.
    :param int admin_level: Admin level of region [default=0]
    :param str|unicode name: Name of the region to store in KML.
    :return:
    """
    ascii_name = gpx_utils.enforce_unicode(name).encode('ascii', 'replace')
    filename = './%s_%s.kml' % (ascii_name.replace(' ', '_'), obj_id)
    __LOG.info(u'store_kml: storing a %s with size: %s ', obj.geom_type, obj.area)
    try:
        ns = '{http://www.opengis.net/kml/2.2}'
        sls = styles.LineStyle(color='ffff0000')
        sas = styles.PolyStyle(color='5500ff00')
        sps = styles.BalloonStyle(bgColor='ff0000ff')
        style = styles.Style(styles=[sls, sas, sps])
        kf = kml.KML(ns)
        if obj.geom_type == 'LineString' or obj.geom_type == 'MultiLineString' or obj.geom_type == 'LinearRing':
            d = kml.Document(ns, str(obj_id), 'Traces', 'GPX Visualization')
        elif obj.geom_type == 'Polygon' or obj.geom_type == 'MultiPolygon':
            d = kml.Document(ns, str(obj_id), 'Border of {0} ({1})'.format(ascii_name, obj_id), 'Border visualization')
        else:
            d = kml.Document(ns, str(obj_id), 'Points', 'Point visualization')
        kf.append(d)
        p = kml.Placemark(ns, str(obj_id), ascii_name, '{0}'.format(ascii_name), styles=[style])
        p.geometry = obj
        d.append(p)
        fil = open(filename, 'w')
        fil.write(kf.to_string(prettyprint=True))
        fil.flush()
        fil.close()
        __LOG.debug(u'store_kml: store successful (%s/%s) -> %s' % (admin_level, obj_id, filename))
    except Exception as e:
        __LOG.error(u'store_kml: Failed to create KML %s: %s' % (filename, e.message))
