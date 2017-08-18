#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import sys
from xml.etree import ElementTree

from fastkml import kml, styles
from shapely import wkb, geos
from shapely.geometry import Point, MultiPoint
from shapely.geometry.base import BaseGeometry

import gpx_utils

__LOG = logging.getLogger('gpx_store')


def load_gpx(filename):
    """
    :param filename: The file to load the track for.
    :return Point|MultiPoint, []: The point or line read from the GPX track file.
                                  And the bounding box as a 4-tuple.
    """
    __LOG.debug("Opening GPX file: %s" % filename)
    try:
        with open(filename, 'r') as gpx_file:
            tree = ElementTree.parse(gpx_file)
            root = tree.getroot()
    except IOError as e:
        __LOG.error("Failed to read %s: %s" % (filename, e.message))
        raise e

    lats = []
    lons = []
    track_points = []

    for trk in root.findall('{http://www.topografix.com/GPX/1/1}trk'):
        for seg in trk.findall('{http://www.topografix.com/GPX/1/1}trkseg'):
            for point in seg.findall('{http://www.topografix.com/GPX/1/1}trkpt'):
                lats.append(float(point.get('lat')))
                lons.append(float(point.get('lon')))
                trk_pt = ([float(point.get('lon')), float(point.get('lat'))])
                track_points.append(trk_pt)
    for trk in root.findall('{http://www.topografix.com/GPX/1/0}trk'):
        for seg in trk.findall('{http://www.topografix.com/GPX/1/0}trkseg'):
            for point in seg.findall('{http://www.topografix.com/GPX/1/0}trkpt'):
                lats.append(float(point.get('lat')))
                lons.append(float(point.get('lon')))
                trk_pt = ([float(point.get('lon')), float(point.get('lat'))])
                track_points.append(trk_pt)

    if len(track_points) > 1:
        track = MultiPoint(track_points)
    elif len(track_points) == 1:
        track = Point(track_points[0])
    else:
        __LOG.critical("Selected GPX have no valid track points")
        print "Selected GPX have no valid track points"
        sys.exit(404)

    lats.sort()
    lons.sort()

    bbox = [lats[0], lons[0], lats[-1], lons[-1]]

    return track, bbox


def load_wkb(obj_id, admin_level, name=None):
    """
    Load a shape object from persistent store. See "obj_to_store".

    :param int obj_id: The object ID to load.
    :param int admin_level: The subdir to load from (usually the administrative level).
    :param str name: The name of the object if known.
    :return: The loaded shape.
    """
    filename = './kml/%s/%s.wkb' % (admin_level, obj_id)

    __LOG.debug('load_wkb: storing (%s/%s) -> %s' % (admin_level, obj_id, filename))
    try:
        with open(filename) as in_file:
            obj = wkb.loads(in_file.read())
        __LOG.info('load_wkb: loaded a %s with size: %s', obj.geom_type, obj.area)
        if obj.geom_type is "Polygon" or obj.geom_type is "MultiPolygon":
            __LOG.info("Retrieved Polygon for %s (%s/%s) from WKB, with area: %s",
                       gpx_utils.enforce_unicode(name), admin_level, obj_id, obj.area)
        else:
            __LOG.error("WKB not returning Polygon shape")
            return None
        if obj.area > 64800:
            __LOG.fatal("ObjectSizeError!!!")
            __LOG.fatal("%s/%s (%s) is too huge!" % (admin_level, obj_id, name))
            print
            print "ObjectSizeError!!!"
            print "%s/%s (%s) is too huge!" % (admin_level, obj_id, name)
            print
            sys.exit(127)
        elif obj.area == 0:
            __LOG.fatal("ObjectSizeError!!!")
            __LOG.fatal("%s/%s (%s) have no size." % (admin_level, obj_id, name))
            print
            print "ObjectSizeError!!!"
            print "%s/%s (%s) have no size." % (admin_level, obj_id, name)
            print
            sys.exit(126)
        return obj
    except IOError:
        # no such file, that is OK.
        return None
    except geos.ReadingError as e:
        __LOG.error('load_wkb: failed with ReadingError: %s' % e.message)
    except Exception as e:
        __LOG.error('load_wkb: failed with Exception: %s' % e.message)
    return None


def store_wkb(obj, obj_id, admin_level='2'):
    """
    Store a shape object in a way that makes it easy to reload and use for matching etc.

    :param BaseGeometry obj: The shape to store.
    :param int obj_id: The object ID to store the shape under.
    :param int admin_level: The subdir (usually the administrative level)
    :return: None
    """
    filename = './kml/%s/%s.wkb' % (admin_level, obj_id)

    __LOG.info('store_wkb: storing a %s with size: %s ', obj.geom_type, obj.area)
    with open(filename, 'w') as out_file:
        out_file.write(wkb.dumps(obj))
        out_file.close()
    __LOG.debug('store_wkb: store successful (%s/%s) -> %s' % (admin_level, obj_id, filename))


def store_kml(obj, obj_id, admin_level=0, name="unknown"):
    """
    Store a shapely geometry object as a KML file.

    :param BaseGeometry obj: The object to store
    :param int obj_id: The object ID of region.
    :param int admin_level: Admin level of region [default=0]
    :param str name: Name of the region to store in KML.
    :return:
    """
    name = gpx_utils.enforce_unicode(name).encode('ascii', 'replace')
    filename = './%s_%s.kml' % (name.replace(" ", "_"), obj_id)
    # filename = './kml/%s/%s.kml' % (admin_level, obj_id)

    __LOG.info('store_kml: storing a %s with size: %s ', obj.geom_type, obj.area)
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
            d = kml.Document(ns, str(obj_id), 'Border of {0} ({1})'.format(name, obj_id), 'Border visualization')
        else:
            d = kml.Document(ns, str(obj_id), 'Points', 'Point visualization')
        kf.append(d)
        p = kml.Placemark(ns, str(obj_id), name, '{0}'.format(name), styles=[style])
        p.geometry = obj
        d.append(p)
        fil = open(filename, 'w')
        fil.write(kf.to_string(prettyprint=True))
        fil.close()
        __LOG.debug('store_kml: store successful (%s/%s) -> %s' % (admin_level, obj_id, filename))
    except Exception as e:
        __LOG.error('store_kml: Failed to create KML %s: %s' % (filename, e.message))
