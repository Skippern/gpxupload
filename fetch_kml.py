#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test the GPX File for coverage, so it is tagged correctly when uploaded

import argparse
import logging

from gpx import gpx_data
from gpx import gpx_store

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='Load and create a KML file')
parser.add_argument('--cache_dir', metavar='DIR', type=str,
                    help='Location of cache', default=gpx_store.cache_dir)
parser.add_argument('obj_id', type=int, help='relation ID of object')
parser.add_argument('obj_level', type=int, help='Level of object')

args = parser.parse_args()


if 'cache_dir' in args:
    gpx_store.cache_dir = args.cache_dir
gpx_store.init_cache()


tags = gpx_data.load_tags(args.obj_id, args.obj_level)

name = str(args.obj_id)
if 'name:en' in tags:
    name = tags['name:en']
else:
    name = tags['name']

geos = gpx_data.load_geo_shape(args.obj_id, args.obj_level, name)
gpx_store.store_kml(geos, args.obj_id, args.obj_level, name)
