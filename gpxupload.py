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
from shapely import speedups
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
import random
import chardet
logger = logging.getLogger("gpxupload")
logging.basicConfig(filename="./kml/GPXUploadEventLog.log", level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s - %(message)s",datefmt="%Y/%m/%d %H:%M:%S:")
overpassServers = []
overpassServer = "http://overpass-api.de/api/interpreter" # Default
overpassServers.append("http://overpass-api.de/api/interpreter")
overpassServers.append("http://overpass.osm.rambler.ru/cgi/interpreter")
overpassServers.append("http://api.openstreetmap.fr/oapi/interpreter")
#overpassServers.append("http://overpass.osm.ch/api/interpreter")
#overpassServers.append("http://overpass.openstreetmap.ie/api/") # Server also runs several other services so only for light usage
overpassServer = random.choice(overpassServers)
print "Download server: {0}".format(overpassServer)
overpassTimeout = 900 # 15 minutes
#overpassTimeout = 1800 # 30 minutes

if speedups.available:
#if False:
    speedups.enable()
    logger.info("Speedups enabled\n")
else:
    logger.debug("Speedups not enabled, executing default\n")

no_upload = True
absolutely_no_upload = True
latinize = False
no_kml = True
no_svg = True
no_wkb = False # Set this to true will prevent caching
no_wkt = True
debuging = False
let_us_upload = True

forceTrue = False
forceTrueID = 1823223 # Guarapari
forceTrueID = 62149

delay = 60

trackVisibility = u"public" # public, private, trackable, identifiable

lang = [ 'en', 'pt', 'no' ] # List of languages to be enforced as defaults during run of the script
tags = []
SQKM = ( (60.0 * 1.852) * (60.0 * 1.852) )
result = ""
name = u"?"
file = ""
nullShape = Point(0.0,0.0).buffer(0.0000001)

def clean(i):
    #    logger.debug("clean(%s)", i)
    if isinstance(i, int):
        i = str(i)
    codec = 'utf-8'
    if isinstance(i, unicode):
        return i
    try:
        encoding = chardet.detect(i)
        codec = encoding['encoding']
        try:
            i = i.encode(codec).decode('utf8')
            logger.decode("clean(i) Text identified as %s", codec)
        except:
            logger.decode("clean(i) failed to detect codec")
    except:
        pass
    logger.debug("clean(i) codec is %s", codec)
    if isinstance(i, unicode):
        return i
    logger.debug("Need to run down codecList in clean(i)")
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
    try:
        with open(u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".wkb") as f:
            shape = wkb_loads(f.read())
    except:
#    except wkb_loads.errors.ParseException as e:
#        logger.error("obj_from_store failed with ParseException: %s", e)
        logger.error("obj_from_store failed with ParseException:")
        return nullShape
    logger.debug("obj_from_store have successfully created a %s with size: %s", shape.geom_type, shape.area)
    return shape

def mk_kml(ob, id, name, subdir="0"):
#    if no_kml:
#        return
    logger.debug("Creating Cache Files")
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
        if no_kml and subdir != "0":
            logger.debug("no_kml set, skip creating %s", filename)
        else:
            fil = open(filename, 'w')
            fil.write(kf.to_string(prettyprint=True))
            fil.close()
            logger.info("KML Saved in %s", filename)
    except:
        logger.error("Failed to create KML: %s", filename)
    if no_svg == False:
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
    if no_wkb == False:
        try:
            if subdir != "0":
                logger.debug("Preparing for WKB file")
                filename = u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".wkb"
                fil = open(filename, 'w')
                fil.write(wkb_dumps(ob))
                fil.close()
                logger.info("WKB Saved in %s", filename)
        except:
            pass
    if no_wkt == False:
        try:
            if subdir != "0":
                logger.debug("Preparing for WKT file")
                filename = u"./kml/"+unicode(subdir)+u"/"+unicode(id)+u".wkt"
                fil = open(filename, 'w')
                fil.write(wkt_dumps(ob))
                fil.close()
                logger.info("WKt Saved in %s", filename)
        except:
            pass

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
#    searchString = 'is_in;relation["type"="boundary"]["boundary"="administrative"]["admin_level"="{4}"]({0},{1},{2},{3});out tags;'.format(minlat,minlon,maxlat,maxlon, al)
    searchString = 'relation["type"="boundary"]["boundary"="administrative"]["admin_level"="{4}"]({0},{1},{2},{3});out tags;'.format(minlat,minlon,maxlat,maxlon, al)
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
        if latinize:
            tag.append(unidecode(unicode(clean(string))))
    except:
        pass
    try:
        string = clean(myTags['name:en'])
        tags.append(string)
        if latinize:
            tag.append(unidecode(unicode(clean(string))))
    except:
        pass
    for i in lang:
        try:
            test = 'name:{0}'.format(i)
            string = clean(myTags[test])
            tags.append(string)
            if latinize:
                tag.append(unidecode(unicode(clean(string))))
        except:
            pass
        try:
            test = 'official_name:{0}'.format(i)
            string = clean(myTags[test])
            tags.append(string)
            if latinize:
                tag.append(unidecode(unicode(clean(string))))
        except:
            pass
        try:
            test = 'alt_name:{0}'.format(i)
            string = clean(myTags[test])
            for j in string.split(";"):
                tags.append(j)
                if latinize:
                    tag.append(unidecode(unicode(clean(j))))
        except:
            pass
        try:
            test = 'long_name:{0}'.format(i)
            string = clean(myTags[test])
            tags.append(string)
            if latinize:
                tag.append(unidecode(unicode(clean(string))))
        except:
            pass
    try:
        string = clean(myTags['official_name'])
        tags.append(string)
        if latinize:
            tag.append(unidecode(unicode(clean(string))))
    except:
        pass
    try:
        string = clean(myTags['short_name'])
        tags.append(string)
        if latinize:
            tag.append(unidecode(unicode(clean(string))))
    except:
        pass
    try:
        string = clean(myTags['long_name'])
        tags.append(string)
        if latinize:
            tag.append(unidecode(unicode(clean(string))))
    except:
        pass
    try:
        string = clean(myTags['alt_name'])
        for j in string.split(";"):
            tags.append(j)
            if latinize:
                tag.append(unidecode(unicode(clean(j))))
    except:
        pass
    try:
        string = clean(myTags['loc_name'])
        tags.append(string)
        if latinize:
            tag.append(unidecode(unicode(clean(string))))
    except:
        pass
    try:
        string = clean(myTags['old_name'])
        for j in string.split(";"):
            tags.append(j)
            if latinize:
                tag.append(unidecode(unicode(clean(j))))
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
        string = clean(myTags['is_in'])
        for j in string.split(";"):
            tags.append(j)
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
            logger.info("Retrieved Polygon for %s (%s/%s) from WKB, with area: %s", clean(name), al, id, shape.area)
#            mk_kml(shape, id, name, al)
            if shape.area > 64800:
                print "ObjectSizeError!!!"
                print "{0}/{1} ({2}) is too huge, and cannot be accepted, verify where in the code this error comes from and try again!".format(al, name, id)
                return nullShape
                sys.exit(666)
            elif shape.area == 0:
                print "ObjectSizeError!!!"
                print "{0}/{1} ({2}) have no size.".format(al, name, id)
            elif shape == nullShape:
#                print "obj_from_store returned nullShape"
                logger.debug("obj_from_store returned nullShape")
            else:
#                print "Built from KML"
                return shape
#        polygons.append(shape)
        logger.error("WKB not returning Polygon shape")
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
#    print "Starting to build {0} ({2}/{1})".format(name.encode('ascii', 'replace'), id, al)
    print u"Starting to build {0} ({3}) ({2}/{1})".format(name, id, al, unidecode(unicode(clean(name))))
    shape = nullShape
    myID = id + 3600000000
    result = False
    while result == False:
#        result = get_data('relation(area:{1})["type"="boundary"]["boundary"="administrative"]["admin_level"="{0}"];out geom;'.format(al, myID))
        result = get_data('relation({0});out geom;'.format(id))
        time.sleep(delay)
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
    testNodes = []
    testWays = []
    testRelation = []
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
                no_double_testing_please = set()
                for i in newElements:
                    if i['type'] == "node":
                        testNodes.append(i)
                    elif i['type'] == "way":
                        testWays.append(i)
                    else:
                        testRelation.append(i)
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
    lines = []
    rings = []
    newPoly = []
    print "Relation contains {0} node and {1} relation members that will not be processed".format(len(testNodes), len(testRelation))
    print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
    logger.debug("Completed creating all elements")
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
    if todoRounds > 0:
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
    print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
    logger.debug("Start polygonize %s lines", len(lines))
    doneRound = 0
    todoRounds = len(lines)
    if todoRounds > 0:
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
    print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
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
        logger.debug("(Multi)Polygon unary_union of polygons")
#        shape = MultiPolygon(unary_union(polygons)).buffer(meter2deg(10.0))
        shape = unary_union(polygons).buffer(meter2deg(10.0))
        try:
            logger.debug("(Multi)Polygon interiors of shape")
#            polygons.append(MultiPolygon(shape.interiors).buffer(meter2deg(10.0)))
            newPoly.append(shape.interiors.buffer(meter2deg(10.0)))
        except:
            pass
        try:
            logger.debug("(Multi)Polygon exterior of shape")
#            polygons.append(MultiPolygon(shape.exterior).buffer(meter2deg(10.0)))
            newPoly.append(shape.exterior.buffer(meter2deg(10.0)))
        except:
            pass
    except:
        pass
    print "Shape is {0}".format(shape.geom_type)
    if shape.geom_type == "MultiPolygon":
        print "We have a {0} with {1} elements".format(shape.geom_type, len(shape))
        sPoints = []
        try:
            doneRound = 0
            todoRounds = len(shape)
            if todoRounds > 0:
                for s in shape:
                    doneRound = doneRound + 1
                    print "\rProcessing {0} of {1} elements".format(doneRound, todoRounds), '\r',
                    sys.stdout.flush()
                    sPoints.append(s.centroid)
                    #print s.geom_type
                    try:
                        if s.exterior.is_ring:
                            rings.append(s.exterior)
                    except:
                        pass
                    try:
                        newPoly.append(s.interiors).buffer(meter2deg(10.0))
                    except:
                        pass
                    try:
                        newPoly.append(s.exterior).buffer(meter2deg(10.0))
                    except:
                        pass
                if len(sPoints) > 1:
                    newPoly.append(LineString(sPoints).buffer(meter2deg(10.0)))
            print ""
        except:
            print "Could not make further elements"
            pass
        print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
#    try:
#        logger.debug("MultiPolygon cascaded_union of polygons")
#        shape = MultiPolygon(cascaded_union(polygons).buffer(meter2deg(10.0)))
#        try:
#            logger.debug("MultiPolygon interiors of shape")
#            polygons.append(MultiPolygon(shape.interiors).buffer(meter2deg(10.0)))
#        except:
#            pass
#        try:
#            logger.debug("MultiPolygon exterior of shape")
#            polygons.append(MultiPolygon(shape.exterior).buffer(meter2deg(10.0)))
#        except:
#            pass
#    except:
#        pass
#    print "Shape is {0}".format(shape.geom_type)
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
                    if s.exterior.is_ring:
                        rings.append(s.exterior)
                except:
                    pass
                try:
                    newPoly.append(s.interiors).buffer(meter2deg(10.0))
                except:
                    pass
                try:
                    newPoly.append(s.exterior).buffer(meter2deg(10.0))
                except:
                    pass
            print ""
        except:
            print "Could not make further elements"
            pass
        print "We now have {0} polygons and {1} rings".format(len(polygons), len(rings))
    doneRound = 0
    todoRounds = len(rings)
    for r in rings:
        doneRound = doneRound + 1
        print "\rProcessing {0} of {1} rings".format(doneRound, todoRounds), '\r',
        sys.stdout.flush()
        newPoly.append(Polygon(r).buffer(meter2deg(1.0)))
    if len(rings) > 0:
        print ""
    print "We now have {0} polygons".format(len(newPoly))
    try:
        logger.debug("Polygon unary_union of polygons")
        shape = Polygon(unary_union(newPoly)).buffer(meter2deg(10.0))
    except:
        try:
            logger.debug("(Multi)Polygon unary_union of polygons")
            shape = MultiPolygon(unary_union(newPoly)).buffer(meter2deg(10.0))
        except:
            try:
                logger.debug("(Multi)Polygon cascaded_union of polygons")
                shape = MultiPolygon(cascaded_union(newPoly).buffer(meter2deg(10.0)))
            except:
                logger.debug("Polygon cascaded_union of polygons")
                shape = Polygon(cascaded_union(newPoly).buffer(meter2deg(10.0)))
    logger.debug("Finally all elements in place, lets make the shape")
    print "Finally all elements in place, lets make the shape"
    try:
        logger.debug("Polygon exterior of shape")
        shape = Polygon(shape.exterior).buffer(meter2deg(10.0))
    except:
        try:
            logger.debug("MultiPolygon exterior of shape")
            shape = MultiPolygon(shape.exterior).buffer(meter2deg(10.0))
        except:
            logger.error("Failed to create (Multi)Polygon from extreriors of shape")
    try:
        logger.info("Completed creating %s of collected chunks with size: %s", str(shape.geom_type), str(shape.area))
    except:
        logger.debug("Completed creating (MultiPolygon) of collected chunks")
    mk_kml(shape, id, name, al)
    print u"Shape {0} is created as a valid {1} with area: {2}".format(name, shape.geom_type, shape.area)
    if shape.area > 64800:
        print "ObjectSizeError!!!"
        print u"{0}/{1} ({2}) is too huge, and cannot be accepted, verify where in the code this error comes from and try again!".format(al, name, id)
        return nullShape
        sys.exit(666)
    return shape

def test_objects(id, al=3, name=u"Default"):
    logger.info("Preparing to test the results for %s (%s/%s)", clean(name), al, id)
    if forceTrue:
        if id == forceTrueID:
            logger.error("Overriding test for %s", forceTrueID)
            return True
    testOB = nullShape
    if True:
        testOB = build_object(id,al,name)
        if track.within(testOB):
            logger.info(u"Track is within %s (%s/%s) place.BBOX(%s)/track.BBOX(%s)", clean(name), al, id, testOB.bounds, track.bounds )
            print u"Within {0} ({3}) ({2}/{1})".format(name, id, al, unidecode(unicode(clean(name))))
            return True
        elif track.intersects(testOB):
            logger.info(u"Track intersects with %s (%s/%s) place.BBOX(%s)/track.BBOX(%s)", clean(name), al, id, testOB.bounds, track.bounds )
            print u"Intersects {0} ({3}) ({2}/{1})".format(name, id, al, unidecode(unicode(clean(name))))
            return True
    logger.info("Rejecting %s (%s/%s) place.BBOX(%s)/track.BBOX(%s)!!!", clean(name), al, id, testOB.bounds, track.bounds )
    return False

def get_data(searchString, returnDummy = False):
    api = overpass.API(timeout=overpassTimeout, endpoint=overpassServer)
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
        logger.error("MultipleRequestsError caught in get_data, waiting for %s seconds: %s", delay, e)
        time.sleep(delay)
        return False
    except overpass.errors.ServerLoadError as e:
        if returnDummy:
            logger.error("ServerLoadError caught in get_data, returning dummyJSON: %s", e)
            return json.loads('{"version": 0.6, "generator": "dummy", "elements": [{"type": "dummy"}, {"type": "dummy"}] }')
        logger.error("ServerLoadError caught in get_data, waiting for %s seconds: %s", delay, e)
        time.sleep(delay)
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("ConnectionError from requests caught in get_data, waiting for %s seconds: %s", delay, e)
        time.sleep(delay)
        return False
#    except requests.exceptions.ChunkEncodingError as e:
#        logger.error("ChunkEncodingError from requests caught in get_data, waiting for %s seconds: %s", delay, e)
#        time.sleep(delay)
#        return False
    try:
        json.loads(json.dumps(result))
    except TypeError:
        logger.debug("json.TypeError in get_data")
        sys.exit(1)
        return False
    except ValueError:
        logger.error("No Valid JSON Loaded (json.ValueError in get_data from search: %s): %s", searchString, result)
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
#    payload = { u"description": uDescription, u"tags": uTags.encode('utf-8').replace(".", "_"), u"visibility": trackVisibility }
    sendTags = uTags.replace(".", "_")
    try:
        sendTags = sendTags.encode('utf-8')
    except:
        pass
    try:
        sendTags = unicode(sendTags)
    except:
        pass
    payload = { u"description": uDescription, u"tags": sendTags, u"visibility": trackVisibility }
#    print payload
    if no_upload:
        print payload
        sys.exit(3)
    if absolutely_no_upload:
        print payload
        sys.exit(3)
    payload = json.loads(json.dumps(payload))
    try:
        url = "http://www.openstreetmap.org/api/0.6/gpx/create"
        files = {u'file': open(gpxFile, 'rb') }
        r = False
        while r == False:
            try:
                r = requests.post(url, auth=(userName, passWord), files=files, data=payload)
            except requests.exceptions.ReadTimeout as e:
                r = False
                time.sleep(delay)
            except requests.exceptions.ConnectionError as e:
                r = False
                time.sleep(delay)
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

def recursive_test(id, obj):
    obj = json.loads(json.dumps(obj))
    if id not in done:
        done.add(id)
    else:
        return False
    al = obj['tags']['admin_level']
    try:
        name = clean(obj['tags']['name'])
    except:
        try:
            name = clean(obj['tags']['name:en'])
        except:
            name = id
    if test_objects(id, al, name):
        get_tags(obj)
        return True
    return False


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
print "File {0} loaded successfully".format(file)

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
    print "Selected GPX have no valid track points"
    sys.exit(404)
lats.sort()
lons.sort()
if track.geom_type == "Point":
    trackLength = 0.0
elif len(track) > 1:
    trackLength = int(deg2meter(LineString(track).length))/1000.0
else:
    trackLength = 0.0
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
#    bbox.append( [min.lat, min.lon, max.lat, max.lon, "Identifier" ] )
    bbox.append( [35.0, 135.0, 84.0, 180.0, "East Asia/NE" ] )
    bbox.append( [-14.0, 135.0, 35.0, 180.0, "East Asia/SE" ] )
    bbox.append( [10.0, 113.0, 35.0, 135.0, "East Asia/SW/1" ] )
    bbox.append( [10.0, 91.0, 35.0, 113.0, "East Asia/SW/2" ] )
    bbox.append( [-14.0, 91.0, 10.0, 113.0, "East Asia/SW/3" ] )
    bbox.append( [-14.0, 113.0, 10.0, 135.0, "East Asia/SW/4" ] )
    bbox.append( [35.0, 91.0, 84.0, 135.0, "East Asia/NW" ] )
    bbox.append( [10.0, 32.0, 40.0, 65.0, "Arabia" ] )
    bbox.append( [-11.0, 53.0, 84.0, 91.0, "Central Asia" ] )
    bbox.append( [32.0, 26.0, 84.0, 53.0, "East Europe" ] )
    bbox.append( [35.0, -35.0, 84.0, 0.0, "West Europe (West)" ] )
    bbox.append( [47.0, 13.0, 59.0, 26.0, "West Europe (South/1)" ] )
    bbox.append( [35.0, 13.0, 47.0, 26.0, "West Europe (South/2)" ] )
    bbox.append( [35.0, 0.0, 47.0, 13.0, "West Europe (South/3)" ] )
    bbox.append( [47.0, 0.0, 59.0, 13.0, "West Europe (South/4)" ] )
    bbox.append( [59.0, 0.0, 84.0, 26.0, "West Europe (North)" ] )
    bbox.append( [28.0, -28.0, 38.0, 64.0, "Mediterania" ] )
    bbox.append( [-56.0, -28.0, 28.0, 64.0, "Africa" ] )
    bbox.append( [25.0, -180.0, 84.0, -126.0, "North America (West)" ] )
    bbox.append( [25.0, -126.0, 84.0, -72.0, "North America (Central)" ] )
    bbox.append( [25.0, -72.0, 84.0, -18.0, "North America (East)" ] )
    bbox.append( [3.0, -123.0, 33.0, -56.0, "Central America" ] )
    bbox.append( [0.0, -95.0, 13.0, -24.0, "South America (North)" ] )
    bbox.append( [-34.0, -59.0, 0.0, -24.0, "South America (East)" ] )
    bbox.append( [-34.0, -95.0, 0.0, -59.0, "South America (West)" ] )
    bbox.append( [-57.0, -95.0, -34.0, -24.0, "South America (South)" ] )
    bbox.append( [-56.0, 90.0, -13.0, 180.0, "Australia" ] )
    bbox.append( [-56.0, -180.0, 25.0, -95.0, "Pacific" ] )
    bbox.append( [-90.0, -180.0, -56.0, 180.0, "Antartica" ] )
    bbox.append( [83.0, -180.0, 90.0, 180.0, "Arctic" ] )
    bbox.append( [-90.0, -180.0, 90.0, 180.0, "The World (Something is wrong further up)"] ) # If this ever happens, identify the missing square, this line should never happen to avoid controlling the GPX file against any country in the world.
    for n in bbox:
        sPoints = []
        sPoints.append( ([ n[1], n[0] ]) )
        sPoints.append( ([ n[3], n[0] ]) )
        sPoints.append( ([ n[3], n[2] ]) )
        sPoints.append( ([ n[1], n[2] ]) )
        testOB = Polygon(sPoints)
        if track.within(testOB) or track.intersects(testOB):
            logger.debug("Found it in {0}!".format(n[4]))
            print "Found in {0}!".format(n[4])
            result = False
            minlon,minlat,maxlon,maxlat = testOB.bounds
            while result == False:
                result = get_data_bbox(minlat,minlon,maxlat,maxlon,2)
                if result == False:
                    time.sleep(delay)
                else:
                    myElements = json.loads(json.dumps(result))['elements']
            break

done = set()
for bravo in myElements:
    bID = bravo['id']
    if bID not in done:
#        print "Executing {0}".format(cID)
        done.add(bID,)
    else:
#        print "cID {0} already done!".format(cID)
        continue
    bname = bID
    try:
        bname = bravo['tags']['name']
    except:
        pass
        logger.debug("Country %s have no readable name", bID)
    try:
        bname = bravo['tags']['name:en']
    except:
        pass
        logger.debug("Country %s have no readable name:en", bID)
    bname = clean(bname)

    logger.debug("Preparing to test %s (%s)", bname, bID)
    if isinstance(bname, int):
        logger.debug("Doesn't seem like {0} has a name!".format(bname))
    elif bname == u"Afghanistan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Albania":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for False in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 7)
                    for golf in  json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            result = False
                            while result == False:
                                result = get_data_relation(gID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Algeria":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Andorra":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 7)
            for golf in json.loads(json.dumps(result))['elements']:
                gID = golf['id']
                if recursive_test(gID, golf):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Angola":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Anguilla":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Antigua and Barbuda":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Argentina":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    result = False
                                    while result == False:
                                        result = get_data_relation(fID, 7)
                                    for golf in json.loads(json.dumps(result))['elements']:
                                        gID = golf['id']
                                        if recursive_test(gID, golf):
                                            if let_us_upload:
                                                no_upload = False
    elif bname == u"Armenia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Australia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                dname = delta['tags']['name']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    if dname == u"Victoria":
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 5)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                result = False
                                while result == False:
                                    result = get_data_relation(eID, 6)
                                for foxtrot in json.loads(json.dumps(result))['elements']:
                                    fID = foxtrot['id']
                                    if recursive_test(fID, 7):
                                        if let_us_upload:
                                            no_upload = False
                    if dname == u"Tasmania" or dname == u"Northern Territory" or dname == u"New South Wales":
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
                    if dname == u"Australian Capital Territory":
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 7)
                        for golf in json.loads(json.dumps(result))['elements']:
                            gID = golf['id']
                            if recursive_test(gID, golf):
                                if let_us_upload:
                                    no_upload = False
    elif bname == u"Austria":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Azerbaijan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Bahrain":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Bangladesh":
        if test_objects(bID, 2, bname):
            get_tags(county)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 9)
                    for india in json.loads(json.dumps(result))['elements']:
                        iID = india['id']
                        if recursive_test(iID, india):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Barbados":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Belarus":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Belgium":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            result = False
                            while result == False:
                                result = get_data_relation(gID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Belize":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Benin":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Bermuda":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Bhutan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Bolivia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Bosnia and Herzegovina":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                try:
                    dname = land['tags']['name:en']
                except:
                    dname = delta['tags']['name']
                if recursive_test(dID, delta):
                    logger.debug("Testing internally for %s", dname)
                    if dname == u"Brcko district of Bosnia and Herzegovina":
                        if let_us_upload:
                            no_upload = False
                    elif dname == u"Republika Srpska":
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 7)
                        for golf in json.loads(json.dumps(result))['elements']:
                            gID = golf['id']
                            if recursive_test(gID, golf):
                                if let_us_upload:
                                    no_upload = False
                    else:
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 5)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                result = False
                                while result == False:
                                    result = get_data_relation(eID, 6)
                                for foxtrot in json.loads(json.dumps(result))['elements']:
                                    fID = foxtrot['id']
                                    if recursive_test(fID, foxtrot):
                                        if let_us_upload:
                                            no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(eID, 7)
                                for golf in json.loads(json.dumps(result))['elements']:
                                    gID = golf['id']
                                    if recursive_test(gID, golf):
                                        if let_us_upload:
                                            no_upload = False
    elif bname == u"Botswana":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Brazil":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"British Indian Ocean Territory":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"British Sovereign Base Areas":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"British Virgin Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Brunei":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Bulgaria":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Burkina Faso":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(rID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Burundi":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Cambodia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Cameroon":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Canada":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                dname = delta['tags']['name']
                if recursive_test(dID, delta):
                    if dname == u"Alberta" or dname == u"Manitoba" or dname == u"Ontario":
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 8)
                        for hotel in json.loads(json.dumps(result))['elements']:
                            hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
                    if dname == u"British Columbia" or dname == u"New Brunswick" or dname == u"Prince Edwuard Island" or dname == u"Saskatchewan":
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
                    if dname == u"Nova Scotia":
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 5)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                if let_us_upload:
                                    no_upload = False
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
                    if dname == u"New Foundland and Labrador" or dname == u"Nunavat":
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 8)
                        for hotel in json.loads(json.dumps(result))['elements']:
                            hID = hotel['id']
                            if recursive_test(hID, hotel):
                                if let_us_upload:
                                    no_upload = False
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Cape Verde":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Cayman Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Central African Republic":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Chad":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Chile":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"China":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                try:
                    cname = charlie['tags']['name:en']
                except:
                    cname = charlie['tags']['name']
                logger.debug("Checking internal for %s", cname)
                if cname == u"Hong Kong":
                    if recursive_test(cID, charlie):
                        result = False
                        while result == False:
                            result = get_data_relation(cID, 5)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                if let_us_upload:
                                    no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(eID, 6)
                                for foxtrot in json.loads(json.dumps(result))['elements']:
                                    fID = foxtrot['id']
                                    if recursive_test(fID, foxtrot):
                                        if let_us_upload:
                                            no_upload = False
                elif cname == u"Macao":
                    if recursive_test(cID, charlie):
                        result = False
                        while result == False:
                            result = get_data_relation(cID, 5)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                if let_us_upload:
                                    no_upload = False
                        result = False
                        while result == False:
                            result = get_data_relation(cID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
                else:
                    result = False
                    while result == False:
                        result = get_data_relation(bID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            result = False
                            while result == False:
                                result = get_data_relation(dID, 5)
                            for echo in json.loads(json.dumps(result))['elements']:
                                eID = echo['id']
                                if recursive_test(eID, echo):
                                    if let_us_upload:
                                        no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(eID, 6)
                                for foxtrot in json.loads(json.dumps(result))['elements']:
                                    fID = foxtrot['id']
                                    if recursive_test(fID, foxtrot):
                                        if let_us_upload:
                                            no_upload = False
    elif bname == u"Colombia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    try:
                        dname = delta['tags']['name:en']
                    except:
                        dname = delta['tags']['name']
                    logger.debug("Checking internal for %s", dname)
                    if dname == u"Bogota":
                        if let_us_upload:
                            no_upload = False
                    else:
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    result = False
                    while result == False:
                        result = get_data_relation(eID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Comoros":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Congo-Brazzaville":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(sID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Congo-Kinshasa":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(sID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Cook Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Costa Rica":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, part):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Côte d'Ivoire":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Croatia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Cuba":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Cyprus":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Czech Republic":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    result = False
                                    while result == False:
                                        result = get_data_relation(gID, 8)
                                    for hotel in json.loads(json.dumps(result))['elements']:
                                        hID = hotel['id']
                                        if recursive_test(hID, hotel):
                                            if let_us_upload:
                                                no_upload = False
    elif bname == u"Denmark":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 7)
            for golf in json.loads(json.dumps(result))['elements']:
                gID = golf['id']
                if recursive_test(gID, golf):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Djibouti":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Dominica":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Dominican Republic":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"East Timor":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Ecuador":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Egypt":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"El Salvador":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 7)
            for golf in json.loads(json.dumps(result))['elements']:
                gID = golf['id']
                if recursive_test(gID, golf):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Equatorial Guinea":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Eritrea":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Estonia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Ethiopia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Falkland Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Faroe Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in  json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Federated States of Micronesia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Fiji":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Finland":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"France":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Gabon":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Gambia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Georgia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in  json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in  json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Germany":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                try:
                    dname = delta['tags']['name:en']
                except:
                    dname = delta['tags']['name']
                logger.debug("Testing internally for %s", dname)
                if dname == u"Berlin":
                    if recursive_test(dID, delta):
                        if let_us_upload:
                            no_upload = False
                elif dname == u"Hamburg":
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 8)
                        for hotel in json.loads(json.dumps(result))['elements']:
                            hID = hotel['id']
                            if recursive_test(hID, hotel):
                                if let_us_upload:
                                    no_upload = False
                        if let_us_upload:
                            no_upload = False
                elif dname == u"Baden-Württemberg" or dname == u"Free State of Bavaria" or dname == u"North Rhine-Westphalia":
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 5)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                result = False
                                while result == False:
                                    result = get_data_relation(eID, 6)
                                for foxtrot in json.loads(json.dumps(result))['elements']:
                                    fID = foxtrot['id']
                                    if recursive_test(fID, foxtrot):
                                        if let_us_upload:
                                            no_upload = False
                else:
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
    elif bname == u"Ghana":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Gibraltar":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Greece":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3) # Sovereign Temple Mountain Monastary
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Greenland":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Grenada":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Guatemala":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Guernsey":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Guinea":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in  json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Guinea-Bissau":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in  json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            result = False
                            while result == False:
                                result = get_data_relation(dID, 6)
                            for foxtrot in  json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Guyana":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Haiti":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in  json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 8)
                            for hotel in  json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Honduras":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Hungary":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in  json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 6)
                            for foxtrot in  json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
                                    result = False
                                    while result == False:
                                        result = get_data_relation(fID, 7)
                                    for golf in  json.loads(json.dumps(result))['elements']:
                                        gID = golf['id']
                                        if recursive_test(gID, golf):
                                            if let_us_upload:
                                                no_upload = False
                                            result = False
                                            while result == False:
                                                result = get_data_relation(gID, 8)
                                            for hotel in  json.loads(json.dumps(result))['elements']:
                                                hID = hotel['id']
                                                if recursive_test(hID, hotel):
                                                    if let_us_upload:
                                                        no_upload = False
    elif bname == u"Iceland":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    result = False
                    while result == False:
                        result = get_data_relation(eID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"India":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Indonesia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Iran":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Iraq":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Ireland":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result - False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    result = False
                    while result == False:
                        result = get_data_relation(eID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Isle of Man":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Italy":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3) # Sovereign Military Hospitaler Order of Saint John of Jerusalem of Rhodes
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Israel":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in  json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Jamaica":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    result = False
                    while result == False:
                        result = get_data_relation(ccID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Japan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Jersey":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Jordan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Kazakhstan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Kenya":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Kiribati":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Kosovo":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Kuwait":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Kyrgyzstan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Laos":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Latvia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Lebanon":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in  json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Lesotho":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Liberia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Libya":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Liechtenstein":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Lithuania":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Luxembourg":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Macedonia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Madagascar":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                try:
                    cname = charlie['tags']['name:en']
                except:
                    cname = charlie['tags']['name']
                if recursive_test(cID, charlie):
                    logger.debug("Checking internal for %s", cname)
                    if cname == u"Province d'Antanarivo":
                        result = False
                        while result == False:
                            result = get_data_relation(cID, 8)
                        for hotel in json.loads(json.dumps(result))['elements']:
                            hID = hotel['id']
                            if recursive_test(hID, hotel):
                                if let_us_upload:
                                    no_upload = False
                    else:
                        result = False
                        while result == False:
                            result = get_data_relation(cID, 4)
                        for delta in json.loads(json.dumps(result))['elements']:
                            dID = delta['id']
                            if recursive_test(dID, delta):
                                if let_us_upload:
                                    no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(dID, 8)
                                for hotel in json.loads(json.dumps(result))['elements']:
                                    hID = hotel['id']
                                    if recursive_test(hID, hotel):
                                        if let_us_upload:
                                            no_upload = False
                        result = False
                        while result == False:
                            result = get_data_relation(cID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(fID, 9)
                                for india in json.loads(json.dumps(result))['elements']:
                                    iID = india['id']
                                    if recursive_test(iID, india):
                                        if let_us_upload:
                                            no_upload = False
    elif bname == u"Malawi":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Malaysia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Maldives":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Mali":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Malta":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3) # Sovereign Military Hospitaler Order of Saint John of Jerusalem of Rhodes
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Marshall Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Mauritania":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Mauritius":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                result = False
                while result == False:
                    result = get_data_relation(cID, 5)
                for echo in json.loads(json.dumps(result))['elements']:
                    eID = echo['id']
                    if recursive_test(eID, echo):
                        if let_us_upload:
                            no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Mexico":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in  json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Moldova":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Monaco":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    result = False
                    while result == False:
                        result = get_data_relation(hID, 10)
                    for juliet in json.loads(json.dumps(result))['elements']:
                        jID = juliet['id']
                        if recursive_test(jID, juliet):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Mongolia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Montenegro":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Montserrat":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Morocco":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    result = False
                    while result == False:
                        result = get_data_relation(eID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Mozambique":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Myanmar":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Namibia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Nauru":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Nepal":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    result = False
                                    while result == False:
                                        result = get_data_relation(fID, 8)
                                    for hotel in json.loads(json.dumps(result))['elements']:
                                        hID = hotel['id']
                                        if recursive_test(hID, hotel):
                                            if let_us_upload:
                                                no_upload = False
    elif bname == u"New Zealand":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Nicaragua":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Niger":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Nigeria":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Niue":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"North Korea":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Norway":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Oman":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Pakistan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Palau":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Palestinian Territories":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
            result = False # To capture the Old Town
            while result == False:
                result = get_data_relation(bID, 9)
            for india in json.loads(json.dumps(result))['elements']:
                iID = india['id']
                if recursive_test(iID, india):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Panama":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Papua New Guinea":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Paraguay":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Peru":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Philippines":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                try:
                    cname = charlie['tags']['name:en']
                except:
                    cname = charlie['tags']['name']
                logger.debug("Checking internal for %s", cname)
                if cname == u"Metro Manila":
                    if recursive_test(cID, charlie):
                        result = False
                        while result == False:
                            result = get_data_relation(cID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
                else:
                    if recursive_test(cID, charlie):
                        result = False
                        while result == False:
                            result = get_data_relation(cID, 4)
                        for delta in json.loads(json.dumps(result))['elements']:
                            dID = delta['id']
                            if recursive_test(dID, delta):
                                if let_us_upload:
                                    no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(dID, 6)
                                for foxtrot in json.loads(json.dumps(result))['elements']:
                                    fID = foxtrot['id']
                                    if recursive_test(fID, foxtrot):
                                        if let_us_upload:
                                            no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(dID, 7)
                                for golf in json.loads(json.dumps(result))['elements']:
                                    gID = golf['id']
                                    if recursive_test(gID, golf):
                                        if let_us_upload:
                                            no_upload = False
    elif bname == u"Pitcairn Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Portugal":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Poland":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Qatar":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Romania":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Russian Federation":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            result = False
                            while result == False:
                                result = get_data_relation(dID, 5)
                            for echo in json.loads(json.dumps(result))['elements']:
                                eID = echo['id']
                                if recursive_test(eID, echo):
                                    if let_us_upload:
                                        no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(dID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Rwanda":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Sahrawi Arab Democratic Republic":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Saint Helena, Ascension and Tristan da Cunha":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Saint Kitts and Nevis":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 10)
            for juliet in json.loads(json.dumps(result))['elements']:
                jID = juliet['id']
                if recursive_test(jID, juliet):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Saint Lucia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Saint Vincent and the Grenadines":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Samoa":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"San Marino":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"São Tomé and Príncipe":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Saudi Arabia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Senegal":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(gID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Serbia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Seychelles":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Sierra Leone":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Singapore":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Slovakia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Slovenia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    result = False
                    while result == False:
                        result = get_data_relation(eID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Solomon Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Somalia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"South Africa":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"South Georgia and the South Sandwich Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"South Korea":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"South Sudan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Spain":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Sri Lanka":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
                                    result = False
                                    while result == False:
                                        result = get_data_relation(fID, 7)
                                    for golf in json.loads(json.dumps(result))['elements']:
                                        gID = golf['id']
                                        if recursive_test(gID, golf):
                                            if let_us_upload:
                                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(eID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Sudan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Suriname":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Swaziland":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Sweden":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            result = False
                            while result == False:
                                result = get_data_relation(dID, 7)
                            for golf in json.loads(json.dumps(result))['elements']:
                                gID = golf['id']
                                if recursive_test(gID, golf):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Switzerland":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            result = False
                            while result == False:
                                result = get_data_relation(fID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Syria":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Taiwan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 5)
            for echo in json.loads(json.dumps(result))['elements']:
                eID = echo['id']
                if recursive_test(eID, echo):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    result = False
                    while result == False:
                        result = get_data_relation(fID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Tajikistan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Tanzania":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            if let_us_upload:
                                no_upload = False
                            result = False
                            while result == False:
                                result = get_data_relation(dID, 5)
                            for echo in json.loads(json.dumps(result))['elements']:
                                eID = echo['id']
                                if recursive_test(eID, echo):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Thailand":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"The Bahamas":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"The Netherlands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                cname = cID
                try:
                    cname = charlie['tags']['name:en']
                except:
                    cname = charlie['tags']['name']
                logger.debug("Testing internally for %s", cname)
                if cname == u"Aruba":
                    result = False
                    while result == False:
                        result = get_data_relation(aID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
                elif cname == u"Netherlands":
                    result = False
                    while result == False:
                        result = get_data_relation(aID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            result = False
                            while result == False:
                                result = get_data_relation(dID, 8)
                            for hotel in json.loads(json.dumps(result))['elements']:
                                hID = hotel['id']
                                if recursive_test(hID, hotel):
                                    if let_us_upload:
                                        no_upload = False
                else:
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Togo":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 9)
                    for india in json.loads(json.dumps(result))['elements']:
                        iID = india['id']
                        if recursive_test(iID, india):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Tonga":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 7)
                    for golf in json.loads(json.dumps(result))['elements']:
                        gID = golf['id']
                        if recursive_test(gID, golf):
                            if let_us_upload:
                                no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 5)
                    for echo in json.loads(json.dumps(result))['elements']:
                        eID = echo['id']
                        if recursive_test(eID, echo):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Tokelau":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Trinidad and Tobago":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Tunisia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Turkey":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            result = False
                            while result == False:
                                result = get_data_relation(dID, 6)
                            for foxtrot in json.loads(json.dumps(result))['elements']:
                                fID = foxtrot['id']
                                if recursive_test(fID, foxtrot):
                                    if let_us_upload:
                                        no_upload = False
    elif bname == u"Turkmenistan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Turks and Caicos Islands":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 6)
            for foxtrot in json.loads(json.dumps(result))['elements']:
                fID = foxtrot['id']
                if recursive_test(fID, foxtrot):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Tuvalu":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 8)
            for hotel in json.loads(json.dumps(result))['elements']:
                hID = hotel['id']
                if recursive_test(hID, hotel):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Uganda":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    result = False
                    while result == False:
                        result = get_data_relation(cID, 4)
                    for delta in json.loads(json.dumps(result))['elements']:
                        dID = delta['id']
                        if recursive_test(dID, delta):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Ukraine":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"United Arab Emirates":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"United Kingdom":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                try:
                    dname = delta['tags']['name:en']
                except:
                    dname = delta['tags']['name']
                logger.debug("Checking internal for %s", dname)
                if dname == u"Northern Ireland":
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            searchString = 'relation(area:{0})["type"="boundary"]["boundary"="historic"]["admin_level"="5"];out tags;'.format(dID + 3600000000)
                            result = get_data(searchString)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                result = False
                                while result == False:
                                    searchString = 'relation(area:{0})["type"="boundary"]["boundary"="historic"]["admin_level"="6"];out tags;'.format(eID + 3600000000)
                                    result = get_data(searchString)
                                for foxtrot in json.loads(json.dumps(result))['elements']:
                                    fID = foxtrot['id']
                                    if recursive_test(fID, foxtrot):
                                        result = False
                                        while result == False:
                                            result = get_data_relation(fID, 10)
                                        for juliet in json.loads(json.dumps(result))['elements']:
                                            jID = juliet['id']
                                            if recursive_test(jID, juliet):
                                                if let_us_upload:
                                                    no_upload = False
                elif dname == u"England":
#                    print "Testing for England 4/{0}".format(dID)
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 5)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                result = False
                                while result == False:
                                    result = get_data_relation(eID, 6)
                                for foxtrot in json.loads(json.dumps(result))['elements']:
                                    fID = foxtrot['id']
                                    if recursive_test(fID, foxtrot):
                                        if let_us_upload:
                                            no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(eID, 8)
                                for hotel in json.loads(json.dumps(result))['elements']:
                                    hID = hotel['id']
                                    if recursive_test(hID, hotel):
                                        if let_us_upload:
                                            no_upload = False
                else:
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
    elif bname == u"United States of America":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 3)
            for charlie in json.loads(json.dumps(result))['elements']:
                cID = charlie['id']
                if recursive_test(cID, charlie):
                    if let_us_upload:
                        no_upload = False
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                try:
                    dname = delta['tags']['name:en']
                except:
                    try:
                        dname = delta['tags']['name']
                    except:
                        dname = dID
                logger.debug("Testing internally for %s", dname)
                if dname == dID:
                    logger.warning("US State have no name: %s", dname)
                    if recursive_test(dID, delta):
                        if let_us_upload:
                            no_upload = False
                elif dname == "District of Colombia":
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 8)
                        for hotel in json.loads(json.dumps(result))['elements']:
                            hID = hotel['id']
                            if recursive_test(hID, hotel):
                                if let_us_upload:
                                    no_upload = False
                elif dname == "Connecticut":
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 8)
                        for hotel in json.loads(json.dumps(result))['elements']:
                            hID = hotel['id']
                            if recursive_test(hID, hotel):
                                if let_us_upload:
                                    no_upload = False
                else:
                    if recursive_test(dID, delta):
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 5)
                        for echo in json.loads(json.dumps(result))['elements']:
                            eID = echo['id']
                            if recursive_test(eID, echo):
                                if let_us_upload:
                                    no_upload = False
                        result = False
                        while result == False:
                            result = get_data_relation(dID, 6)
                        for foxtrot in json.loads(json.dumps(result))['elements']:
                            fID = foxtrot['id']
                            if recursive_test(fID, foxtrot):
                                if let_us_upload:
                                    no_upload = False
                                result = False
                                while result == False:
                                    result = get_data_relation(fID, 8)
                                for hotel in json.loads(json.dumps(result))['elements']:
                                    hID = hotel['id']
                                    if recursive_test(hID, hotel):
                                        if let_us_upload:
                                            no_upload = False
    elif bname == u"Uruguay":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Uzbekistan":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 8)
                    for hotel in json.loads(json.dumps(result))['elements']:
                        hID = hotel['id']
                        if recursive_test(hID, hotel):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Vanuatu":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Vatican City":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            if let_us_upload:
                no_upload = False
    elif bname == u"Venezuela":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    elif bname == u"Vietnam":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Yemen":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Zambia":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
    elif bname == u"Zimbabwe":
        if test_objects(bID, 2, bname):
            get_tags(bravo)
            result = False
            while result == False:
                result = get_data_relation(bID, 4)
            for delta in json.loads(json.dumps(result))['elements']:
                dID = delta['id']
                if recursive_test(dID, delta):
                    if let_us_upload:
                        no_upload = False
                    result = False
                    while result == False:
                        result = get_data_relation(dID, 6)
                    for foxtrot in json.loads(json.dumps(result))['elements']:
                        fID = foxtrot['id']
                        if recursive_test(fID, foxtrot):
                            if let_us_upload:
                                no_upload = False
    else:
        logger.debug("No rules defined for %s (%s)", bname, bID)

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
