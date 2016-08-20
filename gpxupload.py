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
result = ""
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
    #    return
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
        logger.error("Failed to create KML")
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
        logger.critical("ERROR: Latitude %s equal %s - TERMINATING", str(minlat), str(maxlat))
        sys.exit(1)
    if minlon == maxlon:
        logger.critical("ERROR: Longitude %s equal %s - TERMINATING", str(minlon), str(maxlon))
        sys.exit(1)
    if minlat > maxlat:
        logger.error("ERROR: Latitude %s greater than %s - SWAPPING", str(minlat), str(maxlat))
        minlat, maxlat = swap(minlat, maxlat)
    if minlon > maxlon:
        logger.error("ERROR: Longitude %s greater than %s - SWAPPING", str(minlon), str(maxlon))
        minlon, maxlon = swap(minlon, maxlon)
    api = overpass.API(timeout=600)
#    searchString = '[out:json];relation["type"="boundary"]["admin_level"="2"]["boundary"="administrative"]({0},{1},{2},{3});'.format(minlat,minlon,maxlat,maxlon)
    searchString = '[out:json];relation["type"="boundary"]["admin_level"="2"]["boundary"="administrative"]({0},{1},{2},{3});out meta;'.format(minlat,minlon,maxlat,maxlon)
#    searchString = '[out:json];relation["type"="boundary"]["admin_level"="2"]["boundary"="administrative"]({0},{1},{2},{3});(._;>;);out body;'.format(minlat,minlon,maxlat,maxlon)
    try:
        logger.debug(searchString)
        #        print api.Get(searchString)
        result = api.Get(searchString)
#        print result
    except:
        logger.error("No search result returned")
        return False
    try:
        json.loads(result)
    except ValueError:
        logger.error("No Valid JSON Loaded")
        return False
    return result

def get_relation(id):
#    searchString = '[out:json];relation({0});(._;>;);'.format(str(id))
    searchString = '[out:json];relation({0});(._;>;);out meta;'.format(str(id))
    logger.debug(searchString)
    #  print searchString
    api = overpass.API(timeout=600)
    try:
        result = api.Get(searchString)
    except:
        return False
    return result

def get_relations(id, admin_level):
    # 3600000000
    id = id + 3600000000
#    searchString = '[out:json];relation(area:{0})["type"="boundary"]["admin_level"="{1}"]["boundary"="administrative"];'.format(str(id), str(admin_level))
    searchString = '[out:json];relation(area:{0})["type"="boundary"]["admin_level"="{1}"]["boundary"="administrative"];out meta;'.format(str(id), str(admin_level))
    logger.debug(searchString)
    #print searchString
    api = overpass.API(timeout=600)
    try:
        result = api.Get(searchString)
    except overpass.OverpassSyntaxError:
        return False
    except overpass.TimeoutError:
        return False
    except:
        return False
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
#    print payload
#    print type(uTags), type(uDescription), type(payload)
    try:
        url = "http://www.openstreetmap.org/api/0.6/gpx/create"
        files = {u'file': open(gpxFile, 'rb') }
        r = requests.post(url, auth=(userName, passWord), files=files, data=payload)
    except:
        logger.critical("Exception thrown in upload_gpx")
        raise
    if r.status_code == 200:
        print "Uploaded with success"
        #        print r.text
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

#upload_gpx(file, "um, does palavras, três palavras etiquete", "test upload")

tree = etree.parse(gpx_file)
root = tree.getroot()

lats = []
lons = []
track = []

for trk in root.findall('{http://www.topografix.com/GPX/1/1}trk'):
    for seg in trk.findall('{http://www.topografix.com/GPX/1/1}trkseg'):
        for point in seg.findall('{http://www.topografix.com/GPX/1/1}trkpt'):
            lats.append(point.get('lat'))
            lons.append(point.get('lon'))
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

