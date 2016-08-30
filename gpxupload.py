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
overpassServer = "http://overpass-api.de/api/interpreter" # Default
#overpassServer = "http://overpass.osm.rambler.ru/cgi/interpreter"
#overpassServer = "http://api.openstreetmap.fr/oapi/interpreter"
#overpassServer = "http://overpass.osm.ch/api/interpreter"
api = overpass.API(timeout=600, endpoint=overpassServer)

#if speedups.available:
if False:
    speedups.enable()
    logger.info("Speedups enabled\n")
else:
    logger.debug("Speedups not enabled, executing default\n")

no_upload = True
no_kml = False

lang = [ 'en', 'pt', 'no' ]
tags = []
SQKM = ( (60.0 * 1.852) * (60.0 * 1.852) )
result = ""
name = u"?"
file = ""

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

def mk_kml(ob, id, name, subdir="0"):
    if no_kml:
        return
    logger.debug("Creating KML")
    filename = u"./kml/000_Default.kml"
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
    print tags

def build_object(id,al, name=u"Default"):
    shape = Point(0.0,0.0).buffer(0.0000001)
    myID = id + 3600000000
    result = False
    while result == False:
        result = get_data('relation(area:{1})["type"="boundary"]["boundary"="administrative"]["admin_level"="{0}"];out geom;'.format(al, myID))
        time.sleep(30)
    # Code to convert JSON data to shapely geometry
    myElements = json.loads(json.dumps(result))['elements']
    myMembers = []
    for i in myElements:
        for j in i['members']:
            myMembers.append(j)
    myWays = []
    for way in myMembers:
        if way['type'] != 'way':
            continue
        sPoints = []
        try:
            for i in way['geometry']:
                if way['type'] != 'way':
                    continue
                sPoints.append( [ i['lon'], i['lat'] ] )
        except:
            pass
        if len(sPoints) > 1:
            myWays.append(LineString(sPoints))
#    print len(myWays)
    lines = []
    rings = []
    polygons = []
    while len(myWays) > 0:
        i = myWays[0]
        if i.is_ring and len(i.coords) > 2:
            rings.append(i)
        else:
            lines.append(i)
        myWays.remove(i)
#    myWays = []
    for l in lines:
        if isinstance(l, MultiLineString):
            myWays.extend(l)
        else:
            myWays.append(l)
#    print len(myWays)
    try:
        mergedLine = linemerge(myWays)
    except:
        mergedLine = myWays[0]
    if mergedLine.is_ring:
        rings.append(mergedLine)
    else:
        lines.append(mergedLine)
    for r in rings:
        polygons.append(Polygon(r).buffer(meter2deg(1.0)))
    for i in myWays:
        polygons.append( cascaded_union(i).buffer(meter2deg(1.0)) )
    logger.debug("Start creating MultiPolygon of chunks")
    shape = cascaded_union(polygons).buffer(meter2deg(1.0))
    try:
        polygons.append(MultiPolygon(shape.interiors.buffer(meter2deg(1.0))))
    except:
        pass
    try:
        polygons.append(MultiPolygon(shape.exterior.buffer(meter2deg(1.0))))
    except:
        pass
    shape = cascaded_union(polygons).buffer(meter2deg(1.0))
    try:
        shape = MultiPolygon(shape.exterior).buffer(meter2deg(1.0))
    except:
        logger.error("Failed to create MultiPolygon from extreriors of shape")
#    print myWays
#    print shape.area, shape.geom_type, shape.is_valid
#    print shape
    logger.debug("Completed creating {0} of collected chunks", str(shape.geom_type))
    mk_kml(shape, id, name, al)
    return shape

def test_objects(id, al=3, name=u"Default"):
    logger.debug("Preparing to test the results for %s", id)
    myID = id + 3600000000
#    if len(get_data('is_in;relation({4})({0},{1},{2},{3});out ids'.format(track.bounds[1],track.bounds[0],track.bounds[3],track.bounds[2],myID))['elements']) > 0:
#    if len(get_data('rel(area:{4});is_in;node({0},{1},{2},{3});out ids'.format(track.bounds[1],track.bounds[0],track.bounds[3],track.bounds[2],myID))['elements']) > 0:
    result = False
    while result == False:
        result = get_data('rel(area:{4}) ->.a;.a is_in;node({0},{1},{2},{3});out ids qt 1;'.format(track.bounds[1],track.bounds[0],track.bounds[3],track.bounds[2],myID))
                          
    if len(result['elements']) > 0:
        testOB = build_object(id,al,name)
        if track.within(testOB) or track.intersects(testOB):
            logger.debug("We have a positive result in {0}".format(id))
            result = get_data('relation({0});out tags;'.format(myID))
#            logger.debug("I should probably check for town names here")
            return True
    logger.debug("Rejecting {0}!!!".format(id))
    return False

def get_data(searchString):
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
        sys.exit(0)
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
    bbox.append( [35.0, -35.0, 84.0, 26.0, "West Europe" ] ) # West Europe
    bbox.append( [-56.0, -28.0, 38.0, 64.0, "Africa" ] ) # Africa
    bbox.append( [25.0, -180.0, 84.0, -18.0, "North America" ] ) # North America
    bbox.append( [3.0, -123.0, 33.0, -56.0, "Central America" ] ) # Central America
    bbox.append( [-57.0, -95.0, 13.0, -24.0, "South America" ] ) # South America
    bbox.append( [-56.0, 90.0, -13.0, 180.0, "Australia" ] ) # Australia
    bbox.append( [-56.0, -180.0, 25.0, -95.0, "Pacific" ] ) # Pacific
    bbox.append( [-90.0, -180.0, -56.0, 180.0, "Antartica" ] ) # Antartica
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
#    logger.info("Testing GPX in %s (%s)", name, cID)

    if isinstance(name, int):
        logger.debug("Doesn't seem like {0} has a name!".format(name))
#    elif name == "Argentina":
#        # 6, 7
#        if test_objects(cID, 2):
#            result = get_data_relation(cID, 6)
#            for state in json.loads(json.dumps(result))['elements']:
#                sID = state['id']
#                if test_objects(sID, 6):
#                    result = get_data_relation(sID, 7)
#                    for town in json.loads(json.dumps(result))['elements']:
#                        tID = town['id']
#                        test_objects(tID, 7)
    elif name == "Brazil":
        # 4 state, 8 municipality
        if test_objects(cID, 2, name):
            get_tags(country)
            result = get_data_relation(cID, 4)
            for state in json.loads(json.dumps(result))['elements']:
                sID = state['id']
                if sID not in done:
                    done.add(sID)
                else:
                    continue
                if test_objects(sID, 4, state['tags']['name']):
                    get_tags(state)
                    result = get_data_relation(sID, 8)
                    for municipality in json.loads(json.dumps(result))['elements']:
                        mID = municipality['id']
                        if mID not in done:
                            done.add(mID)
                        else:
                            continue
                        if test_objects(mID, 8, municipality['tags']['name']):
                            get_tags(municipality)
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
