#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test the GPX File for coverage, so it is tagged correctly when uploaded

import json
import logging
import sys

from shapely import speedups
from shapely.geometry import LineString, Point, MultiPoint

from gpx import gpx_loader
from gpx import gpx_rules
from gpx import gpx_store
from gpx import gpx_uploader
from gpx import gpx_utils

logging.basicConfig(filename="./kml/GPXUploadEventLog.log", level=logging.DEBUG,
                    format="%(asctime)s %(name)s %(levelname)s - %(message)s", datefmt="%Y/%m/%d %H:%M:%S:")
__LOG = logging.getLogger("gpxupload")
__LOG.info("\n\n\nSTARTING\n\n")

if speedups.available:
    speedups.enable()
    __LOG.info("Speedups enabled\n")
else:
    __LOG.debug("Speedups not enabled, executing default\n")

tags = []
input_file = ""

# TODO: argparser

if len(sys.argv) < 2:
    print "Usage: gpxtest.py <GPX file>"
    sys.exit(0)
else:
    input_file = sys.argv[1]

tracks = gpx_store.load_gpx(input_file)
track_pt_length = 0

for track in tracks:
    track_pt_length = track_pt_length + len(track)

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
    __LOG.debug("GPX File contains %s trackpoints with %s km.", str(len(track)), str(trackLength))

    countries = gpx_loader.get_relations_in_bbox(*gpx_utils.bbox_for_track(track).tuple())

    if len(countries) == 0:
        if isinstance(track, Point):
            countries = gpx_loader.get_relations_around_point(track.y, track.x)
        elif isinstance(track, MultiPoint):
            countries = gpx_loader.get_relations_around_point(track[0].y, track[0].x)
        else:
            __LOG.error("Noooo! " + type(track))
            sys.exit(123)

    if len(countries) == 0:
        __LOG.error("No countries found!")
        # This should NEVER happen...
        continue

    print json.dumps(countries, sort_keys=True, indent=2)

    for country in countries:
        c_ok, c_tags = gpx_rules.test_country(track, country['id'], gpx_utils.get_name(country))
        if c_ok:
            __LOG.info("Track intersects with " + country['name'])
            tags.extend(c_tags)

    print json.dumps(tags, sort_keys=True, indent=2)


if True:
    sys.exit(0)


tags.sort()
tags = gpx_utils.remove_duplicates(tags)
my_tags = ", ".join(tags)
my_description = u"Track file containing {0} segments with a {1} points".format(
    len(tracks), track_pt_length)

__LOG.info("TAGS: " + my_tags)

gpx_uploader.upload_gpx(input_file, my_tags, my_description)

__LOG.debug("Completed execution of %s\n\n\n", input_file)
