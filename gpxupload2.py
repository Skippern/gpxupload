#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test the GPX File for coverage, so it is tagged correctly when uploaded

import logging
import sys
import xml.etree.ElementTree as etree

from shapely import speedups
from shapely.geometry import LineString, Point, MultiPoint, Polygon

from gpx import gpx_loader
from gpx import gpx_rules
from gpx import gpx_store
from gpx import gpx_uploader
from gpx import gpx_utils

logger = logging.getLogger("gpxupload")
logging.basicConfig(filename="./kml/GPXUploadEventLog.log", level=logging.DEBUG,
                    format="%(asctime)s %(name)s %(levelname)s - %(message)s", datefmt="%Y/%m/%d %H:%M:%S:")

logger.info("\n\n\nSTARTING\n\n")

if speedups.available:
    speedups.enable()
    logger.info("Speedups enabled\n")
else:
    logger.debug("Speedups not enabled, executing default\n")

delay = 60

tags = []
SQKM = ((60.0 * 1.852) * (60.0 * 1.852))
result = ""
name = u"?"
file = ""
nullShape = Point(0.0, 0.0).buffer(0.0000001)


__ENABLE_KML = True
__ENABLE_WKB = True


def mk_kml(ob, id, name, subdir="0"):
    """
    :param ob:
    :param id:
    :param name:
    :param subdir:
    :return:
    """
    if __ENABLE_KML:
        gpx_store.store_kml(ob, id, int(subdir), name)
    if __ENABLE_WKB:
        gpx_store.store_wkb(ob, id, int(subdir))


# print tags

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

track, bbox = gpx_store.load_gpx(file)


if track.geom_type == "Point":
    trackLength = 0.0
elif len(track) > 1:
    trackLength = int(gpx_utils.deg2meter(LineString(track).length)) / 1000.0
else:
    trackLength = 0.0
if trackLength < 1.0:
    tags.append(u"Short Trace")
elif trackLength > 100.0:
    tags.append(u"Long Trace")
logger.debug("GPX File contains %s trackpoints with %s km.", str(len(track)), str(trackLength))

result = gpx_loader.get_relations_in_bbox(bbox[0], bbox[1], bbox[2], bbox[3], 2)

# print result

myElements = result['elements']
# print myElements
if len(myElements) == 0:
    logger.debug("No countries found in first run, testing per continent")
    global_region = []
    #    global_region.append( [min.lat, min.lon, max.lat, max.lon, "Identifier" ] )
    global_region.append([35.0, 135.0, 84.0, 180.0, "East Asia/NE"])
    global_region.append([-14.0, 135.0, 35.0, 180.0, "East Asia/SE"])
    global_region.append([10.0, 113.0, 35.0, 135.0, "East Asia/SW/1"])
    global_region.append([10.0, 91.0, 35.0, 113.0, "East Asia/SW/2"])
    global_region.append([-14.0, 91.0, 10.0, 113.0, "East Asia/SW/3"])
    global_region.append([-14.0, 113.0, 10.0, 135.0, "East Asia/SW/4"])
    global_region.append([35.0, 91.0, 84.0, 135.0, "East Asia/NW"])
    global_region.append([10.0, 32.0, 40.0, 65.0, "Arabia"])
    global_region.append([-11.0, 53.0, 84.0, 91.0, "Central Asia"])
    global_region.append([32.0, 26.0, 84.0, 53.0, "East Europe"])
    global_region.append([35.0, -35.0, 84.0, 0.0, "West Europe (West)"])
    global_region.append([47.0, 13.0, 59.0, 26.0, "West Europe (South/1)"])
    global_region.append([35.0, 13.0, 47.0, 26.0, "West Europe (South/2)"])
    global_region.append([35.0, 0.0, 47.0, 13.0, "West Europe (South/3)"])
    global_region.append([47.0, 0.0, 59.0, 13.0, "West Europe (South/4)"])
    global_region.append([59.0, 0.0, 84.0, 26.0, "West Europe (North)"])
    global_region.append([28.0, -28.0, 38.0, 64.0, "Mediterania"])
    global_region.append([-56.0, -28.0, 28.0, 64.0, "Africa"])
    global_region.append([25.0, -180.0, 84.0, -126.0, "North America (West)"])
    global_region.append([25.0, -126.0, 84.0, -72.0, "North America (Central)"])
    global_region.append([25.0, -72.0, 84.0, -18.0, "North America (East)"])
    global_region.append([3.0, -123.0, 33.0, -56.0, "Central America"])
    global_region.append([0.0, -95.0, 13.0, -24.0, "South America (North)"])
    global_region.append([-34.0, -59.0, 0.0, -24.0, "South America (East)"])
    global_region.append([-34.0, -95.0, 0.0, -59.0, "South America (West)"])
    global_region.append([-57.0, -95.0, -34.0, -24.0, "South America (South)"])
    global_region.append([-56.0, 90.0, -13.0, 180.0, "Australia"])
    global_region.append([-56.0, -180.0, 25.0, -95.0, "Pacific"])
    global_region.append([-90.0, -180.0, -56.0, 180.0, "Antartica"])
    global_region.append([83.0, -180.0, 90.0, 180.0, "Arctic"])
    global_region.append([-90.0, -180.0, 90.0, 180.0,
                 "The World (Something is wrong further up)"])  # If this ever happens, identify the missing square, this line should never happen to avoid controlling the GPX file against any country in the world.
    for n in global_region:
        sPoints = []
        sPoints.append(([n[1], n[0]]))
        sPoints.append(([n[3], n[0]]))
        sPoints.append(([n[3], n[2]]))
        sPoints.append(([n[1], n[2]]))
        testOB = Polygon(sPoints)
        if track.within(testOB) or track.intersects(testOB):
            logger.debug("Found it in {0}!".format(n[4]))
            print "Found in {0}!".format(n[4])
            minlon, minlat, maxlon, maxlat = testOB.bounds
            result = gpx_loader.get_relations_in_bbox(minlat, minlon, maxlat, maxlon, 2)
            break

completed_ids = set()
for element in result['elements']:
    country_id = element['id']
    if country_id not in completed_ids:
        #        print "Executing {0}".format(cID)
        completed_ids.add(country_id, )
    else:
        #        print "cID {0} already done!".format(cID)
        continue
    country_name = country_id
    try:
        country_name = element['tags']['name']
    except:
        logger.debug("Country %s have no readable name", country_id)
    try:
        country_name = element['tags']['name:en']
    except:
        logger.debug("Country %s have no readable name:en", country_id)

    country_name = gpx_utils.enforce_unicode(country_name)

    logger.debug("Preparing to test %s (%s)", country_name, country_id)
    accept, country_tags = gpx_rules.test_country(track, country_id, country_name)
    if accept:
        tags.extend(country_tags)

try:
    tags.sort()
except:
    pass
tags = gpx_utils.remove_duplicates(tags)
myTags = ", ".join(tags)
bbox = [([track.bounds[1], track.bounds[0], track.bounds[3], track.bounds[2]])]
myDescription = u"Track containing {0} trackpoints with a length of {2} km - bbox.{1}".format(trackptLength, bbox,
                                                                                              trackLength)
logger.info(myTags)
gpx_uploader.upload_gpx(file, myTags, myDescription)
logger.debug("Completed execution of %s\n\n\n", file)