####
#box.append( [ minlat, minlon, maxlat, maxlon ] ) ##
bbox.append( [ -34.0, -51.0, 5.0, -28.0 ] ) # Brazil
bbox.append( [ -9.0, -69.0, 0.0, -28.0 ] ) # Brazil
bbox.append( [ -34.0, -53.0, 2.0, -51.0 ] ) # Brazil
bbox.append( [ 2.0, -53.0, 6.0, -51.0 ] ) # Brazil/France
bbox.append( [ 23.0, 123.0, 34.0, 132.0 ] ) # Japan
bbox.append( [ 39.0, 124.0, 43.0, 132.0 ] ) # North Korea
bbox.append( [ 54.0, 77.0, 79.0, 108.0 ] ) # Russia
bbox.append( [ -60.0, 153.0, -49.0, 180.0 ] ) # New Zealand/Antarctica
bbox.append( [ 4.0, 116.0, 21.0, 129.0 ] ) # Philipines
bbox.append( [ 45.0, 135.0, 54.0, 180.0 ] ) # Russia
bbox.append( [ 32.0, 34.0, 34.0, 35.0 ] ) # Israel
bbox.append( [ -23.0, -80.0, -12.0, -68.0 ] ) # Chile, Peru
bbox.append( [ 6.0, -77.0, 14.0, -74.0 ] ) # Columbia
bbox.append( [ 18.0, -90.0, 24.0, -86.0 ] ) # Belize, Mexico
bbox.append( [ 0.0, -66.0, 6.0, -59.0 ] ) # Brazil, Guyana, Venezuela
bbox.append( [ -43.0, -63.0, -28.0, -59.0 ] ) # Argentina
bbox.append( [ -4.0, -71.0, 3.0, -69.0 ] ) # Brazil, Columbia
bbox.append( [ 2.0, -84.0, 6.0, -70.0 ] ) # Columbia
bbox.append( [ 6.0, -62.0, 10.0, -59.0 ] ) # Guyana, Venezuela
bbox.append( [ 11.0, -69.0, 13.0, -64.0 ] ) # Curação
bbox.append( [ -28.0, -73.0, -23.0, -63.0 ] ) # Argentina, Chile
bbox.append( [ 27.0, -120.0, 30.0, -106 ] ) # Mexico
bbox.append( [ 24.0, -120.0, 27.0, -100.0 ] ) # Mexico
bbox.append( [ 15.0, -88.0, 19.0, -79.0 ] ) # Honduras
bbox.append( [ 17.0, -68.0, 20.0, -64.0 ] ) # Puerto Rico
bbox.append( [ 20.0, 87.0, 26.0, 93.0 ] ) # Bangladesh
bbox.append( [ 21.0, 119.0, 26.0, 123.0 ] ) # Taiwan
bbox.append( [ 32.0, 35.0, 35.0, 37.0 ] ) # Israel, Libanon
bbox.append( [ 10.0, 102.0, 15.0, 108.0 ] ) # Cambodia
bbox.append( [ -45.0, 109.0, -9.0, 163.0 ] ) # Australia
bbox.append( [ 34.0, 124.0, 39.0, 132.0 ] ) # South Korea
bbox.append( [ 56.0, 164.0, 84.0, 180.0 ] ) # Russia
bbox.append( [ -6.0, -82.0, 2.0, -74.0 ] ) # Equador, Columbia, Peru
bbox.append( [ 27.0, -99.0, 30.0, -84.0 ] ) # USA
bbox.append( [ 30.0, -120, 33.0, -104.0 ] ) # USA, Mexico
bbox.append( [ -40.0, -59.0, -35.0, -53.0 ] ) # Argentina
bbox.append( [ -4.0, -74.0, 2.0, -71.0 ] ) # Peru, Columbia
bbox.append( [ 0.0, -69.0, 3.0, -66.0 ] ) # Brazil, Columbia, Venezuela
bbox.append( [ -23.0, -68.0, -19.0, -63.0 ] ) # Bolivia, Chile, Argentila
bbox.append( [ 17.0, -76.0, 19.0, -73.0 ] ) # Haiti
bbox.append( [ -51.0, -78.0, -28.0, -71.0 ] ) # Chile, Argentina
bbox.append( [ 17.0, -73.0, 24.0, -68.0 ] ) # Haiti, Dominican Republic
bbox.append( [ 12.0, -71.0, 13.0, -69.0 ] ) # Aruba
bbox.append( [ 10.0, -88.0, 15.0, -80.0 ] ) # Nicaragua
bbox.append( [ 27.0, -106.0, 30.0, -99.0 ] ) # USA, Mexico
bbox.append( [ 24.0, -100.0, 27.0, -96.0 ] ) # USA, Mexico
bbox.append( [ 13.0, -93.0, 18.0, -88.0 ] ) # Guatamala
bbox.append( [ 56.0, -9.0, 60.0, -5.0 ] ) # Scotland
bbox.append( [ 79.0, 35.0, 82.0, 108.0 ] ) # Franz Joseph Land
bbox.append( [ 54.0, 13.0, 55.0, 15.0 ] ) # Germany, Poland
bbox.append( [ 44.0, 9.0, 47.0, 14.0 ] ) # Italy, Switzerland, Austria, Slovenia, Croatia
bbox.append( [ 43.0, 8.0, 44.0, 12.0 ] ) # Italy
bbox.append( [ 42.0, 10.0, 43.0, 13.0 ] ) # Italy
bbox.append( [ 30.0, -8.0, 36.0, -6.0 ] ) # Marocco
bbox.append( [ -28.0, 19.0, -17.0, 30.0 ] ) # Botswana
bbox.append( [ -32.0, 30.0, -28.0, 33.0 ] ) # South Africa
bbox.append( [ -1.0, 71.0, 12.0, 75.0 ] ) # Maldives
bbox.append( [ 5.0, 79.0, 11.0, 83.0 ] ) # Sri Lanka
bbox.append( [ 38.0, 39.0, 44.0, 51.0 ] ) # Caucasus
bbox.append( [ 34.0, 32.0, 36.0, 35.0 ] ) # Cyprus
bbox.append( [ 28.0, 46.0, 31.0, 49.0 ] ) # Kuwait
bbox.append( [ 24.0, 50.0, 27.0, 52.0 ] ) # Qatar, Bahrain
bbox.append( [ 13.0, 36.0, 19.0, 43.0 ] ) # Eritrea
bbox.append( [ 41.0, 13.0, 44.0, 17.0 ] ) # Italy
bbox.append( [ 49.0, 7.0, 51.0, 12.0 ] ) # Germany
bbox.append( [ 54.0, 108.0, 82.0, 164.0 ] ) # Russia
bbox.append( [ 26.0, 79.0, 31.0, 88.0 ] ) # Nepal
bbox.append( [ 27.0, -13.0, 36.0, -8.0 ] ) # Marocco
bbox.append( [ 44.0, 5.0, 49.0, 9.0 ] ) # France, Italy, Switzerland, Germany
bbox.append( [ 0.0, -55.0, 7.0, -53.0 ] ) # Brazil, French Guiana, Suriname
bbox.append( [ -19.0, -68.0, -9.0, -53.0 ] ) # Brazil, Bolivia
bbox.append( [ -34.0, -59.0, -30.0, -53.0 ] ) # Uruguay
bbox.append( [ -35.0, -58.0, -34.0, -53.0 ] ) # Uruguay
bbox.append( [ -35.0, -59.0, -34.0, -58.0 ] ) # Buenos Aires AR
bbox.append( [ -35.0, -58.0, -34.0, -57.0 ] ) # Argentina/Uruguay
bbox.append( [ -35.0, -57.0, -34.0, -53.0 ] ) # Montevideo
bbox.append( [ -57.0, -69.0, -51.0, -63.0 ] ) # Tierra del Fuego AR
bbox.append( [ -54.0, -63.0, -50.0, -57.0 ] ) # Falklands
bbox.append( [ -57.0, -76.0, -52.0, -57.0 ] ) # Tierra del Fuego CL
bbox.append( [ 14.0, -26.0, 18.0, -22.0 ] ) # Cap Verde
bbox.append( [ 27.0, -19.0, 31.0, -13.0 ] ) # Canaries
bbox.append( [ 36.0, -10.0, 41.0, -8.0 ] ) # Portugal
bbox.append( [ 36.0, -8.0, 41.0, -6.0 ] ) # Portugal, Spain
bbox.append( [ 41.0, -10.0, 43.0, -6.0 ] ) # Portugal, Spain
bbox.append( [ 37.0, -6.0, 42.0, 2.0 ] ) # Spain
bbox.append( [ 43.0, -10.0, 44.0, -6.0 ] ) # Spain
bbox.append( [ 38.0, 2.0, 42.0, 5.0 ] ) # Spain
bbox.append( [ 42.0, 2.0, 43.0, 4.0 ] ) # Spain, France
bbox.append( [ 42.0, -6.0, 44.0, 1.0 ] ) # Spain, France
bbox.append( [ 42.0, 1.0, 44.0, 7.0 ] ) # France
bbox.append( [ 36.0, -5.0, 37.0, -1.0 ] ) # Spain
bbox.append( [ 35.0, -4.0, 36.0, -2.0 ] ) # Spain, Marocco
bbox.append( [ 35.0, 14.0, 37.0, 15.0 ] ) # Malta
bbox.append( [ 63.0, 20.0, 68.0, 26.0 ] ) # Finland, Sweden
bbox.append( [ 49.0, 5.0, 51.0, 7.0 ] ) # Luxembourg
bbox.append( [ 58.0, 3.0, 66.0, 11.0 ] ) # Norway
bbox.append( [ 57.0, 6.0, 58.0, 8.0, ] ) # Norway
bbox.append( [ 57.0, 8.0, 58.0, 11.0 ] ) # Denmark
bbox.append( [ 56.0, 6.0, 57.0, 11.0 ] ) # Denmark
bbox.append( [ 56.0, 11.0, 59.0, 12.0 ] ) # Denmark, Sweeden, Norway
bbox.append( [ 55.0, 12.0, 57.0, 13.0 ] ) # Denmark, Sweden
bbox.append( [ 59.0, 11.0, 68.0, 12.0 ] ) # Norway, Sweden
bbox.append( [ 56.0, 14.0, 57.0, 19.0 ] ) # Sweden
bbox.append( [ 57.0, 12.0, 73.0, 20.0 ] ) # Norway, Sweden
bbox.append( [ 68.0, 20.0, 73.0, 28.0 ] ) # Norway, Sweden, Finland
bbox.append( [ 68.0, 28.0, 73.0, 32.0 ] ) # Norway, Russia
bbox.append( [ 55.0, 13.0, 57.0, 14.0 ] ) # Sweden
bbox.append( [ 54.0, 14.0, 56.0, 16.0 ] ) # Bornholm
bbox.append( [ 54.0, 6.0, 56.0, 12.0 ] ) # Denmark, Germany
bbox.append( [ 54.0, 12.0, 55.0, 13.0 ] ) # Denmark, Germany
bbox.append( [ 51.0, 3.0, 54.0, 8.0 ] ) # Netherland, Belgium, Germany
bbox.append( [ 51.0, 2.0, 52.0, 3.0 ] ) # Belgium
bbox.append( [ 49.0, 2.0, 51.0, 5.0 ] ) # Belgium, France
bbox.append( [ 51.0, 1.0, 52.0, 2.0 ] ) # Dover Straight
bbox.append( [ 35.0, -5.0, 36.0, -4.0 ] ) # Marocco
bbox.append( [ -16.0, 10.0, -7.0, 16.0 ] ) # Angola
bbox.append( [ -16.0, 10.0, -9.0, 21.0 ] ) # Angola
bbox.append( [ -7.0, 10.0, -4.0, 14.0 ] ) # Angola, Cabinda, Congo, Congo DR
bbox.append( [ 0.0, 9.0, 3.0, 12.0 ] ) # Equatorial Guinea
bbox.append( [ -90.0, -91.0, -60.0, -44.0 ] ) # Antarctica - Graham Land
bbox.append( [ -90.0, -180.0, -60.0, -91.0 ] ) # Antarctica
bbox.append( [ -90.0, -44.0, -61.0, 180.0 ] ) # Antarctica
bbox.append( [ -9.0, -15.0, -7.0, -14.0] ) # Ascension
bbox.append( [ -17.0, -6.0, -15.0, -5.0 ] ) # St. Helena
bbox.append( [ -38.0, -13.0, -37.0, -12.0 ] ) # Trista da Cunha
bbox.append( [ -41.0, -11.0, -40.0, -9.0 ] ) # Gough Island
bbox.append( [ -55.0, 2.0, -54.0, 4.0 ] ) # Bouvet Island
bbox.append( [ -61.0, -44.0, -52.0, -23.0 ] ) # South Georgia & South Sandwich Islands
bbox.append( [ 35.0, -32.0, 41.0, -23.0 ] ) # Azores
bbox.append( [ 32.0, -18.0, 34.0, -15.0 ] ) # Madeira
bbox.append( [ 63.0, -26.0, 68.0, -12.0 ] ) # Iceland
bbox.append( [ 70.0, -11.0, 72.0, -7.0 ] ) # Jan Mayen
bbox.append( [ 74.0, 18.0, 75.0, 20.0 ] ) # Bjørnøya
bbox.append( [ 76.0, 9.0, 81.0, 35.0 ] ) # Svalbard
bbox.append( [ 57.0, -14.0, 58.0, -13.0 ] ) # Rockall
bbox.append( [ 61.0, -8.0, 63.0, -6.0 ] ) # Føroyar
bbox.append( [ 32.0, -65.0, 33.0, -64.0 ] ) # Bermuda
bbox.append( [ 24.0, -79.0, 28.0, -73.0 ] ) # Bahamas
bbox.append( [ 24.0, -80.0, 28.0, -79.0 ] ) # Bahamas, USA
bbox.append( [ 24.0, -81.0, 25.0, -80.0 ] ) # Bahamas, USA
bbox.append( [ 24.0, -84.0, 30.0, -81.0 ] ) # USA
bbox.append( [ 33.0, -126.0, 41.0, -69.0 ] ) # USA
bbox.append( [ 51.0, -168.0, 86.0, -142.0 ] ) # USA
bbox.append( [ 41.0, -126.0, 48.0, -94.0 ] ) # USA
bbox.append( [ 18.0, -179.0, 26.0, -152.0 ] ) # USA
bbox.append( [ -52.0, -78.0, -51.0, -69.0 ] ) # Chile, Argentina
bbox.append( [ -30.0, -59.0, -28.0, -53.0 ] ) # Brazil, Argentina
bbox.append( [ 50.0, -180.0, 56.0, -168.0 ] ) # Aleutian Islands
bbox.append( [ 50.0, 164.0, 56.0, 180.0 ] ) # Aleutian Islands
bbox.append( [ 56.0, -180.0, 86.0, -171.0 ] ) # Russia
bbox.append( [ 41.0, -94.0, 50.0, -66.0 ] ) # USA, Canada
bbox.append( [ 48.0, -129.0, 50.0, -94.0 ] ) # USA, Canada
bbox.append( [ 58.0, -142.0, 86.0, -140.0 ] ) # USA, Canada
bbox.append( [ 41.0, -66.0, 50.0, -50.0 ] ) # Canada
bbox.append( [ 19.0, -86.0, 24.0, -73.0 ] ) # Cuba
bbox.append( [ 17.0, -79.0, 19.0, -76.0 ] ) # Jamaica
bbox.append( [ 55.0, -171.0, 84.0, -168.0 ] ) # Bering Streight
bbox.append( [ 50.0, -140.0, 63.0, -52.0 ] ) # Canada
bbox.append( [ 63.0, -140.0, 86.0, -76.0 ] ) # Canada
bbox.append( [ 59.0, -76.0, 86.0, -26.0 ] ) # Greenland
bbox.append( [ 68.0, -26.0, 86.0, -11.0 ] ) # Greenland
bbox.append( [ 35.0, -6.0, 37.0, -5.0 ] ) # Gibraltar
bbox.append( [ -31.0, 26.0, -28.0, 30.0 ] ) # Lesoto
bbox.append( [ -28.0, 30.0, -25.0, 33.0 ] ) # Swaziland
bbox.append( [ -28.0, -63.0, -19.0, -53.0 ] ) # Paraguay
bbox.append( [ 25.0, -81.0, 30.0, -80.0 ] ) # USA
bbox.append( [ -34.0, -82.0, -33.0, -78.0 ] ) # Easter Island?
bbox.append( [ -28.0, -110.0, -27.0, -109.0 ] ) # Easter Island
bbox.append( [ -26.0, -132.0, -23.0, -124.0 ] ) # Pitcairn
bbox.append( [ 41.0, 12.0, 42.0, 13.0 ] ) # Vatican, Italy
bbox.append( [ 43.0, 12.0, 44.0, 13.0 ] ) # San Marino, Italy
bbox.append( [ 43.0, 7.0, 44.0, 8.0 ] ) # Monaco, France
bbox.append( [ 42.0, 1.0, 43.0, 2.0 ] ) # Andorra, Spain, France
bbox.append( [ 47.0, 9.0, 48.0, 10.0 ] ) # Lichtenstein, Austria, Switzerland
bbox.append( [ 1.0, 103.0, 2.0, 105.0 ] ) # Singapore, Indonesia, Malaysia
bbox.append( [ 10.0, 41.0, 13.0, 44.0 ] ) # Djibouti
bbox.append( [ -2.0, 5.0, -1.0, 6.0 ] ) # Annobon
bbox.append( [ -1.0, 6.0, 1.0, 7.0 ] ) # Sao Tome
bbox.append( [ 1.0, 7.0, 2.0, 8.0 ] ) # Principe
bbox.append( [ 3.0, 8.0, 4.0, 9.0 ] ) # Bioko
bbox.append( [ 3.0, 114.0, 6.0, 116.0 ] ) # Brunei
bbox.append( [ 22.0, 113.0, 23.0, 115.0 ] ) # Hong Kong, Macau
bbox.append( [ 26.0, 88.0, 29.0, 93.0 ] ) # Buthan
bbox.append( [ -21.0, 57.0, -19.0, 58.0 ] ) # Mauritiuz
bbox.append( [ -22.0, 55.0, -20.0, 57.0 ] ) # Reunion
bbox.append( [ -20.0, 63.0, -19.0, 64.0 ] ) # Rodrigues
bbox.append( [ -13.0, 96.0, -11.0, 97.0 ] ) # Keeling
bbox.append( [ -11.0, 105.0, -10.0, 106.0 ] ) # Christmas Island
bbox.append( [ -9.0, 69.0, -4.0, 75.0 ] ) # British Indian Ocean Territory
bbox.append( [ -51.0, 68.0, -48.0, 71.0 ] ) # French Southern Antarctic Lands
bbox.append( [ -54.0, 72.0, -52.0, 74.0 ] ) # Heard & McDonald Islands
bbox.append( [ -38.0, 77.0, -37.0, 78.0 ] ) # Ile Amsterdam
bbox.append( [ -1.0, 72.0, 9.0, 72.0 ] ) # Maldives
bbox.append( [ -17.0, 59.0, -16.0, 60.0 ] ) # Coco Island
bbox.append( [ 51.0, -11.0, 56.0, -5.0 ] ) # Ireland, Northern Ireland, Wales
bbox.append( [ 49.0, -7.0, 51.0, 2.0 ] ) # England, France
bbox.append( [ 51.0, -6.0, 52.0, 1.0 ] ) # England
bbox.append( [ 52.0, -5.0, 61.0, 3.0 ] ) # England, Scotland, Wales, Orkeney
bbox.append( [ 44.0, -7.0, 49.0, 5.0 ] ) # France
bbox.append( [ 38.0, 7.0, 43.0, 10.0 ] ) # Corsica, Sardinia
bbox.append( [ 0.0, -59.0, 9.0, -55.0 ] ) # French Guiana, Suriname, Brazil, Guyana
bbox.append( [ -51.0, -71.0, -28.0, -63.0 ] ) # Argentina
bbox.append( [ -12.0, -74.0, -4.0, -68.0 ] ) # Brazil, Bolivia, Peru
bbox.append( [ 6.0, -84.0, 10.0, -77.0 ] ) # Panama, Columbia, Costa Rica
bbox.append( [ 30.0, -104.0, 33.0, -78.0 ] ) # USA
bbox.append( [ -49.0, 163.0, -32.0, 180.0 ] ) # New Zealand
bbox.append( [ -2.0, -94.0, 6.0, -84.0 ] ) # Galapagos
bbox.append( [ 27.0, 32.0, 32.0, 35.0 ] ) # Sinai
bbox.append( [ 63.0, 26.0, 68.0, 32.0 ] ) # Russia, Finland
bbox.append( [ 48.0, 9.0, 49.0, 14.0 ] ) # Germany, Austria, Czech
bbox.append( [ 37.0, 10.0, 41.0, 19.0 ] ) # Italy
bbox.append( [ 35.0, 35.0, 38.0, 43.0 ] ) # Turkey, Syria, Iraq
bbox.append( [ 5.0, 75.0, 12.0, 79.0 ] ) # India
bbox.append( [ -12.0, 49.0, -3.0, 61.0 ] ) # Seyshelles
bbox.append( [ -32.0, 163.0, -25.0, 180.0 ] ) # Norfolk Island
bbox.append( [ -46.0, -180.0, -40.0, -170.0 ] ) # Catham Island
bbox.append( [ 41.0, 132.0, 45.0, 138.0 ] ) # Russia
bbox.append( [ 2.0, 100.0, 7.0, 105.0 ] ) # Malaysia
bbox.append( [ 30.0, 72.0, 38.0, 81.0 ] ) # Kashmir
bbox.append( [ -9.0, 140.0, 1.0, 163.0 ] ) # Papua New Guinea
bbox.append( [ 18.0, -93.0, 24.0, -90.0 ] ) # Mexico
bbox.append( [ 41.0, 87.0, 54.0, 120.0 ] ) # Mongolia
bbox.append( [ 45.0, 132.0, 54.0, 135.0 ] ) # China, Russia
bbox.append( [ 30.0, 132.0, 41.0, 138.0 ] ) # Japan
bbox.append( [ -9.0, 116.0, 4.0, 140.0 ] ) # Indonesia
bbox.append( [ 11.0, 79.0, 26.0, 87.0 ] ) # India
bbox.append( [ -27.0, 42.0, -12.0, 55.0 ] ) # Madagaskar
bbox.append( [ -31.0, 14.0, -28.0, 26.0 ] ) # South Africa
bbox.append( [ -17.0, 10.0, -16.0, 21.0 ] ) # Angola
bbox.append( [ 13.0, -120, 24.0, -93.0 ] ) # Mexico
bbox.append( [ -12.0, -82.0, -6.0, -74.0 ] ) # Peru
bbox.append( [ 3.0, -70.0, 6.0, -66.0 ] ) # Colombia, Venezuela
bbox.append( [ -50.0, 30.0, -40.0, 60.0 ] ) # Indian Ocean Territory
bbox.append( [ 0.0, 41.0, 10.0, 58.0 ] ) # Somalia, Etiopia
bbox.append( [ 30.0, 7.0, 37.0, 14.0 ] ) # Tunisia
bbox.append( [ -5.0, 28.0, -1.0, 31.0 ] ) # Burundi, Rwanda
bbox.append( [ 43.0, 120.0, 54.0, 132.0 ] ) # China, Russia
bbox.append( [ 30.0, 138.0, 45.0, 155.0 ] ) # Japan
bbox.append( [ -25.0, 163.0, -6.0, 174.0 ] ) # Vanuatu
bbox.append( [ 6.0, -74.0, 12.0, -69.0 ] ) # Colombia, Venezuela
bbox.append( [ 41.0, 10.0, 42.0, 12.0 ] ) # Italia
bbox.append( [ 38.0, 19.0, 43.0, 22.0 ] ) # Albania
bbox.append( [ 13.0, 43.0, 19.0, 53.0 ] ) # Yemen
bbox.append( [ 12.0, 68.0, 30.0, 79.0 ] ) # India
bbox.append( [ 59.0, 20.0, 63.0, 32.0 ] ) # Finland, Estonia
bbox.append( [ 51.0, 8.0, 54.0, 16.0 ] ) # Germany, Polan
bbox.append( [ 6.0, -69.0, 11.0, -62.0 ] ) # Venezuela
bbox.append( [ -37.0, 15.0, -31.0, 30.0 ] ) # South Africa
bbox.append( [ -28.0, 10.0, -17.0, 19.0 ] ) # Namibia
bbox.append( [ 10.0, 44.0, 13.0, 57.0 ] ) # Gulf of Aden
bbox.append( [ 34.0, 120.0, 43.0, 124.0 ] ) # China
bbox.append( [ -9.0, 103.0, 1.0, 116.0 ] ) # Indonesia
bbox.append( [ 6.0, -88.0, 10.0, -84.0 ] ) # Costa Rica
bbox.append( [ 10.0, -62.0, 12.0, -60.0 ] ) # Trinidad & Tobago
bbox.append( [ 12.0, -74.0, 14.0, -71.0 ] ) # Colombia
bbox.append( [ 37.0, 7.0, 38.0, 10.0 ] ) # Tunisia
bbox.append( [ 22.0, 52.0, 27.0, 57.0 ] ) # UAE
bbox.append( [ 29.0, 35.0, 32.0, 36.0 ] ) # Israel, Palestina, Jordan
bbox.append( [ 47.0, 10.0, 48.0, 14.0 ] ) # Austria
bbox.append( [ 57.0, 20.0, 59.0, 32.0 ] ) # Estonia
bbox.append( [ -12.0, 42.0, 0.0, 49.0 ] ) # Indian Ocean
bbox.append( [ 31.0, 81.0, 41.0, 123.0 ] ) # China
bbox.append( [ -9.0, 94.0, 2.0, 103.0 ] ) # Indonesia
bbox.append( [ 7.0, 102.0, 10.0, 116.0 ] ) # Vietnam
bbox.append( [ 56.0, 32.0, 79.0, 77.0 ] ) # Russia
bbox.append( [ 11.0, -64.0, 13.0, -62.0 ] ) # Caribbean
bbox.append( [ 19.0, 52.0, 22.0, 63.0 ] ) # Oman
bbox.append( [ 41.0, 17.0, 44.0, 19.0 ] ) # Montenegro, Bosnia
bbox.append( [ 2.0, 92.0, 7.0, 100.0 ] ) # Indonesia
bbox.append( [ 32.0, 37.0, 35.0, 42.0 ] ) # Syria
bbox.append( [ 36.0, 26.0, 38.0, 35.0 ] ) # Turkey
bbox.append( [ -25.0, 174.0, -14.0, 180.0 ] ) # Fiji
bbox.append( [ 4.0, 129.0, 13.0, 140.0 ] ) # Palau
bbox.append( [ 29.0, 88.0, 31.0, 123.0 ] ) # China
bbox.append( [ 1.0, 105.0, 3.0, 116.0 ] ) # Indonesia, Malaysia
bbox.append( [ 30.0, 60.0, 38.0, 72.0 ] ) # Afganistan
bbox.append( [ 18.0, 2.0, 38.0, 7.0 ] ) # Algeria
bbox.append( [ 30.0, -6.0, 35.0, -2.0 ] ) # Morocco
bbox.append( [ 12.0, -62.0, 20.0, -58.0 ] ) # Caribbean
bbox.append( [ 24.0, 36.0, 28.0, 50.0 ] ) # Saudi-Arabia
bbox.append( [ 24.0, 35.0, 29.0, 36.0 ] ) # Saudi-Arabia
bbox.append( [ 36.0, 19.0, 38.0, 26.0 ] ) # Greece
bbox.append( [ 13.0, 53.0, 19.0, 60.0 ] ) # Oman
bbox.append( [ 22.0, 61.0, 30.0, 68.0 ] ) # Pakistan
bbox.append( [ 3.0, 105.0, 7.0, 114.0 ] ) # Malaysia
bbox.append( [ 16.0, -64.0, 20.0, -62.0 ] ) # Caribbean
bbox.append( [ 10.0, -18.0, 17.0, -11.0 ] ) # Senegal, Gambia, Guinea-Bissau
bbox.append( [ 7.0, 91.0, 15.0, 96.0 ] ) # Andaman
bbox.append( [ 7.0, 140.0, 30.0, 150.0 ] ) # Mariana Islands
bbox.append( [ 49.0, 12.0, 51.0, 19.0 ] ) # Czech
bbox.append( [ 56.0, 19.0, 57.0, 32.0 ] ) # Latvia
bbox.append( [ 19.0, 38.0, 24.0, 52.0 ] ) # Saudi-Arabia
bbox.append( [ 3.0, 9.0, 7.0, 12.0 ] ) # Cameroon
bbox.append( [ 10.0, 108.0, 18.0, 116.0 ] ) # Vietnam
bbox.append( [ 26.0, 99.0, 29.0, 123.0 ] ) # China
bbox.append( [ 22.0, 57.0, 24.0, 61.0 ] ) # Oman
bbox.append( [ -1.0, 30.0, 5.0, 35.0 ] ) # Uganda
bbox.append( [ 34.0, 19.0, 36.0, 32.0 ] ) # Greece
bbox.append( [ 54.0, 16.0, 56.0, 27.0 ] ) # Lituania, Kaliningrad
bbox.append( [ 44.0, 14.0, 49.0, 19.0 ] ) # Croatia
bbox.append( [ 28.0, 36.0, 32.0, 39.0 ] ) # Jordan
bbox.append( [ 19.0, 35.0, 24.0, 38.0 ] ) # Egypt, Sudan
bbox.append( [ 18.0, -1.0, 37.0, 2.0 ] ) # Algeria
bbox.append( [ -4.0, 7.0, 0.0, 14.0 ] ) # Gabon
bbox.append( [ -27.0, 33.0, -25.0, 42.0 ] ) # Mosambique
bbox.append( [ 30.0, -2.0, 36.0, -1.0 ] ) # Algeria
bbox.append( [ 6.0, -15.0, 10.0, -10.0 ] ) # Sierra Leone
bbox.append( [ -5.0, 35.0, 0.0, 42.0 ] ) # Kenya
bbox.append( [ 38.0, 22.0, 42.0, 27.0 ] ) # Greece
bbox.append( [ 51.0, 16.0, 54.0, 27.0 ] ) # Poland
bbox.append( [ 28.0, 39.0, 32.0, 46.0 ] ) # Saudi-Arabia, Iraq
bbox.append( [ 38.0, 27.0, 42.0, 39.0 ] ) # Turkey
bbox.append( [ 24.0, 57.0, 30.0, 61.0 ] ) # Iran
bbox.append( [ 34.0, 15.0, 37.0, 19.0 ] ) # Italia
bbox.append( [ -5.0, 31.0, -1.0, 35.0 ] ) # Tanzania
bbox.append( [ 7.0, 96.0, 15.0, 102.0 ] ) # Thailand
bbox.append( [ 21.0, 115.0, 26.0, 119.0 ] ) # China
bbox.append( [ 6.0, 114.0, 7.0, 116.0 ] ) # det var en holme der...
bbox.append( [ 1.0, 150.0, 30.0, 180.0 ] ) # Marshall Islands, Micronesia
bbox.append( [ 43.0, 19.0, 47.0, 22.0 ] ) # Serbia
bbox.append( [ 0.0, 35.0, 5.0, 41.0 ] ) # Kenya
bbox.append( [ -7.0, 14.0, -1.0, 28.0 ] ) # DR Congo Kinshasa (Zaire)
bbox.append( [ 15.0, 91.0, 20.0, 99.0 ] ) # Myanmar (Burma)
bbox.append( [ 18.0, 108.0, 22.0, 115.0 ] ) # China
bbox.append( [ 23.0, 99.0, 26.0, 115.0 ] ) # China
bbox.append( [ 1.0, 140.0, 7.0, 150.0 ] ) # det var en holme der...
bbox.append( [ -6.0, 163.0, 1.0, 180.0 ] ) # Nauru
bbox.append( [ 0.0, -180.0, 18.0, -150.0 ] ) # Kiribati
bbox.append( [ -2.0, -120.0, 13.0, -94.0 ] ) # Clipperton Island
bbox.append( [ 21.0, -19.0, 27.0, 8.0 ] ) # Western Sahara
bbox.append( [ 18.0, 7.0, 30.0, 14.0 ] ) # Algeria, Libya, Niger
bbox.append( [ 27.0, 50.0, 28.0, 57.0 ] ) # Iran
bbox.append( [ -25.0, 34.0, -17.0, 42.0 ] ) # Mosambique
#bbox.append( [ -89.0, -179.9, 89.0, 179.9 ] )
mk_kml(cascaded_union(polygons), 0, u"bbox")
for i in bbox:
    sPoints = []
    sPoints.append( ([ i[1], i[0] ]) )
    sPoints.append( ([ i[3], i[0] ]) )
    sPoints.append( ([ i[3], i[2] ]) )
    sPoints.append( ([ i[1], i[2] ]) )
    testOB = Polygon(sPoints)
    minlon, minlat, maxlon, maxlat = testOB.bounds
    if track.within(testOB) or track.intersects(testOB):
        result = False
        while result == False:
            result = get_countries(minlat,minlon,maxlat,maxlon)
            if result == False:
                time.sleep(30)
        myElements = json.loads(result)['elements']
        for check in myElements:
            for sub in check['members']:
                if sub['role'] == 'subarea' and sub['type'] == 'relation':
                    toTest.append(sub['ref'])
            toTest.append(check['id'])
    polygons.append(testOB)
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
    #    print executeTest, toTest
    country = False
    country = test_relation(executeTest)
    if country == False:
        logger.info("Country %s (%s) is FALSE",executeTest, name)
        #        print "Country {0} ({1}) is FALSE".format(executeTest, name)
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
