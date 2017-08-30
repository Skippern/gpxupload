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
        merged_line = linemerge(lines)
        if merged_line.is_ring or isinstance(merged_line, MultiLineString) or isinstance(merged_line, LineString):
            polygons.append(merged_line.buffer(__1MD))
        else:
            raise "Unknown linemerge result: %s" % repr(merged_line)
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

    data = gpx_loader.get_geometry_for_relation(obj_id)
    obj = geojson_to_geometry(data)

    gpx_store.store_wkb(obj, obj_id, admin_level)
    return obj


def load_relations(parent_obj_id, parent_admin_level, admin_level):
    obj = gpx_store.load_rels(parent_obj_id, parent_admin_level, admin_level)
    if obj is not None:
        return obj

    obj = gpx_loader.get_relations_in_object(parent_obj_id, admin_level)
    gpx_store.store_rels(obj, parent_obj_id, parent_admin_level, admin_level)
    return obj


def load_tags(obj_id, admin_level):
    obj = gpx_store.load_tags(obj_id, admin_level)
    if obj is not None:
        return obj

    obj = gpx_loader.get_tags_for_relation(obj_id)
    gpx_store.store_tags(obj, obj_id, admin_level)
    return obj
