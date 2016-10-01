#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test the GPX File for coverage, so it is tagged correctly when uploaded

import sys
import os
import xml.etree.ElementTree as etree
import overpass
import logging
import json
from fastkml import kml, styles
#from shapely import speedups
from shapely.geometry import shape, mapping, LineString, MultiLineString, Point, MultiPoint, Polygon, MultiPolygon, LinearRing, asShape
from shapely.geometry.collection import GeometryCollection
from shapely.ops import linemerge, polygonize, cascaded_union, unary_union
from shapely.validation import explain_validity
from shapely.wkt import loads as wkt_loads, dumps as wkt_dumps
from shapely.wkb import loads as wkb_loads, dumps as wkb_dumps
from unidecode import unidecode
from math import cos, sin, radians, degrees
import keytree
import datetime
import time
import requests
logger = logging.getLogger("gpxupload")
#logging.basicConfig(filename="./kml/GPXUploadEventLog.log", level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s - %(message)s",datefmt="%Y/%m/%d %H:%M:%S:")
logging.basicConfig(filename="./kml/GPXUploadEventLog.log", level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s - %(message)s",datefmt="%Y/%m/%d %H:%M:%S:")
overpassServer = "http://overpass-api.de/api/interpreter" # Default
#overpassServer = "http://overpass.osm.rambler.ru/cgi/interpreter"
#overpassServer = "http://api.openstreetmap.fr/oapi/interpreter"
#overpassServer = "http://overpass.osm.ch/api/interpreter"
api = overpass.API(timeout=900, endpoint=overpassServer)

#if speedups.available:
if False:
    speedups.enable()
    logger.info("Speedups enabled\n")
else:
    logger.debug("Speedups not enabled, executing default\n")

no_upload = True
no_kml = False
debuging = False

lang = [ 'en', 'pt', 'no' ]
tags = []
SQKM = ( (60.0 * 1.852) * (60.0 * 1.852) )
result = ""
name = u"?"
file = ""
nullShape = Point(0.0,0.0).buffer(0.0000001)

def clean(i):
    codecList = [ 'ascii', 'iso-8859-2', 'iso-8859-1', 'iso-8859-3', 'iso-8859-4', 'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8', 'iso-8859-9', 'iso-8859-10', 'iso-8859-11', 'iso-8859-12', 'iso-8859-13', 'iso-8859-14', 'iso-8859-15', 'iso-8859-16', 'mac-latin2', 'big5', 'cp037', 'cp1006', 'cp1026', 'cp1140', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256', 'cp1257', 'cp1258', 'cp424', 'cp437', 'cp500', 'cp720', 'cp737', 'cp755', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'euc_jis-2004', 'gb18030', 'gb2312', 'gbk', 'hp-roman8', 'mac_arabic', 'mac_centeuro', 'mac_croatian', 'mac_cyrillic', 'mac_farsi', 'mac_greek', 'mac_iceland', 'mac_roman', 'mac_romanian', 'mac_turkish', 'palmos', 'ptcp154', 'tis_620', 'mbcs', 'utf-8' ]
    for codec in codecList:
        try:
            i = i.encode(codec).decode('utf8')
            break
        except:
            pass
    return i

def deg2meter(deg):
    return (deg * (60.0 * 1852.0))
def meter2deg(meter):
    return (meter / (1852.0 * 60.0 ))

def obj_from_store(id, subdir="2"):
    shape = nullShape
#    return shape
    with open(u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".wkb") as f:
        shape = wkb_loads(f.read())
#    tree = etree.parse(open(u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".kml"))
#    kmlns = tree.getroot().tag.split('}')[0][1:]
#    placemarks = tree.findall('*/{%s}Placemark' % kmlns)
#    myObject = []
#    for i in placemarks:
##        p0 = i
##        print i, i.geom_type
#        try:
#            f = keytree.feature(i)
#            myObject.append(asShape(f.geometry))
#        except:
#            try:
#                myObject.append(asShape(wkb.loads(i)))
#            except:
#                pass
##    p0 = placemarks[0]
##    f = keytree.feature(p0)
##    shape = asShape(f.geometry)
##    shape = unary_union(myObject).buffer(deg2meter(0.1))
##    fil = open(u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".wkb", 'r')
##    shape = wkt_loads(fil)
##    shape = to_shape(wkb_loads(fil))
##    fil.close()
    logger.info("obj_from_store have successfully created a %s with size: %s", shape.geom_type, shape.area)
#    print "{0} successfully loaded from KML".format(shape.geom_type)
    return shape

def mk_kml(ob, id, name, subdir="0"):
    if no_kml:
        return
    logger.debug("Creating KML")
    filename = u"./kml/000_Default.kml"
    name = clean(name).encode('ascii', 'replace')
    try:
        ns = '{http://www.opengis.net/kml/2.2}'
        sls = styles.LineStyle(color="ffff0000")
        sas = styles.PolyStyle(color="5500ff00")
        sps = styles.BalloonStyle(bgColor="ff0000ff")
        style = styles.Style(styles = [sls, sas, sps])
        kf = kml.KML(ns)
        if ob.geom_type == "LineString" or ob.geom_type == "MultiLineString" or ob.geom_type == "LinearRing":
            d = kml.Document(ns, str(id), "Traces", 'GPX Visualization')
        elif ob.geom_type == "Polygon" or ob.geom_type == "MultiPolygon":
            d = kml.Document(ns, str(id), 'Border of {0} ({1})'.format(name, id), 'Border visualization')
        else:
            d = kml.Document(ns, str(id), "Points", 'Point visualization')
        kf.append(d)
        p = kml.Placemark(ns, str(id), name, '{0}'.format(name), styles = [style])
        p.geometry = ob
        d.append(p)
        if subdir == "0":
            filename = u"./kml/"+unicode(id)+u"_"+name.replace(" ", "_")+u".kml"
        else:
            filename = u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".kml"
#            filename = u"./kml/"+unicode(subdir)+u"/"+name.replace(" ", "_")+u"_"+unicode(id)+u".kml"
        fil = open(filename, 'w')
        fil.write(kf.to_string(prettyprint=True))
        fil.close()
        logger.info("KML Saved in %s", filename)
    except:
        logger.error("Failed to create KML: %s", filename)
        return
        try:
            logger.debug("Creating SVG")
            if subdir == "0":
                filename = "./kml/"+str(id)+"_"+name.replace(" ", "_")+".svg"
            else:
                filename = "./kml/"+subdir+"/"+name.replace(" ", "_")+"_"+str(id)+".svg"
            fil = open(filename, 'w')
            fil.write(ob.svg())
            fil.close()
            logger.info("SVG Saved in %s", filename)
        except:
            logger.error("Failed to create SVG")
    try:
        # Make WKT or WKB file
        if subdir != "0":
            logger.debug("Preparing for WKB file")
            filename = u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".wkb"
            fil = open(filename, 'w')
            #print ob, wkb_dumps(ob)
            fil.write(wkb_dumps(ob))
            fil.close()
    except:
        pass
#    try:
#        # Make WKT or WKB file
#        if subdir != "0":
#            logger.debug("Preparing for WKT file")
#            filename = u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".wkt"
#            fil = open(filename, 'w')
#            #print ob, wkt_dumps(ob)
#            fil.write(wkt_dumps(ob))
#            fil.close()
#    except:
#        pass

def remove_duplicates(values):
    output = []
    seen = set()
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output

def swap(a, b):
    return b, a

def get_data_bbox(minlat, minlon, maxlat, maxlon, al=2):
    result = ""
    if minlat == maxlat:
        logger.critical("ERROR: Latitude %s equal %s - EXPANDING", str(minlat), str(maxlat))
        minlat = minlat - 0.0000001
        maxlat = maxlat + 0.0000001
    if minlon == maxlon:
        logger.critical("ERROR: Longitude %s equal %s - EXPANDING", str(minlon), str(maxlon))
        minlon = minlon - 0.0000001
        maxlon = maxlon + 0.0000001
    if minlat > maxlat:
        logger.error("ERROR: Latitude %s greater than %s - SWAPPING", str(minlat), str(maxlat))
        minlat, maxlat = swap(minlat, maxlat)
    if minlon > maxlon:
        logger.error("ERROR: Longitude %s greater than %s - SWAPPING", str(minlon), str(maxlon))
        minlon, maxlon = swap(minlon, maxlon)
    searchString = 'is_in;relation["type"="boundary"]["boundary"="administrative"]["admin_level"="{4}"]({0},{1},{2},{3});out tags;'.format(minlat,minlon,maxlat,maxlon, al)
    return get_data(searchString)

def get_data_relation(relationID, al=3):
    relationID = relationID + 3600000000
    #    searchString = 'is_in;relation["type"="boundary"]["boundary"="administrative"]["admin_level"="{0}"]({1});out tags;'.format(al, relationID)
    searchString = 'relation(area:{1})["type"="boundary"]["boundary"="administrative"]["admin_level"="{0}"];out tags;'.format(al, relationID)
    return get_data(searchString)

def get_tags(element):
    myTags = element['tags']
    if debuging:
        try:
            string = clean(myTags['admin_level'])
            tags.append(string)
        except:
            pass
    try:
        string = clean(myTags['name'])
        tags.append(string)
    except:
        pass
    for i in lang:
        try:
            test = 'name:{0}'.format(i)
            string = clean(myTags[test])
            tags.append(string)
        except:
            pass
        try:
            test = 'official_name:{0}'.format(i)
            string = clean(myTags[test])
            tags.append(string)
        except:
            pass
        try:
            test = 'alt_name:{0}'.format(i)
            string = clean(myTags[test])
            for j in string.split(";"):
                tags.append(j)
        except:
            pass
        try:
            test = 'long_name:{0}'.format(i)
            string = clean(myTags[test])
            tags.append(string)
        except:
            pass
    try:
        string = clean(myTags['official_name'])
        tags.append(string)
    except:
        pass
    try:
        string = clean(myTags['short_name'])
        tags.append(string)
    except:
        pass
    try:
        string = clean(myTags['long_name'])
        tags.append(string)
    except:
        pass
    try:
        string = clean(myTags['alt_name'])
        for j in string.split(";"):
            tags.append(j)
    except:
        pass
    try:
        string = clean(myTags['loc_name'])
        tags.append(string)
    except:
        pass
    try:
        string = clean(myTags['old_name'])
        for j in string.split(";"):
            tags.append(j)
    except:
        pass
    try:
        string = clean(myTags['ISO3166-1'])
        tags.append(string)
    except:
        pass
    try:
        string = clean(myTags['ISO3166-1:alpha2'])
        tags.append(string)
    except:
        pass
    try:
        string = clean(myTags['ISO3166-1:alpha3'])
        tags.append(string)
    except:
        pass
    try:
        string = clean(myTags['ISO3166-2'])
        tags.append(string)
    except:
        pass
    try:
        string = clean(myTags['is_in:continent'])
        tags.append(string)
    except:
        pass
#    print tags

def build_object(id,al, name=u"Default"):
    polygons = []
    shape = nullShape
    try:
        shape = obj_from_store(id, al)
        if shape.geom_type == "Polygon" or shape.geom_type == "MultiPolygon":
            logger.info("Retrieved Polygon for %s (%s) from KML, with area: %s", clean(name), id, shape.area)
#            mk_kml(shape, id, name, al)
            if shape.area > 64800:
                print "ObjectSizeError!!!"
                print "{0}/{1} ({2}) is too huge, and cannot be accepted, verify where in the code this error comes from and try again!".format(al, name.encode('ascii', 'replace'), id)
                return nullShape
                sys.exit(666)
            elif shape.area == 0:
                print "ObjectSizeError!!!"
                print "{0}/{1} ({2}) have no size.".format(al, name.encode('ascii', 'replace'), id)
            elif shape == nullShape:
                print "obj_from_store returned nullShape"
            else:
#                print "Built from KML"
                return shape
#        polygons.append(shape)
        logger.error("KML not returning Polygon shape")
    except IOError:
        # File doesn't exist, silently passing
        pass
#    except xml.etree.ElementTree.ParseError:
    except etree.ParseError:
        # Something went wrong in Parsing the file
        pass
    except:
        logger.debug("Not able to reconstruct KML")
        raise
    print "Starting to build {0} ({2}/{1})".format(name.encode('ascii', 'replace'), id, al)
    shape = nullShape
    myID = id + 3600000000
    result = False
    while result == False:
#        result = get_data('relation(area:{1})["type"="boundary"]["boundary"="administrative"]["admin_level"="{0}"];out geom;'.format(al, myID))
        result = get_data('relation({0});out geom;'.format(id))
        time.sleep(30)
    if debuging:
        print result
    # Code to convert JSON data to shapely geometry
    myElements = json.loads(json.dumps(result))['elements']
    myMembers = []
    for i in myElements:
        for j in i['members']:
            myMembers.append(j)
    myWays = []
    doneRound = 0
    todoRounds = len(myMembers)
    for way in myMembers:
        doneRound = doneRound + 1
        print "\rProcessing {0} of {1} members".format(doneRound, todoRounds), '\r',
        sys.stdout.flush()
        if way['type'] != 'way':
            continue
        sPoints = []
        try:
            for i in way['geometry']:
                sPoints.append( [ i['lon'], i['lat'] ] )
        except:
            logger.debug("Failed to read 'geometry' for way!")
#            print way,
            # Let us try to download the way manually and create it from there.
            newResult = False
            wID = way['ref']
            while newResult == False:
                newResult = get_data('way({0});out geom;'.format(wID))
            newElements = json.loads(json.dumps(newResult))['elements']
#            print newElements
            newGeometry = []
            for elm in newElements:
                sPoints = []
                try:
                    newGeometry = json.loads(json.dumps(elm))['geometry']
                except:
                    try:
                        newGeometry = json.loads(elm)['geometry']
                    except:
                        logger.debug("Failed to get geometry")
                for p in newGeometry:
                    sPoints.append( [ p['lon'], p['lat'] ] )
                if len(sPoints) > 1:
                    myWays.append(LineString(sPoints))
            if len(sPoints) == 0:
                # We still havn't made it, now lets try the LONG way
                logger.debug("Still no way, now, try to download as complete objects")
                newResult = False
                while newResult == False:
                    newResult = get_data('way({0});(._;>;);out body;'.format(wID))
                newElements = json.loads(json.dumps(newResult))['elements']
                testNodes = []
                testWays = []
                no_double_testing_please = set()
                for i in newElements:
                    if i['type'] == "node":
                        testNodes.append(i)
                    elif i['type'] == "way":
                        testWays.append(i)
                for way in testWays:
                    wID = way['id']
                    for node in way['nodes']:
                        for i in testNodes:
                            if node == i['id']:
                                sPoints.append( ([ float(i['lon']), float(i['lat']) ]) )
        if len(sPoints) > 1:
            myWays.append(LineString(sPoints))
            logger.debug("Way created with %s position tuples", len(sPoints))
        else:
            logger.error("Way have only %s position tuples", len(sPoints))
    print ""
    print "We now have {0} polygons".format(len(polygons))
    logger.debug("Completed creating all elements")
    lines = []
    rings = []
#    polygons = []
    while len(myWays) > 0:
        i = myWays[0]
        polygons.append(i.buffer(meter2deg(1.0)))
        if i.is_ring and len(i.coords) > 2:
            rings.append(i)
        else:
            lines.append(i)
        myWays.remove(i)
    for l in lines:
        polygons.append(l.buffer(meter2deg(1.0)))
        if isinstance(l, MultiLineString):
            myWays.extend(l)
            lines.remove(l)
        else:
            myWays.append(l)
            lines.remove(l)
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
            polygons.append(Polygon(l).buffer(meter2deg(1.0)))
            lines.remove(l)
        except:
            try:
                polygons.append(Polygon(LineString(l).buffer(meter2deg(1.0))))
                lines.remove(l)
            except:
                try:
                    polygons.append(MultiPolygon(MultiLineString(l).buffer(meter2deg(1.0))))
                    lines.remove(l)
                except:
                    pass
    logger.debug("We have %s rings", len(rings))
    doneRound = 0
    todoRounds = len(myWays)
    for i in myWays:
        doneRound = doneRound + 1
        print "\rProcessing {0} of {1} ways".format(doneRound, todoRounds), '\r',
        sys.stdout.flush()
        try:
            polygons.append( MultiPolygon(unary_union(i).buffer(meter2deg(1.0))) )
        except:
            try:
                polygons.append( MultiPolygon(cascaded_union(i).buffer(meter2deg(1.0))) )
            except:
                polygons.append( Polygon(cascaded_union(i).buffer(meter2deg(1.0))) )
    print ""
    print "We now have {0} polygons".format(len(polygons))
    logger.debug("Start polygonize %s lines", len(lines))
    doneRound = 0
    todoRounds = len(lines)
    while len(lines) > 0:
        l = lines[0]
        doneRound = doneRound + 1
        print "\rProcessing {0} of {1} lines".format(doneRound, todoRounds), '\r',
        sys.stdout.flush()
        try:
            polygons.append( cascaded_union(l).buffer(meter2deg(1.0)) )
        except:
            pass
        try:
            polygons.append(MultiPolygon(l.buffer(meter2deg(1.0))))
        except:
            pass
        lines.remove(l)
    print ""
    print "We now have {0} polygons".format(len(polygons))
    logger.debug("Completed polygonizing lines")
    try:
        logger.debug("Trying to polygonize remainding lines")
        polygons.append(MultiPolygon(linemerge(lines).buffer(meter2deg(1.0))))
    except:
        pass
    logger.info("We have created %s polygons", len(polygons))
    if (len(lines)) > 0:
        logger.warning("We still have %s lines that will not be handled more after this point", len(lines))
    logger.info("Start creating MultiPolygon of chunks")
    try:
        logger.debug("MultiPolygon unary_union of polygons")
        shape = MultiPolygon(unary_union(polygons)).buffer(meter2deg(10.0))
        try:
            logger.debug("MultiPolygon interiors of shape")
            polygons.append(MultiPolygon(shape.interiors).buffer(meter2deg(10.0)))
        except:
            pass
        try:
            logger.debug("MultiPolygon exterior of shape")
            polygons.append(MultiPolygon(shape.exterior).buffer(meter2deg(10.0)))
        except:
            pass
    except:
        pass
    print "Shape is {0}".format(shape.geom_type)
    if shape.geom_type == "MultiPolygon":
        print "We have a {0} with {1} elements".format(shape.geom_type, len(shape))
        try:
            doneRound = 0
            todoRounds = len(shape)
            for s in shape:
                doneRound = doneRound + 1
                print "\rProcessing {0} of {1} elements".format(doneRound, todoRounds), '\r',
                sys.stdout.flush()
                #print s
                try:
                    polygons.append(s.interiors).buffer(meter2deg(10.0))
                except:
                    pass
                try:
                    polygons.append(s.exterior).buffer(meter2deg(10.0))
                except:
                    pass
            print ""
        except:
            print "Could not make further elements"
            pass
        print "We now have {0} polygons".format(len(polygons))
    try:
        logger.debug("MultiPolygon cascaded_union of polygons")
        shape = MultiPolygon(cascaded_union(polygons).buffer(meter2deg(10.0)))
        try:
            logger.debug("MultiPolygon interiors of shape")
            polygons.append(MultiPolygon(shape.interiors).buffer(meter2deg(10.0)))
        except:
            pass
        try:
            logger.debug("MultiPolygon exterior of shape")
            polygons.append(MultiPolygon(shape.exterior).buffer(meter2deg(10.0)))
        except:
            pass
    except:
        pass
    print "Shape is {0}".format(shape.geom_type)
    if shape.geom_type == "MultiPolygon":
        print "We have a {0} with {1} elements".format(shape.geom_type, len(shape))
        try:
            doneRound = 0
            todoRounds = len(shape)
            for s in shape:
                doneRound = doneRound + 1
                print "\rProcessing {0} of {1} elements".format(doneRound, todoRounds), '\r',
                sys.stdout.flush()
                #print s
                try:
                    polygons.append(s.interiors).buffer(meter2deg(10.0))
                except:
                    pass
                try:
                    polygons.append(s.exterior).buffer(meter2deg(10.0))
                except:
                    pass
            print ""
        except:
            print "Could not make further elements"
            pass
        print "We now have {0} polygons".format(len(polygons))
    try:
        logger.debug("MultiPolygon unary_union of polygons")
        shape = MultiPolygon(unary_union(polygons)).buffer(meter2deg(10.0))
    except:
        logger.debug("MultiPolygon cascaded_union of Polygons")
        try:
            shape = MultiPolygon(cascaded_union(polygons).buffer(meter2deg(10.0)))
        except:
            shape = Polygon(cascaded_union(polygons).buffer(meter2deg(10.0)))
    doneRound = 0
    todoRounds = len(rings)
    for r in rings:
        doneRound = doneRound + 1
        print "\rProcessing {0} of {1} rings".format(doneRound, todoRounds), '\r',
        sys.stdout.flush()
        polygons.append(Polygon(r).buffer(meter2deg(1.0)))
    if len(rings) > 0:
        print ""
    print "We now have {0} polygons".format(len(polygons))
    try:
        logger.debug("MultiPolygon exterior of shape")
        shape = Polygon(shape.exterior).buffer(meter2deg(10.0))
    except:
        try:
            shape = MultiPolygon(shape.exterior).buffer(meter2deg(10.0))
        except:
            logger.error("Failed to create MultiPolygon from extreriors of shape")
    try:
        logger.info("Completed creating %s of collected chunks with size: %s", str(shape.geom_type), str(shape.area))
    except:
        logger.debug("Completed creating (MultiPolygon) of collected chunks")
    mk_kml(shape, id, name, al)
#    try:
#        newShape = obj_from_store(id, al)
#        if newShape.area > 64800:
#            print "ObjectSizeError!!!"
#            print "{0}/{1} ({2}) is too huge, and cannot be accepted, verify where in the code this error comes from and try again!".format(al, clean(name), id)
#            return nullShape
#            sys.exit(666)
#        if (shape.area > newShape.area):
#            return shape
#        return newShape
#    except:
#        pass
    if shape.area > 64800:
        print "ObjectSizeError!!!"
        print "{0}/{1} ({2}) is too huge, and cannot be accepted, verify where in the code this error comes from and try again!".format(al, name.encode('ascii', 'replace'), id)
        return nullShape
        sys.exit(666)
    return shape

def test_objects(id, al=3, name=u"Default"):
    logger.info("Preparing to test the results for %s (%s/%s)", clean(name), al, id)
#    print "Starting to test {0} ({1})".format(name.encode('ascii', 'replace'), id)
    if al == 2:
        logger.error("Overriding test for country")
        return True
#    if al == 4:
#        if id == 54882:
#            print "Decission override for state (Espirito Santo)"
#            return True
#    myID = id + 3600000000
#    result = False
#    while result == False:
#        result = get_data('rel(area:{4}) ->.a;.a is_in;node({0},{1},{2},{3});out ids qt 1;'.format(track.bounds[1],track.bounds[0],track.bounds[3],track.bounds[2],myID), True)
    testOB = nullShape
#    if len(result['elements']) > 0:
    if True:
        testOB = build_object(id,al,name)
        if track.within(testOB):
            logger.info(u"Track is within %s (%s) place.BBOX(%s)/track.BBOX(%s)", clean(name), id, testOB.bounds, track.bounds )
            print "Within {0} ({2}/{1})".format(name.encode('ascii', 'replace'), id, al)
            return True
        elif track.intersects(testOB):
            logger.info(u"Track intersects with %s (%s) place.BBOX(%s)/track.BBOX(%s)", id, clean(name), testOB.bounds, track.bounds )
            print "Intersects {0} ({2}/{1})".format(name.encode('ascii', 'replace'), id, al)
            return True
    logger.info("Rejecting %s (%s) place.BBOX(%s)/track.BBOX(%s)!!!", clean(name), id, testOB.bounds, track.bounds )
#    print "Rejecting {0} ({1})".format(name.encode('ascii', 'replace'), id)
    return False

def get_data(searchString, returnDummy = False):
    try:
        logger.debug(searchString)
        result = api.Get(searchString, responseformat="json")
    except overpass.errors.OverpassSyntaxError as e:
        logger.critical("OverpassSyntaxError caught in get_data: %s", e)
        return False
    except overpass.errors.ServerRuntimeError as e:
        logger.critical("ServerRuntimeError from Overpass caught in get_data: %s", e)
        return False
    except overpass.errors.UnknownOverpassError as e:
        logger.critical("UnknownOverpassError caught in get_data: %s", e)
        return False
    except overpass.errors.TimeoutError as e:
        logger.critical("TimeoutError caught in get_data: %s", e)
        return False
    except overpass.errors.MultipleRequestsError as e:
        logger.error("MultipleRequestsError caught in get_data, waiting for 30 seconds: %s", e)
        time.sleep(30)
        return False
    except overpass.errors.ServerLoadError as e:
        if returnDummy:
            logger.error("ServerLoadError caught in get_data, returning dummyJSON: %s", e)
            return json.loads('{"version": 0.6, "generator": "dummy", "elements": [{"type": "dummy"}, {"type": "dummy"}] }')
        logger.error("ServerLoadError caught in get_data, waiting for 30 seconds: %s", e)
        time.sleep(30)
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("ConnectionError from requests caught in get_data, waiting for 30 seconds: %s", e)
        time.sleep(30)
        return False
    try:
        json.loads(json.dumps(result))
    except TypeError:
        logger.debug("json.TypeError in get_data")
        sys.exit(1)
        return False
    except ValueError:
        logger.error("No Valid JSON Loaded (json.ValueError in get_data): %s", result)
        sys.exit(1)
        return False
    try:
        myElements = json.loads(json.dumps(result))['elements']
    except:
        logger.error("json in get_data does not contain ['elements']: %s", result)
        sys.exit(1)
    if len(myElements) < 1:
        logger.debug("json in get_data contains empty ['elements']!")
#    logger.debug("get_data passed all tests")
    return result

def upload_gpx(gpxFile, uTags, uDescription):
    userName = os.environ.get("OSM_USER")
    if userName == None:
        userName = os.environ.get("MAPILLARY_EMAIL")
    if userName == None:
        logger.critical("NO USERNAME SET FOR UPLOAD")
        print "For upload to work, you need to set the environmental variables OSM_USER and OSM_PASSWORD"
        sys.exit(99)
    passWord = os.environ.get("OSM_PASSWORD")
    if passWord == None:
        passWord = os.environ.get("MAPILLARY_PASSWORD")
    if passWord == None:
        logger.critical("NO PASSWORD SET FOR UPLOAD")
        print "For upload to work, you need to set the environmental variables OSM_USER and OSM_PASSWORD"
        sys.exit(99)
    payload = { u"description": uDescription, u"tags": uTags.encode('utf-8').replace(".", "_"), u"visibility": u"trackable" }
#    print payload
    if no_upload:
        print payload
        sys.exit(3)
    payload = json.loads(json.dumps(payload))
    try:
        url = "http://www.openstreetmap.org/api/0.6/gpx/create"
        files = {u'file': open(gpxFile, 'rb') }
        r = requests.post(url, auth=(userName, passWord), files=files, data=payload)
    except:
        logger.critical("Exception thrown in upload_gpx")
        raise
    if r.status_code == 200:
        print "Uploaded with success"
        logger.info("%s Upload completed with success", gpxFile)
        sys.exit(0)
        return
    else:
        print "Ended with status code: {0}".format(r.status_code)
        print r.text
        logger.error("Upload unsuccessful, ended with status code: %s", r.status_code)
        logger.error("Message: %s", r.text)
        sys.exit(r.status_code)
    return


if len(sys.argv) < 2:
    print "Usage: gpxtest.py <GPX file>"
    sys.exit(0)
else:
    file = sys.argv[1]

try:
    gpx_file = open(file, 'r')
    logger.info("Opened %s", file)
except IOError:
    logger.critical("Could not find file: %s\n\n", file)
    sys.exit(1)

tree = etree.parse(gpx_file)
root = tree.getroot()

lats = []
lons = []
track = []

for trk in root.findall('{http://www.topografix.com/GPX/1/1}trk'):
    for seg in trk.findall('{http://www.topografix.com/GPX/1/1}trkseg'):
        for point in seg.findall('{http://www.topografix.com/GPX/1/1}trkpt'):
            lats.append(float(point.get('lat')))
            lons.append(float(point.get('lon')))
            trkpt = ([ float(point.get('lon')), float(point.get('lat')) ])
            track.append(trkpt)
for trk in root.findall('{http://www.topografix.com/GPX/1/0}trk'):
    for seg in trk.findall('{http://www.topografix.com/GPX/1/0}trkseg'):
        for point in seg.findall('{http://www.topografix.com/GPX/1/0}trkpt'):
            lats.append(float(point.get('lat')))
            lons.append(float(point.get('lon')))
            trkpt = ([ float(point.get('lon')), float(point.get('lat')) ])
            track.append(trkpt)
trackptLength = len(track)
if len(track) > 1:
    mk_kml(LineString(track), 0, u'test_gpx')
    track = MultiPoint(track)
elif len(track) == 1:
    track = Point(track[0])
else:
    logger.critical("Selected GPX have no valid track points")
    sys.exit(404)
lats.sort()
lons.sort()
trackLength = int(deg2meter(LineString(track).length))/1000.0
if trackLength < 1.0:
    tags.append(u"Short Trace")
elif trackLength > 100.0:
    tags.append(u"Long Trace")
logger.debug("GPX File contains %s trackpoints with %s km.", str(len(lats)), str(trackLength))

result = False
while result == False:
    result = get_data_bbox(lats[0], lons[0], lats[len(lats) - 1], lons[len(lons) - 1], 2)
    if result == False:
        time.sleep(30)

#print result

myElements = json.loads(json.dumps(result))['elements']
#print myElements
if len(myElements) == 0:
    logger.debug("No countries found in first run, testing per continent")
    bbox = []
    bbox.append( [-14.0, 91.0, 84.0, 180.0, "East Asia" ] ) # East Asia
    bbox.append( [10.0, 32.0, 40.0, 65.0, "Arabia" ] ) # Arabia
    bbox.append( [-11.0, 53.0, 84.0, 91.0, "Central Asia" ] ) # Central Asia
    bbox.append( [32.0, 26.0, 84.0, 53.0, "East Europe" ] ) # East Europe
#    bbox.append( [35.0, -35.0, 84.0, 26.0, "West Europe" ] ) # West Europe
    bbox.append( [35.0, -35.0, 84.0, 0.0, "West Europe (West)" ] )
    bbox.append( [35.0, 0.0, 59.0, 26.0, "West Europe (South)" ] )
    bbox.append( [59.0, 0.0, 84.0, 26.0, "West Europe (North)" ] )
    bbox.append( [-56.0, -28.0, 38.0, 64.0, "Africa" ] ) # Africa
    bbox.append( [25.0, -180.0, 84.0, -18.0, "North America" ] ) # North America
    bbox.append( [3.0, -123.0, 33.0, -56.0, "Central America" ] ) # Central America
#    bbox.append( [-57.0, -95.0, 13.0, -24.0, "South America" ] ) # South America
    bbox.append( [0.0, -95.0, 13.0, -24.0, "South America (North)" ] )
    bbox.append( [-34.0, -59.0, 0.0, -24.0, "South America (East)" ] )
    bbox.append( [-34.0, -95.0, 0.0, -59.0, "South America (West)" ] )
    bbox.append( [-57.0, -95.0, -34.0, -24.0, "South America (South)" ] )
    bbox.append( [-56.0, 90.0, -13.0, 180.0, "Australia" ] ) # Australia
    bbox.append( [-56.0, -180.0, 25.0, -95.0, "Pacific" ] ) # Pacific
    bbox.append( [-90.0, -180.0, -56.0, 180.0, "Antartica" ] ) # Antartica
    bbox.append( [-90.0, -180.0, 90.0, 180.0, "The World (Something is wrong further up)"] ) # If this ever happens, identify the missing square, this line should never happen to avoid controlling the GPX file against any country in the world.
    for n in bbox:
#        print n
        sPoints = []
        sPoints.append( ([ n[1], n[0] ]) )
        sPoints.append( ([ n[3], n[0] ]) )
        sPoints.append( ([ n[3], n[2] ]) )
        sPoints.append( ([ n[1], n[2] ]) )
        testOB = Polygon(sPoints)
        if track.within(testOB) or track.intersects(testOB):
            logger.debug("Found it in {0}!".format(n[4]))
#            print "Found"
            result = False
            minlon,minlat,maxlon,maxlat = testOB.bounds
            while result == False:
                result = get_data_bbox(minlat,minlon,maxlat,maxlon,2)
                if result == False:
                    time.sleep(30)
                else:
                    myElements = json.loads(json.dumps(result))['elements']
                    #print myElements
            break
#print myElements
#myElements = remove_duplicates(myElements)

done = set()
for country in myElements:
    cID = country['id']
    if cID not in done:
#        print "Executing {0}".format(cID)
        done.add(cID)
    else:
#        print "cID {0} already done!".format(cID)
        continue
    name = cID
    try:
        name = country['tags']['name']
    except:
        pass
        logger.debug("Country %s have no readable name", cID)
    try:
        name = country['tags']['name:en']
    except:
        pass
        logger.debug("Country %s have no readable name:en", cID)
    name = clean(name)

    logger.debug("Preparing to test %s (%s)", name, cID)
    if isinstance(name, int):
        logger.debug("Doesn't seem like {0} has a name!".format(name))
#    elif name == "Argentina":
#        # 4 Privince, 5 Departamento, 6 Distrito, 7 Municipio
    elif name == "Brazil":
        if test_objects(cID, 2, name):
            get_tags(country)
            result = False
            while result == False:
                result = get_data_relation(cID, 4)
            for state in json.loads(json.dumps(result))['elements']:
                sID = state['id']
                if sID not in done:
                    done.add(sID)
                else:
                    continue
                if test_objects(sID, 4, clean(state['tags']['name'])):
                    get_tags(state)
                    result = False
                    while result == False:
                        result = get_data_relation(sID, 8)
                    for municipality in json.loads(json.dumps(result))['elements']:
                        mID = municipality['id']
                        if mID not in done:
                            done.add(mID)
                        else:
                            continue
                        if test_objects(mID, 8, clean(municipality['tags']['name'])):
                            get_tags(municipality)
                            no_upload = False
#    elif name == "Chile"
        # 4 Region, 6 Province, 8 Comunas
    elif name == "Norway":
        if test_objects(cID, 2, name):
            get_tags(country)
            result = False
            while result == False:
                result = get_data_relation(cID, 4)
            for fylke in json.loads(json.dumps(result))['elements']:
                fID = fylke['id']
                if fID not in done:
                    done.add(fID)
                else:
                    continue
                if test_objects(fID, 4, clean(fylke['tags']['name'])):
                    get_tags(fylke)
                    result = False
                    while result == False:
                        result = get_data_relation(rID, 7)
                    for kommune in json.loads(json.dumps(result))['elements']:
                        kID = kommune['id']
                        if kID not in done:
                            done.add(kID)
                        else:
                            continue
                        if test_objects(kID, 7, clean(kommune['tags']['name'])):
                                get_tags(kommune)
    elif name == "Portugal":
        if test_objects(cID, 2, name):
            get_tags(country)
            result = False
            while result == False:
                result = get_data_relation(cID, 4)
            for region in json.loads(json.dumps(result))['elements']:
                rID = region['id']
                if rID not in done:
                    done.add(rID)
                else:
                    continue
                if test_objects(rID, 4, clean(region['tags']['name'])):
                    get_tags(region)
                    result = False
                    while result == False:
                        result = get_data_relation(rID, 7)
                    for municipality in json.loads(json.dumps(result))['elements']:
                        mID = municipality['id']
                        if mID not in done:
                            done.add(mID)
                        else:
                            continue
                        if test_objects(mID, 7, clean(municipality['tags']['name'])):
                            get_tags(municipality)
#    elif name == "Uguguay"
        # 4 Department, 6 Municipio
    else:
        logger.debug("No rules defined for %s (%s)", name, cID)

#    if country == "Russia":
#        logger.debug("%s: checking levels 3, 6, 8", country)
#    elif country == "Brazil" or country == "Switzerland" or country == "Uruguay" or country == "Paraguay":
#        logger.debug("%s: checking levels 4, 8", country)
#    elif country == "Norway" or country == "Sweden" or country == "Denmark":
#        logger.debug("%s: checking levels 4, 7", country)
#    elif country == "Argentina" or country == "Portugal":
#        logger.debug("%s: checking levels 6, 7", country)
#    elif country == "Chile" or country == "Spain" or country == "United States" or "United Kingdom":
#        logger.debug("%s: checking levels 4, 6, 8", country)
#    elif country == "Czech":
#        logger.debug("%s: checking levels 4, 6, 7, 8", country)
#    elif country == "Iceland":
#        logger.debug("%s: checking levels 5, 6", country)

try:
    tags.sort()
except:
    pass
tags = remove_duplicates(tags)
myTags = ", ".join(tags)
bbox = [ ([ track.bounds[1], track.bounds[0], track.bounds[3], track.bounds[2] ]) ]
myDescription = u"Track containing {0} trackpoints with a length of {2} km - bbox.{1}".format(trackptLength, bbox, trackLength)
logger.info(myTags)
upload_gpx(file, myTags, myDescription )
logger.debug("Completed execution of %s\n\n\n", file)
