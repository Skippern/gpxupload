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
from shapely.ops import linemerge, polygonize, cascaded_union, unary_union
from shapely.validation import explain_validity
from shapely.wkt import loads
from unidecode import unidecode
from math import cos, sin, radians, degrees
import datetime
import time
import requests
logger = logging.getLogger("gpxupload")
logging.basicConfig(filename="./kml/GPXUploadEventLog.log", level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s - %(message)s",datefmt="%Y/%m/%d %H:%M:%S:")
#logging.basicConfig(filename="./kml/GPXUploadEventLog.log", level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s - %(message)s",datefmt="%Y/%m/%d %H:%M:%S:")
#logging.basicConfig(filename="./kml/GPXUploadEventLog.log", level=logging.WARNING, format="%(asctime)s %(name)s %(levelname)s - %(message)s",datefmt="%Y/%m/%d %H:%M:%S:")
#overpassServer = "http://overpass-api.de/api/interpreter" # Default
#overpassServer = "http://overpass.osm.rambler.ru/cgi/interpreter"
#overpassServer = "http://api.openstreetmap.fr/oapi/interpreter"
overpassServer = "http://overpass.osm.ch/api/interpreter"


#if speedups.available:
if False:
    speedups.enable()
    logger.info("Speedups enabled\n")
else:
    logger.debug("Speedups not enabled, executing default\n")

lang = [ 'en', 'pt', 'no' ]
tags = []
tags.append(u"gpxupload")
toTest = []
treTest = []
fireTest = []
femTest = []
seksTest = []
syvTest = []
atteTest = []
niTest = []
tiTest = []
bbox = []
polygons = []
testOB = Point( ([ 0.0, 0.0 ]) ).buffer(0.00001)
sPoints = []
SQKM = ( (60.0 * 1.852) * (60.0 * 1.852) )
result = ""
name = u"?"
file = ""

def clean(i):
    codecList = [ 'ascii', 'iso-8859-2', 'iso-8859-1', 'iso-8859-3', 'iso-8859-4', 'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8', 'iso-8859-9', 'iso-8859-10', 'iso-8859-11', 'iso-8859-12', 'iso-8859-13', 'iso-8859-14', 'iso-8859-15', 'iso-8859-16', 'mac-latin2', 'big5', 'cp037', 'cp1006', 'cp1026', 'cp1140', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256', 'cp1257', 'cp1258', 'cp424', 'cp437', 'cp500', 'cp720', 'cp737', 'cp755', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'euc_jis-2004', 'gb18030', 'gb2312', 'gbk', 'hp-roman8', 'mac_arabic', 'mac_centeuro', 'mac_croatian', 'mac_cyrillic', 'mac_farsi', 'mac_greek', 'mac_iceland', 'mac_roman', 'mac_romanian', 'mac_turkish', 'palmos', 'ptcp154', 'tis_620', 'mbcs', 'utf-8' ]
    for codec in codecList:
        try:
            i = i.encode(codec).decode('utf8')
            #print "{0} was encoded with {1}".format(i, codec)
            break
        except:
            pass
    return i

def deg2meter(deg):
    return (deg * (60.0 * 1852.0))
def meter2deg(meter):
    return (meter / (1852.0 * 60.0 ))

def test_relation(id):
    logger.debug("Testing GPX file in relation with id: %s", str(id))
    name = str(id)
    try:
        toTest.remove(id)
    except:
        pass
    try:
        treTest.remove(id)
    except:
        pass
    try:
        fireTest.remove(id)
    except:
        pass
    try:
        femTest.remove(id)
    except:
        pass
    try:
        seksTest.remove(id)
    except:
        pass
    try:
        syvTest.remove(id)
    except:
        pass
    try:
        atteTest.remove(id)
    except:
        pass
    try:
        niTest.remove(id)
    except:
        pass
    try:
        tiTest.remove(id)
    except:
        pass
    result = False
    while result == False:
        result = get_relation(id)
        if result == False:
            time.sleep(10)
    logger.debug("Relation downloaded")
    myElements = json.loads(result)['elements']
    sPoints = []
    nodeList = []
    wayList = []
    relationList = []
    LineStringList = []
    name = ""
    outerList = set()
    innerList = set()
    logger.debug("There are %s elements in the relation", len(myElements))
    while len(myElements) > 0:
        check = myElements[0]
        myElements.remove(check)
        if check['type'] == 'node':
            nodeList.append(check)
        elif check['type'] == 'way':
            wayList.append(check)
        else:
            relationList.append(check)
    try:
        name = unidecode(clean(json.loads(json.dumps(relationList[0]))['tags']['name']))
    except:
        pass
    logger.debug("Completed building object list, with %s nodes, %s ways and %s relations", len(nodeList), len(wayList), len(relationList))
    if len(relationList) > 1:
        logger.warning("Download contains more than one relation, this is probably an error in the way the query is done")
    elif len(relationList) == 0:
        logger.error("Download has no relations, the code is broken!")
    myElements = json.loads(json.dumps(relationList[0]))['members']
    logger.debug("The relation has %s members", len(myElements))
    while len(myElements) > 0:
        check = myElements[0]
        myElements.remove(check)
        if check['type'] == 'way' and check['role'] == 'outer':
            outerList.add(check['ref'])
        elif check['type'] == 'way' and check['role'] == 'inner':
            innerList.add(check['ref'])
        elif check['type'] == 'way' and check['role'] == 'conclave':
            outerList.add(check['ref'])
        elif check['type'] == 'way' and check['role'] == 'exclave':
            innerList.add(check['ref'])
        elif check['type'] == 'way' and check['role'] == '':
            logger.error("Relation %s have members without roles!", id)
            outerList.add(check['ref'])
        elif check['type'] == 'node' or check['type'] == 'relation':
            sys.stdout.write('')
        else:
            logger.error("Unknown role in relation %s: %s", id, check['role'] )
    logger.debug("Creating lines of outer boundries of relation out of %s ways (%s outer, %s inner)", len(wayList), len(outerList), len(innerList))
    nn = 0
    for way in wayList:
        nn += 1
        if way['id'] in outerList:
            for node in way['nodes']:
                for i in nodeList:
                    if node == i['id']:
                        sPoints.append( ([ float(i['lon']), float(i['lat']) ]) )
            if len(sPoints) > 1:
                LineStringList.append(LineString(sPoints))
        sPoints = []
    logger.debug("%s lines created in %s passes", len(LineStringList), nn)
    rings = []
    lines = []
    polygons = []
    logger.debug("Separating circular and non-circular lines from %s LineStrings", len(LineStringList))
    while len(LineStringList) > 0:
        i = LineStringList[0]
        if i.is_ring and len(i.coords) > 2:
            rings.append(i)
        else:
            lines.append(i)
        LineStringList.remove(i)
    logger.debug("%s circular lines and %s non-circular lines", len(rings), len(lines))
    workflow = []
    logger.debug("Merging non-circular lines")
    #    try:
    newLines = []
    for line in lines:
        if isinstance(line, MultiLineString):
            newLines.extend(line)
        else:
            newLines.append(line)
    try:
        newLine = linemerge(newLines)
    except:
        try:
            newLine = lines[0]
        except:
            newLine = LineString( [ (0.0,0.0), (0.000001,0.0) ] )
            pass
    if newLine.is_ring:
        logger.debug("newLine is a %s closed ring", newLine.geom_type)
        rings.append(newLine)
    else:
        logger.debug("newLine is a non-closed %s", newLine.geom_type)
        lines.append(newLine)
    try:
        polygons.append(Polygon(newLine).buffer(meter2deg(1.0)))
        logger.debug("Created Polygon from sum of lines")
    except:
        logger.debug("Not able to create Polygon from sum of lines")
        pass
    try:
        polygons.append(MultiPolygon(newLine).buffer(meter2deg(1.0)))
        logger.debug("Created MultiPolygon from sum of lines")
    except:
        logger.debug("Not able to create MultiPolygon from sum of lines")
        pass
    #    newLine = lines[0]
    while len(lines) > 0:
        i = lines[0]
        try:
            newLine = linemerge( [newLine, i] )
        except:
            #            raise
            pass
        lines.remove(i)
        workflow.append( i.buffer(meter2deg(1.0)) )
        polygons.append( i.buffer(meter2deg(1.0)) )
    polygons.append( cascaded_union(workflow).buffer(meter2deg(1.0)) )
    if newLine.is_ring:
        logger.debug("newLine is a %s closed ring", newLine.geom_type)
        rings.append(newLine)
    else:
        logger.debug("newLine is a non-closed %s", newLine.geom_type)
    try:
        polygons.append(Polygon(newLine).buffer(meter2deg(1.0)))
        logger.debug("Created Polygon from sum of lines")
    except:
        logger.debug("Not able to create Polygon from sum of lines")
        pass
    try:
        polygons.append(MultiPolygon(newLine).buffer(meter2deg(1.0)))
        logger.debug("Created MultiPolygon from sum of lines")
    except:
        logger.debug("Not able to create MultiPolygon from sum of lines")
        pass
    logger.debug("Merging circular lines")
    while len(rings) > 0:
        i = rings[0]
        polygons.append(Polygon(i).buffer(meter2deg(1.0) ))
        rings.remove(i)
    nn = -1
    for i in polygons:
        nn += 1
        if i.is_valid:
            logger.debug("polygons[%s] is a valid %s", str(nn), i.geom_type)
        else:
            logger.debug("polygons[%s] is NOT a valid %s", str(nn), i.geom_type)
    if len(polygons) > 1:
        logger.info("Creating a MultiPolygon from %s objects", str(len(polygons)))
        testOB = cascaded_union(polygons).buffer(0)
    elif len(polygons) == 1:
        logger.info("Creating a %s from polygons[0]", polygons[0].geom_type)
        testOB = polygons[0].buffer(0)
    else:
        logger.error("No Polygons created, creating 1 meter circle on 0.0 island")
        testOB = Point( ([ 0.0, 0.0 ])).buffer(meter2deg(1.0))
    testOB = testOB.buffer(0)
    try:
        testOB = Polygon(testOB.exterior).buffer(meter2deg(1.0))
        logger.debug("Making Polygon from external coordinates from %s", testOB.exterior.geom_type)
    except:
        try:
            testOB = MultiPolygon(testOB.exterior).buffer(meter2deg(1.0))
            logger.debug("Making MultiPolygon from external coordinates from %s", testOB.exterior.geom_type)
        except:
            logger.error("Could not make Polygon of exterior coordinates")
            pass
    try:
        polygons = []
        polygons.append(testOB)
        logger.debug("Extracting interiors from testOB")
        testMe = testOB.interiors
        logger.debug("testOB have %s interiors", len(testMe))
        while testMe > 0:
            i = testMe[0]
            testMe.remove(i)
            polygons.append(Polygon(i).buffer(meter2deg(1.0)))
        testOB = cascaded_union(polygons).buffer(0)
        logger.debug("%s created with inner elements", testOB.geom_type)
    except:
        logger.debug("Could not make polygons of interiors")
        pass
    if testOB.is_valid:
        logger.debug("testOB is a valid %s", testOB.geom_type)
    else:
        logger.error("testOB is NOT a valid %s", testOB.geom_type)
        testOB = testOB.buffer(meter2deg(1.0)).buffer(0)
        logger.debug("Testing relation against track")
    if track.within(testOB) or track.intersects(testOB) or track.crosses(testOB) or track.touches(testOB) or testOB.contains(track):
        name = unicode(id)
        logger.info("Found id: %s", name)
        try:
            name = clean(json.loads(json.dumps(relationList[0]))['tags']['name'])
            tags.append(name)
            b_name = unidecode(name).encode('utf-8')
            b_name = unicode(b_name)
            tags.append(b_name)
            logger.info("Found name: %s/%s (%s/%s)", name, b_name, type(name), type(b_name))
        except:
            raise
        try:
            name = json.loads(json.dumps(relationList[0]))['tags']['name:en']
            tags.append(name)
            logger.info("Found name:en: %s (%s)", name, type(name))
        except:
            pass
        for l in lang:
            try:
                if l == "en":
                    continue
                string = clean(json.loads(json.dumps(relationList[0]))['tags']['name:{0}'.format(l)])
                tags.append(string)
                logger.info("Found name:%s: %s (%s)", l, string, type(string))
            except:
                pass
            try:
                string = clean(json.loads(json.dumps(relationList[0]))['tags']['official_name:{0}'.format(l)])
                tags.append(string)
                logger.info("Found official_name:%s: %s (%s)", l, string, type(string))
            except:
                pass
            
            try:
                string = clean(json.loads(json.dumps(relationList[0]))['tags']['alt_name:{0}'.format(l)])
                for i in string.split(";"):
                    tags.append(i)
                logger.info("Found alt_name:%s: %s (%s)", l, string, type(string))
            except:
                pass
            try:
                string = clean(json.loads(json.dumps(relationList[0]))['tags']['long_name:{0}'.format(l)])
                tags.append(string)
                logger.info("Found long_name:%s: %s (%s)", l, string, type(string))
            except:
                pass
        try:
            string = clean(json.loads(json.dumps(relationList[0]))['tags']['official_name'])
            tags.append(string)
            logger.info("Found official_name: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = json.loads(json.dumps(relationList[0]))['tags']['short_name']
            tags.append(string)
            logger.info("Found short_name: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = clean(json.loads(json.dumps(relationList[0]))['tags']['long_name'])
            tags.append(string)
            logger.info("Found long_name: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = clean(json.loads(json.dumps(relationList[0]))['tags']['alt_name'])
            for i in string.split(";"):
                tags.append(i)
            logger.info("Found alt_name: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = clean(json.loads(json.dumps(relationList[0]))['tags']['loc_name'])
            tags.append(string)
            logger.info("Found loc_name: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = clean(json.loads(json.dumps(relationList[0]))['tags']['old_name'])
            for i in string.split(";"):
                tags.append(i)
            logger.info("Found old_name: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = json.loads(json.dumps(relationList[0]))['tags']['ISO3166-1']
            tags.append(string)
            logger.info("Found ISO3166-1: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = json.loads(json.dumps(relationList[0]))['tags']['ISO3166-1:alpha2']
            tags.append(string)
            logger.info("Found ISO3166-1:alpha2: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = json.loads(json.dumps(relationList[0]))['tags']['ISO3166-1:alpha3']
            tags.append(string)
            logger.info("Found ISO3166-1:alpha3: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = json.loads(json.dumps(relationList[0]))['tags']['ISO3166-2']
            tags.append(string)
            logger.info("Found ISO3166-2: %s (%s)", string, type(string))
        except:
            pass
        try:
            string = json.loads(json.dumps(relationList[0]))['tags']['is_in:continent']
            tags.append(string)
            logger.info("Found is_in:continent: %s (%s)", string, type(string))
        except:
            pass
        try:
            if testOB.geom_type == "Polygon" or testOB.geom_type == "MultiPolygon":
                centroidLat = (testOB.centroid.y)
            else:
                centroidLat = 0.0
        except:
            centroidLat = 0.0
        area = int(testOB.area * SQKM * cos(centroidLat ) * 10.0) / 10.0
        if area < 0:
            area = -area
        try:
            al = json.loads(json.dumps(relationList[0]))['tags']['admin_level']
        except:
            al = '2'
        if testOB.geom_type == "Polygon":
            items = 1
        else:
            items = len(testOB)
        logger.info(u"GPX File is in %s (%s) covering %s km2 (no of Polygons: %s)", name, str(al), str(area), str(items) )
        print u"GPX is in {0} ({1})".format(name, al)
        mk_kml(testOB, id, name, al)
    else:
        name = unicode(id)
        logger.info("-- (not) -- Found id: %s", name)
        try:
            name = clean(json.loads(json.dumps(relationList[0]))['tags']['name'])
            logger.info("-- (not) -- Found name: %s/%s (%s)", name, unidecode(name), type(name))
        except:
            pass
        try:
            name = json.loads(json.dumps(relationList[0]))['tags']['name:en']
            logger.info("-- (not) -- Found name:en: %s (%s)", name, type(name))
        except:
            pass
        try:
            if testOB.geom_type == "Polygon" or testOB.geom_type == "MultiPolygon":
                centroidLat = (testOB.centroid.y)
            else:
                centroidLat = 0.0
        except:
            centroidLat = 0.0
        area = int(testOB.area * SQKM * cos(centroidLat ) * 10.0) / 10.0
        if area < 0:
            area = -area
        try:
            al = json.loads(json.dumps(relationList[0]))['tags']['admin_level']
        except:
            al = '2'
        logger.debug(u"GPX File is NOT in %s (%s) ~ %s km2", name, str(al), str(area))
        mk_kml(testOB, id, name, al)
        name = unicode(id)
        return False
### Here we should sleep for 3 seconds to avoid MultipleRequestsError from overpass, adjust time if problem persists
    time.sleep(3)
    if name == unicode(id):
        print "Not been able to capture name of this relation: {0}".format(name)
        return False
    return name

def mk_kml(ob, id, name, subdir="0"):
    return
    logger.debug("Creating KML")
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
            d = kml.Document(ns, str(id), '{0}'.format(unidecode(name)), 'Border visualization')
        else:
            d = kml.Document(ns, str(id), "Points", 'Point visualization')
        kf.append(d)
        p = kml.Placemark(ns, str(id), name, '{0}'.format(name), styles = [style])
        p.geometry = ob
        d.append(p)
        if subdir == "0":
            filename = u"./kml/"+unicode(id)+u"_"+name.replace(" ", "_")+u".kml"
        else:
            filename = u"./kml/"+unicode(subdir)+u"/"+name.replace(" ", "_")+u"_"+unicode(id)+u".kml"
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

def get_countries(minlat, minlon, maxlat, maxlon):
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
    api = overpass.API(timeout=600, endpoint=overpassServer)
    searchString = 'is_in;relation["type"="boundary"]["boundary"="administrative"]({0},{1},{2},{3});out ids;'.format(minlat,minlon,maxlat,maxlon)
    try:
        logger.debug(searchString)
        result = api.Get(searchString, responseformat="json")
    except overpass.errors.OverpassSyntaxError as e:
        logger.critical("OverpassSyntaxError caught in get_countries: %s", e)
        return False
    except overpass.errors.ServerRuntimeError as e:
        logger.critical("ServerRuntimeError from Overpass in get_countries: %s", e)
        return False
    except overpass.errors.UnknownOverpassError as e:
        logger.critical("UnknownOverpassError caught in get_countries: %s", e)
        return False
    try:
        json.loads(json.dumps(result))
#        json.loads(result)
    except TypeError:
        logger.error("json.TypeError in get_countries")
        sys.exit(1)
        return False
    except ValueError:
        logger.error("No Valid JSON Loaded (json.ValueError in get_countries): %s", result)
        sys.exit(1)
        return False
    try:
        myElements = json.loads(json.dumps(result))['elements']
    except:
        logger.error("json in get_countries does not contain ['elements']: %s", result)
        sys.exit(1)
    print myElements
    if len(myElements) < 1:
        logger.error("json in get_countries contains empty ['elements']! %s", result)
        sys.exit(1)
    logger.debug("get_countries passed all tests")
    return result

def get_relation(id):
#    searchString = '[out:json];relation({0});(._;>;);'.format(str(id))
#    searchString = '[out:json];relation({0});(._;>;);out meta;'.format(str(id))
#    searchString = 'relation({0});(._;>;);'.format(str(id))
    searchString = 'relation({0});>>;'.format(str(id))
    logger.debug(searchString)
    api = overpass.API(timeout=600, responseformat="json", endpoint=overpassServer)
    try:
        result = api.Get(searchString)
    except overpass.errors.OverpassSyntaxError as e:
        logger.critical("OverpassSyntaxError caught in get_relation: %s", e)
        return False
    return result

def get_relations(id, admin_level):
    # 3600000000
    id = id + 3600000000
    searchString = 'relation(area:{0})["type"="boundary"]["admin_level"="{1}"]["boundary"="administrative"];out ids;'.format(str(id), str(admin_level))
    logger.debug(searchString)
    api = overpass.API(timeout=600, responseformat="json", endpoint=overpassServer)
    try:
        result = api.Get(searchString)
    except overpass.OverpassSyntaxError:
        logger.critical("OverpassSyntaxError caught in get_relations")
        return False
    except overpass.TimeoutError:
        logger.error("overpass gave TimeoutError in get_relations")
        return False
    try:
        json.loads('{0}'.format(result))
    except TypeError:
        logger.error("json.TypeError in get_countries")
    except ValueError:
        logger.error("No Valid JSON Loaded (json.ValueError in get_relations)")
        return False
    try:
        json.loads('{0}'.format(result))['elements']
    except:
        logger.critical("json in get_relations does not contain ['elements']: %s", result)
        sys.exit(1)
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
trackptLength = len(track)
if len(track) > 1:
    mk_kml(LineString(track), 0, u'test_gpx')
    track = MultiPoint(track)
elif len(track) == 1:
    track = Point(track[0])
else:
    logger.critical("Selected GPX have no valid track points")
    sys.exit(0)
lats.sort()
lons.sort()
trackLength = int(deg2meter(LineString(track).length))/1000.0
if trackLength < 1.0:
    tags.append(u"Short Trace")
elif trackLength > 100.0:
    tags.append(u"Long Trace")
logger.debug("GPX File contains %s trackpoints with %s km.", str(len(lats)), str(trackLength))
toTest = []

gpxBbox = [ lats[0], lons[0], lats[len(lats) - 1], lons[len(lons) - 1] ]
result = False
while result == False:
    result = get_countries(gpxBbox[0], gpxBbox[1], gpxBbox[2], gpxBbox[3])
    if result == False:
        time.sleep(30)

myElements = json.loads(result)['elements']
for check in myElements:
    if check['tags']['admin_level'] == '2':
        for sub in check['members']:
            if sub['role'] == 'subarea' and sub['type'] == 'relation':
                toTest.append(sub['ref'])
        toTest.append(check['id'])

#toTest.append(59470)
if track.within(Point( ([ 0.0, 0.0 ]) ).buffer(meter2deg(1.0))):
    tags.append(u"0.0")
toTest.sort()
toTest = remove_duplicates(toTest)
logger.debug(toTest)

######
toTest = remove_duplicates(toTest)
logger.info("Relations to test: %s", toTest)
while len(toTest) > 0:
    executeTest = toTest[0]
    toTest.remove(executeTest)
    country = False
    country = test_relation(executeTest)
    if country == False:
        logger.info("Country %s (%s) is FALSE",executeTest, name)
        continue
    logger.debug("Executing subdivision for %s", country)
    if country == "Russia":
        logger.debug("%s: checking levels 3, 6, 8", country)
        result = False
        while result == False:
            result = get_relations(executeTest, 3)
            if result == False:
                time.sleep(10)
        myElements = json.loads(result)['elements']
        for check in myElements:
            treTest.append(check['id'])
        treTest = remove_duplicates(treTest)
        while len(treTest) > 0:
            i = treTest[0]
            treTest.remove(i)
            if not test_relation(i):
                continue
            result = False
            while result == False:
                result = get_relations(i, 6)
                if result == False:
                    time.sleep(10)
            myElements = json.loads(result)['elements']
            for check in myElements:
                seksTest.append(check['id'])
                seksTest = remove_duplicates(seksTest)
            while len(seksTest) > 0:
                j = seksTest[0]
                seksTest.remove(j)
                if not test_relation(j):
                    continue
                result = False
                while result == False:
                    result = get_relations(j, 8)
                    if result == False:
                        time.sleep(10)
                myElements = json.loads(result)['elements']
                for check in myElements:
                    atteTest.append(check['id'])
                atteTest = remove_duplicates(atteTest)
                while len(atteTest) > 0:
                    k = atteTest[0]
                    atteTest.remove(k)
                    if not test_relation(k):
                        continue
    elif country == "Brazil" or country == "Switzerland" or country == "Uruguay" or country == "Paraguay":
        logger.debug("%s: checking levels 4, 8", country)
        result = False
        while result == False:
            result = get_relations(executeTest, 4)
            if result == False:
                time.sleep(10)
        myElements = json.loads(result)['elements']
        for check in myElements:
            fireTest.append(check['id'])
        fireTest = remove_duplicates(fireTest)
        while len(fireTest) > 0:
            i = fireTest[0]
            fireTest.remove(i)
            if not test_relation(i):
                continue
            result = False
            while result == False:
                result = get_relations(i, 8)
                if result == False:
                    time.sleep(10)
            myElements = json.loads(result)['elements']
            for check in myElements:
                atteTest.append(check['id'])
            atteTest = remove_duplicates(atteTest)
            while len(atteTest) > 0:
                j = atteTest[0]
                atteTest.remove(j)
                if not test_relation(j):
                    continue
    elif country == "Norway" or country == "Sweden" or country == "Denmark":
        logger.debug("%s: checking levels 4, 7", country)
        result = False
        while result == False:
            result = get_relations(executeTest, 4)
            if result == False:
                time.sleep(10)
        myElements = json.loads(result)['elements']
        for check in myElements:
            fireTest.append(check['id'])
        fireTest = remove_duplicates(fireTest)
        while len(fireTest) > 0:
            i = fireTest[0]
            fireTest.remove(i)
            if not test_relation(i):
                continue
            result = False
            while result == False:
                result = get_relations(i, 7)
                if result == False:
                    time.sleep(10)
            myElements = json.loads(result)['elements']
            for check in myElements:
                syvTest.append(check['id'])
            syvTest = remove_duplicates(syvTest)
            while len(syvTest) > 0:
                j = syvTest[0]
                syvTest.remove(j)
                if not test_relation(j):
                    continue
    elif country == "Argentina" or country == "Portugal":
        logger.debug("%s: checking levels 6, 7", country)
        result = False
        while result == False:
            result = get_relations(executeTest, 4)
            if result == False:
                time.sleep(10)
        myElements = json.loads(result)['elements']
        for check in myElements:
            fireTest.append(check['id'])
        fireTest = remove_duplicates(fireTest)
        while len(fireTest) > 0:
            i = fireTest[0]
            fireTest.remove(i)
            if not test_relation(i):
                continue
            result = False
            while result == False:
                result = get_relations(i, 6)
                if result == False:
                    time.sleep(10)
            myElements = json.loads(result)['elements']
            for check in myElements:
                seksTest.append(check['id'])
            seksTest = remove_duplicates(seksTest)
            while len(seksTest) > 0:
                j = seksTest[0]
                seksTest.remove(j)
                if not test_relation(j):
                    continue
                result = False
                while result == False:
                    result = get_relations(j, 7)
                    if result == False:
                        time.sleep(10)
                myElements = json.loads(result)['elements']
                for check in myElements:
                    syvTest.append(check['id'])
                syvTest = remove_duplicates(syvTest)
                while len(syvTest) > 0:
                    k = syvTest[0]
                    syvTest.remove(k)
                    if not test_relation(k):
                        continue
    elif country == "Chile" or country == "Spain" or country == "United States" or "United Kingdom":
        logger.debug("%s: checking levels 4, 6, 8", country)
        result = False
        while result == False:
            result = get_relations(executeTest, 4)
            if result == False:
                time.sleep(10)
        myElements = json.loads(result)['elements']
        for check in myElements:
            fireTest.append(check['id'])
        fireTest = remove_duplicates(fireTest)
        while len(fireTest) > 0:
            i = fireTest[0]
            fireTest.remove(i)
            if not test_relation(i):
                continue
            result = False
            while result == False:
                result = get_relations(i, 6)
                if result == False:
                    time.sleep(10)
            myElements = json.loads(result)['elements']
            for check in myElements:
                seksTest.append(check['id'])
            seksTest = remove_duplicates(seksTest)
            while len(seksTest) > 0:
                j = seksTest[0]
                seksTest.remove(j)
                if not test_relation(j):
                    continue
                result = False
                while result == False:
                    result = get_relations(j, 8)
                    if result == False:
                        time.sleep(10)
                myElements = json.loads(result)['elements']
                for check in myElements:
                    atteTest.append(check['id'])
                atteTest = remove_duplicates(atteTest)
                while len(atteTest) > 0:
                    k = atteTest[0]
                    atteTest.remove(k)
                    if not test_relation(k):
                        continue
    elif country == "Czech":
        logger.debug("%s: checking levels 4, 6, 7, 8", country)
        result = False
        while result == False:
            result = get_relations(executeTest, 4)
            if result == False:
                time.sleep(10)
        myElements = json.loads(result)['elements']
        for check in myElements:
            fireTest.append(check['id'])
        fireTest = remove_duplicates(fireTest)
        while len(fireTest) > 0:
            i = fireTest[0]
            fireTest.remove(i)
            if not test_relation(i):
                continue
            result = False
            while result == False:
                result = get_relations(i, 6)
                if result == False:
                    time.sleep(10)
            myElements = json.loads(result)['elements']
            for check in myElements:
                seksTest.append(check['id'])
            seksTest = remove_duplicates(seksTest)
            while len(seksTest) > 0:
                j = seksTest[0]
                seksTest.remove(j)
                if not test_relation(j):
                    continue
                result = False
                while result == False:
                    result = get_relations(j, 7)
                    if result == False:
                        time.sleep(10)
                myElements = json.loads(result)['elements']
                for check in myElements:
                    syvTest.append(check['id'])
                syvTest = remove_duplicates(syvTest)
                while len(syvTest) > 0:
                    k = syvTest[0]
                    syvTest.remove(k)
                    if not test_relation(k):
                        continue
                    result = False
                    while result == False:
                        result = get_relations(k, 8)
                        if result == False:
                            time.sleep(10)
                    myElements = json.loads(result)['elements']
                    for check in myElements:
                        atteTest.append(check['id'])
                    atteTest = remove_duplicates(atteTest)
                    while len(atteTest) > 0:
                        l = atteTest[0]
                        atteTest.remove(l)
                        if not test_relation(l):
                            continue
    elif country == "Iceland":
        logger.debug("%s: checking levels 5, 6", country)
        result = False
        while result == False:
            result = get_relations(executeTest, 5)
            if result == False:
                time.sleep(10)
        myElements = json.loads(result)['elements']
        for check in myElements:
            femTest.append(check['id'])
        femTest = remove_duplicates(femTest)
        while len(femTest) > 0:
            i = femTest[0]
            femTest.remove(i)
            if not test_relation(i):
                continue
            result = False
            while result == False:
                result = get_relations(i, 6)
                if result == False:
                    time.sleep(10)
            myElements = json.loads(result)['elements']
            for check in myElements:
                seksTest.append(check['id'])
            seksTest = remove_duplicates(seksTest)
            while len(seksTest) > 0:
                j = seksTest[0]
                seksTest.remove(j)
                if not test_relation(j):
                    continue
    else:
        logger.warning("No country definition for %s", country)
        print "No rules defined for {0}".format(country)

try:
    tags.sort()
except:
    pass
tags = remove_duplicates(tags)
#print tags
myTags = ", ".join(tags)
myDescription = u"Track containing {0} trackpoints with a length of {2} km - bbox.{1}".format(trackptLength, track.bounds, trackLength)

#print myTags
#print type(myTags)
#print myTags, myDescription
logger.warning(myTags)

upload_gpx(file, myTags, myDescription )

logger.debug("Completed execution of %s\n\n\n", file)
