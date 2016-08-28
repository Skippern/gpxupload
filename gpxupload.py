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
#overpassServer = "http://overpass-api.de/api/interpreter" # Default
#overpassServer = "http://overpass.osm.rambler.ru/cgi/interpreter"
#overpassServer = "http://api.openstreetmap.fr/oapi/interpreter"
overpassServer = "http://overpass.osm.ch/api/interpreter"

dummyResult = {u'elements': [ { u'type': u'relation', u'id': 59470, u'tags': { u'admin_level': '2', u'name': u'Brasil' } }, { u'type': u'relation', u'id': 1059668, u'tags': { u'admin_level': '2', u'name': u'Norge' } }, { u'type': u'relation', u'id': 2978650, u'tags': { u'admin_level': '2', u'name': u'Norway' } }, { u'type': u'relation', u'id': 295480, u'tags': { u'admin_level': '2', u'name': u'Portugal' } } ], u'version': 0.6, u'osm3s': {u'timestamp_osm_base': u'29554', u'timestamp_areas_base': u'29532', u'copyright': u'The data included in this document is from www.openstreetmap.org. The data is made available under ODbL.'}, u'generator': u'Overpass API'}

#if speedups.available:
if False:
    speedups.enable()
    logger.info("Speedups enabled\n")
else:
    logger.debug("Speedups not enabled, executing default\n")

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
    searchString = 'is_in;relation["type"="boundary"]["boundary"="administrative"]["admin_level"=8]({0},{1},{2},{3});out tags;'.format(minlat,minlon,maxlat,maxlon)
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
    except TypeError:
        logger.error("json.TypeError in get_countries")
        sys.exit(1)
        return False
    except ValueError:
        logger.error("No Valid JSON Loaded (json.ValueError in get_countries): %s", result)
        sys.exit(1)
        return False
#    result = dummyResult
    try:
        myElements = json.loads(json.dumps(result))['elements']
    except:
        logger.error("json in get_countries does not contain ['elements']: %s", result)
        sys.exit(1)
    if len(myElements) < 1:
        logger.error("json in get_countries contains empty ['elements']! %s", result)
        sys.exit(1)
    logger.debug("get_countries passed all tests")
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
    print payload
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
    result = get_countries(lats[0], lons[0], lats[len(lats) - 1], lons[len(lons) - 1])
    if result == False:
        time.sleep(30)

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
myDescription = u"Track containing {0} trackpoints with a length of {2} km - bbox.{1}".format(trackptLength, track.bounds, trackLength)
logger.info(myTags)
upload_gpx(file, myTags, myDescription )
logger.debug("Completed execution of %s\n\n\n", file)
