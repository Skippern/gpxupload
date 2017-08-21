#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon
from shapely.ops import linemerge, unary_union

import gpx_loader
import gpx_store
import gpx_utils

__LOG = logging.getLogger('gpx_data')
__1MD = gpx_utils.meter2deg(1.0)

__DEBUGGING = False
__NAME_LANGUAGES = ['en', 'no', 'pt']


def get_name(data):
    """
    :param dict data: relation data
    :return unicode: relation name
    """
    rel_id = data['id']
    try:
        rel_name = data['tags']['name']
    except KeyError:
        try:
            rel_name = data['tags']['name:en']
        except KeyError:
            rel_name = str(rel_id)
    return gpx_utils.enforce_unicode(rel_name)


def get_tags(tags):
    """
    :param dict tags: Tags dictionary from overpass data response.
    :return []: list of tags
    """
    out = []
    if __DEBUGGING:
        try:
            out.append(gpx_utils.enforce_unicode(tags['admin_level']))
        except KeyError:
            pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['name']))
    except KeyError:
        pass

    for lang in __NAME_LANGUAGES:
        try:
            out.append(gpx_utils.enforce_unicode(tags['name:%s' % lang]))
        except KeyError:
            pass
        try:
            out.append(gpx_utils.enforce_unicode(tags['official_name:%s' % lang]))
        except KeyError:
            pass
        try:
            out.append(gpx_utils.enforce_unicode(tags['alt_name:%s' % lang]))
        except KeyError:
            pass
        try:
            out.append(gpx_utils.enforce_unicode(tags['long_name:%s' % lang]))
        except KeyError:
            pass

    try:
        out.append(gpx_utils.enforce_unicode(tags['official_name']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['short_name']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['long_name']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['alt_name']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['loc_name']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['old_name']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['ISO3166-1']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['ISO3166-1:alpha2']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['ISO3166-1:alpha3']))
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['ISO3166-2']))
    except KeyError:
        pass
    try:
        is_in_all = gpx_utils.enforce_unicode(tags['is_in'])
        for is_in in is_in_all.split(';'):
            out.append(is_in)
    except KeyError:
        pass
    try:
        out.append(gpx_utils.enforce_unicode(tags['is_in:continent']))
    except KeyError:
        pass

    return out


def geojson_to_geometry(data):
    """
    NOTE: Incomplete and buggy!

    But this is meant to replace the build_object function below.

    :param dict data: Json data result from overpass
    :return BaseGeometry: Shapely geometry (Polygon or MultiPolygon).
    """
    if data is None:
        return None

    ###########################
    ##
    my_ways = []

    for feature in data['features']:
        if 'geometry' in feature:
            my_ways.append(LineString(feature['geometry']['coordinates']))

    ###########################

    rings = []
    lines = []

    # Split between already fixed rings, and lines we need to work on
    for way in my_ways:
        # polygons.append(way)
        if way.is_ring and len(way.coords) > 2:
            rings.append(way)
        else:
            lines.append(way)

    ###########################

    polygons = []
    # Try to merge lines and generate polygons out of the merged lines.
    if len(lines) > 1:
        try:
            merged_line = linemerge(lines)
            if merged_line.is_ring or isinstance(merged_line, MultiLineString):
                polygons.append(merged_line.buffer(__1MD))
            else:
                raise Exception("Unknown linemerge result: ", repr(merged_line))
        except Exception as e:
            __LOG.error('Exception in linemerge: %s' % e.message)
            # but continue.
    elif len(lines) == 1:
        # or ? polygons.append(Polygon(lines[0].buffer(__1MD)))
        polygons.append(lines[0].buffer(__1MD))

    # Try to make polygons our of the rings.
    for ring in rings:
        try:
            polygons.append(Polygon(ring).buffer(__1MD))
        except Exception as e:
            __LOG.error("Unable to make polygon from ring: " % e.message)
            # but continue

    # Merge all the polygons!!!!
    shape = unary_union(polygons).buffer(__1MD)

    # Remake the polygons into exterior polygons (contains whatever is inside it).
    if isinstance(shape, MultiPolygon):
        polygons = []
        for poly in shape:
            polygons.append(Polygon(poly.exterior).buffer(__1MD))
        shape = unary_union(polygons).buffer(__1MD)
    elif isinstance(shape, Polygon):
        shape = Polygon(shape.exterior).buffer(__1MD)
    else:
        raise Exception("Unknown polygon type: %s" % shape.type)
    return shape


def load_geo_shape(obj_id, admin_level, name):
    """
    Load object with ID either from object store or from overpass (and store in object store).

    :param int obj_id: The object relation ID to load.
    :param int admin_level: The administrative level of relation.
    :param unicode name: The name of the object (mostly for debugging).
    :return: The loaded geometrical shape
    """
    obj = gpx_store.load_wkb(obj_id, admin_level)
    if obj is not None:
        return obj

    __LOG.info(u"Starting to build %s/%s: %s" % (admin_level, obj_id, name))

    data = gpx_loader.get_geometry_for_relation(obj_id, admin_level)
    obj = geojson_to_geometry(data)

    gpx_store.store_wkb(obj, obj_id, admin_level)
    return obj
