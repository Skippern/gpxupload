#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import sys

from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon
from shapely.ops import linemerge, unary_union, cascaded_union

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


def to_geometry(data):
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
    for elem in data['elements']:
        s_points = []
        if 'geometry' in elem:
            for geom in elem['geometry']:
                s_points.append((geom['lon'], geom['lat']))
        if len(s_points) > 1:
            my_ways.append(LineString(s_points))
            # __LOG.debug("Way created with %s position tuples", len(s_points))
        else:
            # __LOG.error("Way have only %s position tuples", len(s_points))
            # __LOG.debug(repr(elem))
            pass

    ###########################

    rings = []
    lines = []
    polygons = []
    for way in my_ways:
        polygons.append(way.buffer(__1MD))
        if way.is_ring and len(way.coords) > 2:
            rings.append(way)
        else:
            lines.append(way)

    ###########################

    try:
        merged_line = linemerge(my_ways)
    except Exception as e:
        __LOG.error('Exception in linemerge: %s' % e.message)
        merged_line = my_ways[0]

    if merged_line.is_ring:
        rings.append(merged_line)
    else:
        lines.append(merged_line)

    __LOG.debug("We have %s lines" % len(lines))
    __LOG.debug("We have %s rings" % len(rings))

    for line in lines:
        try:
            polygons.append(Polygon(line).buffer(__1MD))
        except Exception as e:
            # __LOG.error("P1: %s" % e.message)
            try:
                polygons.append(Polygon(LineString(line).buffer(__1MD)))
            except Exception as e:
                # __LOG.error("P2: %s" % e.message)
                try:
                    polygons.append(MultiPolygon(MultiLineString(line).buffer(__1MD)))
                except Exception as e:
                    # __LOG.error("P3: %s" % e.message)
                    pass

    out = unary_union(polygons).buffer(__1MD)

    print "Area: %s" % out.area
    print repr(out)

    return out


