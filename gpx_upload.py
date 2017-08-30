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

##################
# TODO: argparser
##################
log_file = '%s/GPXUploadEventLog.log' % gpx_store.cache_dir
input_file = ""

if len(sys.argv) < 2:
    print "Usage: gpxtest.py <GPX file>"
    sys.exit(0)
else:
    input_file = sys.argv[1]


gpx_store.init_cache()


logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format="%(asctime)s %(name)s %(levelname)s - %(message)s", datefmt="%Y/%m/%d %H:%M:%S:")
__LOG = logging.getLogger("gpxupload")
__LOG.info("\n\n\nSTARTING: %s\n\n" % input_file)

if speedups.available:
    speedups.enable()
    __LOG.info("Speedups enabled\n")
else:
    __LOG.debug("Speedups not enabled, executing default\n")

tags = []

tracks = gpx_store.load_gpx(input_file)
track_pt_length = 0
trackLength = 0.0

for track in tracks:
    track_pt_length = track_pt_length + len(track)

    if track.geom_type == "Point":
        pass
    elif len(track) > 1:
        trackLength = trackLength + (int(gpx_utils.deg2meter(LineString(track).length)) / 1000.0)

__LOG.info("GPX file contains %s tracks, with %s points over %s km" % (len(tracks), track_pt_length, trackLength))

for track in tracks:
    countries = gpx_loader.get_relations_in_bbox(*gpx_utils.bbox_for_track(track).tuple())

    if len(countries) == 0:
        if isinstance(track, Point):
            countries = gpx_loader.get_relations_around_point(track.y, track.x)
        elif isinstance(track, MultiPoint):
            countries = gpx_loader.get_relations_around_point(track[0].y, track[0].x)
        else:
            assert False, 'Invalid track: %s' % repr(track)

    if len(countries) == 0:
        __LOG.error("No countries found!")
        # This should NEVER happen...
        continue

    print json.dumps(countries, sort_keys=True, indent=2)

    for country in countries:
        c_ok, c_tags = gpx_rules.test_country(track, country['id'], gpx_utils.get_name(country))
        if c_ok:
            __LOG.info("Track intersects with " + gpx_utils.get_name(country))
            tags.extend(c_tags)

    tags.sort()
    tags = gpx_utils.remove_duplicates(tags)
    print json.dumps(tags, sort_keys=True, indent=2)


if True:
    sys.exit(0)


my_tags = ", ".join(tags)
my_description = u"Track file containing {0} segments with a {1} points".format(
    len(tracks), track_pt_length)

__LOG.info("TAGS: " + my_tags)

gpx_uploader.upload_gpx(input_file, my_tags, my_description)

__LOG.debug("Completed execution of %s\n\n\n", input_file)