def build_object(obj_id, admin_level, name=u"Default"):
    #    print "Starting to build {0} ({2}/{1})".format(name.encode('ascii', 'replace'), id, al)
    __LOG.debug(u"Starting to build {0} ({3}) ({2}/{1})".format(name, obj_id, admin_level, gpx_utils.enforce_unicode(name)))

    result = gpx_loader.get_data('relation({0});out geom;'.format(obj_id))

    # Code to convert JSON data to shapely geometry
    myElements = result['elements']
    myMembers = []
    for i in myElements:
        for j in i['members']:
            myMembers.append(j)
    myWays = []
    doneRound = 0

    testNodes = []
    testWays = []
    testRelation = []
    for way in myMembers:
        doneRound = doneRound + 1

        if way['type'] != 'way':
            continue
        sPoints = []
        try:
            for i in way['geometry']:
                sPoints.append([i['lon'], i['lat']])
        except:
            __LOG.debug("Failed to read 'geometry' for way!")
            #            print way,
            # Let us try to download the way manually and create it from there.
            wID = way['ref']
            newResult = gpx_loader.get_data('way({0});out geom;'.format(wID))
            newElements = newResult['elements']
            #            print newElements
            newGeometry = []
            for elm in newElements:
                sPoints = []
                try:
                    newGeometry = elm['geometry']
                except:
                    try:
                        newGeometry = json.loads(elm)['geometry']
                    except:
                        __LOG.debug("Failed to get geometry")
                for p in newGeometry:
                    sPoints.append([p['lon'], p['lat']])
                if len(sPoints) > 1:
                    myWays.append(LineString(sPoints))
            if len(sPoints) == 0:
                # We still havn't made it, now lets try the LONG way
                __LOG.debug("Still no way, now, try to download as complete objects")
                newResult = gpx_loader.get_data('way({0});(._;>;);out body;'.format(wID))
                newElements = newResult['elements']

                for i in newElements:
                    if i['type'] == "node":
                        testNodes.append(i)
                    elif i['type'] == "way":
                        testWays.append(i)
                    else:
                        testRelation.append(i)
                for way in testWays:

                    for node in way['nodes']:
                        for i in testNodes:
                            if node == i['id']:
                                sPoints.append(([float(i['lon']), float(i['lat'])]))
        if len(sPoints) > 1:
            myWays.append(LineString(sPoints))
            __LOG.debug("Way created with %s position tuples", len(sPoints))
        else:
            __LOG.error("Way have only %s position tuples", len(sPoints))
    print ""
    lines = []
    rings = []
    newPoly = []
    print "Relation contains {0} node and {1} relation members that will not be processed".format(len(testNodes),
                                                                                                  len(testRelation))
    polygons = []
    print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
    __LOG.debug("Completed creating all elements")

    while len(myWays) > 0:
        i = myWays[0]
        polygons.append(i.buffer(gpx_utils.meter2deg(1.0)))
        if i.is_ring and len(i.coords) > 2:
            rings.append(i)
        else:
            lines.append(i)
        myWays.remove(i)
    for l in lines:
        polygons.append(l.buffer(gpx_utils.meter2deg(1.0)))
        if isinstance(l, MultiLineString):
            myWays.extend(l)
            lines.remove(l)
        else:
            myWays.append(l)
            lines.remove(l)
    mergedLine = None
    try:
        mergedLine = linemerge(myWays)
    except:
        try:
            mergedLine = myWays[0]
        except:
            try:
                mergedLine = myWays
            except:
                pass
    try:
        if mergedLine.is_ring:
            rings.append(mergedLine)
        else:
            lines.append(mergedLine)
    except:
        for i in mergedLine:
            if i.is_ring:
                rings.append(i)
            else:
                lines.append(i)
    for l in lines:
        try:
            polygons.append(Polygon(l).buffer(gpx_utils.meter2deg(1.0)))
            lines.remove(l)
        except:
            try:
                polygons.append(Polygon(LineString(l).buffer(gpx_utils.meter2deg(1.0))))
                lines.remove(l)
            except:
                try:
                    polygons.append(MultiPolygon(MultiLineString(l).buffer(gpx_utils.meter2deg(1.0))))
                    lines.remove(l)
                except:
                    pass
    __LOG.debug("We have %s rings", len(rings))
    doneRound = 0
    todoRounds = len(myWays)
    if todoRounds > 0:
        for i in myWays:
            doneRound = doneRound + 1
            try:
                polygons.append(MultiPolygon(unary_union(i).buffer(gpx_utils.meter2deg(1.0))))
            except:
                try:
                    polygons.append(MultiPolygon(cascaded_union(i).buffer(gpx_utils.meter2deg(1.0))))
                except:
                    polygons.append(Polygon(cascaded_union(i).buffer(gpx_utils.meter2deg(1.0))))
        print ""
    print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
    __LOG.debug("Start polygonize %s lines", len(lines))
    doneRound = 0
    todoRounds = len(lines)
    if todoRounds > 0:
        while len(lines) > 0:
            l = lines[0]
            doneRound = doneRound + 1
            try:
                polygons.append(cascaded_union(l).buffer(gpx_utils.meter2deg(1.0)))
            except:
                pass
            try:
                polygons.append(MultiPolygon(l.buffer(gpx_utils.meter2deg(1.0))))
            except:
                pass
            lines.remove(l)
        print ""
    print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
    __LOG.debug("Completed polygonizing lines")
    try:
        __LOG.debug("Trying to polygonize remainding lines")
        polygons.append(MultiPolygon(linemerge(lines).buffer(gpx_utils.meter2deg(1.0))))
    except:
        pass
    __LOG.info("We have created %s polygons", len(polygons))
    if (len(lines)) > 0:
        __LOG.warning("We still have %s lines that will not be handled more after this point", len(lines))
    __LOG.info("Start creating MultiPolygon of chunks")
    try:
        __LOG.debug("(Multi)Polygon unary_union of polygons")
        #        shape = MultiPolygon(unary_union(polygons)).buffer(meter2deg(10.0))
        obj = unary_union(polygons).buffer(gpx_utils.meter2deg(10.0))
        try:
            __LOG.debug("(Multi)Polygon interiors of shape")
            #            polygons.append(MultiPolygon(shape.interiors).buffer(meter2deg(10.0)))
            newPoly.append(obj.interiors.buffer(gpx_utils.meter2deg(10.0)))
        except:
            pass
        try:
            __LOG.debug("(Multi)Polygon exterior of shape")
            #            polygons.append(MultiPolygon(shape.exterior).buffer(meter2deg(10.0)))
            newPoly.append(obj.exterior.buffer(gpx_utils.meter2deg(10.0)))
        except:
            pass
    except:
        pass
    print "Shape is {0}".format(obj.geom_type)
    if obj.geom_type == "MultiPolygon":
        print "We have a {0} with {1} elements".format(obj.geom_type, len(obj))
        sPoints = []
        try:
            doneRound = 0
            todoRounds = len(obj)
            if todoRounds > 0:
                for s in obj:
                    doneRound = doneRound + 1

                    sPoints.append(s.centroid)
                    # print s.geom_type
                    try:
                        if s.exterior.is_ring:
                            rings.append(s.exterior)
                    except:
                        pass
                    try:
                        newPoly.append(s.interiors).buffer(gpx_utils.meter2deg(10.0))
                    except:
                        pass
                    try:
                        newPoly.append(s.exterior).buffer(gpx_utils.meter2deg(10.0))
                    except:
                        pass
                if len(sPoints) > 1:
                    newPoly.append(LineString(sPoints).buffer(gpx_utils.meter2deg(10.0)))
            print ""
        except:
            print "Could not make further elements"
            pass
        print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
    #    try:
    #        __LOG.debug("MultiPolygon cascaded_union of polygons")
    #        shape = MultiPolygon(cascaded_union(polygons).buffer(meter2deg(10.0)))
    #        try:
    #            __LOG.debug("MultiPolygon interiors of shape")
    #            polygons.append(MultiPolygon(shape.interiors).buffer(meter2deg(10.0)))
    #        except:
    #            pass
    #        try:
    #            __LOG.debug("MultiPolygon exterior of shape")
    #            polygons.append(MultiPolygon(shape.exterior).buffer(meter2deg(10.0)))
    #        except:
    #            pass
    #    except:
    #        pass
    #    print "Shape is {0}".format(shape.geom_type)
    if obj.geom_type == "MultiPolygon":
        print "We have a {0} with {1} elements".format(obj.geom_type, len(obj))
        try:
            doneRound = 0

            for s in obj:
                doneRound = doneRound + 1

                # print s
                try:
                    if s.exterior.is_ring:
                        rings.append(s.exterior)
                except:
                    pass
                try:
                    newPoly.append(s.interiors).buffer(gpx_utils.meter2deg(10.0))
                except:
                    pass
                try:
                    newPoly.append(s.exterior).buffer(gpx_utils.meter2deg(10.0))
                except:
                    pass
            print ""
        except:
            print "Could not make further elements"
            pass
        print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
    doneRound = 0

    for r in rings:
        doneRound = doneRound + 1

        newPoly.append(Polygon(r).buffer(gpx_utils.meter2deg(1.0)))
    if len(rings) > 0:
        print ""
    print "We now have {0} polygons".format(len(newPoly))
    try:
        __LOG.debug("Polygon unary_union of polygons")
        obj = Polygon(unary_union(newPoly)).buffer(gpx_utils.meter2deg(10.0))
    except:
        try:
            __LOG.debug("(Multi)Polygon unary_union of polygons")
            obj = MultiPolygon(unary_union(newPoly)).buffer(gpx_utils.meter2deg(10.0))
        except:
            try:
                __LOG.debug("(Multi)Polygon cascaded_union of polygons")
                obj = MultiPolygon(cascaded_union(newPoly).buffer(gpx_utils.meter2deg(10.0)))
            except:
                __LOG.debug("Polygon cascaded_union of polygons")
                obj = Polygon(cascaded_union(newPoly).buffer(gpx_utils.meter2deg(10.0)))
    __LOG.debug("Finally all elements in place, lets make the shape")
    print "Finally all elements in place, lets make the shape"
    try:
        __LOG.debug("Polygon exterior of shape")
        obj = Polygon(obj.exterior).buffer(gpx_utils.meter2deg(10.0))
    except:
        try:
            __LOG.debug("MultiPolygon exterior of shape")
            obj = MultiPolygon(obj.exterior).buffer(gpx_utils.meter2deg(10.0))
        except:
            __LOG.error("Failed to create (Multi)Polygon from extreriors of shape")
    try:
        __LOG.info("Completed creating %s of collected chunks with size: %s", str(obj.geom_type), str(obj.area))
    except:
        __LOG.debug("Completed creating (MultiPolygon) of collected chunks")

    print u"Shape {0} is created as a valid {1} with area: {2}".format(name, obj.geom_type, obj.area)
    if obj.area > 64800:
        print "ObjectSizeError!!!"
        print u"{0}/{1} ({2}) is too huge, and cannot be accepted!".format(admin_level, name, obj_id)
        sys.exit(666)

    return obj


def load_object(obj_id, admin_level, name):
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

    __LOG.info(u"Starting to build %s/%s (%s)" % (admin_level, obj_id, name))

    obj = build_object(obj_id, admin_level, name)

    gpx_store.store_wkb(obj, obj_id, admin_level)
    return obj
