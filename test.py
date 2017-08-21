#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import sys

from gpx import gpx_data
from gpx import gpx_loader
from gpx import gpx_store

# from gpx import gpx_data

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

# sør-tr: 4/406567 size: 5.32357184501

# 2017/08/18 23:02:40: gpxupload INFO - Track intersects with Sør-Trøndelag (4/406567)
# place.BBOX((7.647727443070296, 62.25535774937205, 12.255034250677872, 64.72882056249559))/
# track.BBOX((7.696714, 62.548783, 9.518007, 63.114353))


# norge : 2/2978650 size: 197.936903308

# 2017/08/18 22:55:58: gpxupload INFO - Track is within Norway (2/2978650)
# place.BBOX((-9.685102558198317, -54.65428797698121, 34.689413191018396, 81.02836397686758))/
# track.BBOX((7.696714, 62.548783, 9.518007, 63.114353))


# Kuwait (2/305099) size: 2.30355758481

# 2017/08/18 23:04:32: gpxupload INFO - Track is within Kuwait (2/305099)
# place.BBOX((46.55231473125042, 28.523993230971392, 49.00504985152776, 30.104177170338666))/
# track.BBOX((47.62998, 28.677306, 48.37961, 29.391003))

# ...... (4/4579477) size: 0.542009616223

# 2017/08/18 23:04:48: gpxupload INFO - Track intersects with الاحمدي (4/4579477)
# place.BBOX((47.54078044332839, 28.523993230971392, 48.567580853044134, 29.209065567406938))/
# track.BBOX((47.62998, 28.677306, 48.37961, 29.391003))


#relation_id = 406567
#level = 4
relation_id = 305099
level = 2

# with open("out.json") as f:
#    tmp = json.loads(f.read())
#    tmp = gpx_data.to_geometry(tmp)
#    print
#    print "----------------------------------------"
#    print
#    print "Area: %s / %s" % (tmp.area, tmp.geom_type)

# Test new geometry building!
if True:
    data = gpx_loader.get_geometry_for_relation(relation_id, level)
    # with open('geom.json', 'r') as f:
    #     data = json.loads(f.read())
    with open('geom.json', 'w') as f:
        f.write(json.dumps(data))
    obj = gpx_data.geojson_to_geometry(data)
    gpx_store.store_kml(obj, relation_id, level)

# tmp = gpx_loader.get_data(
#    'relation' +
#    '["type"="boundary"]' +
#    '["boundary"="administrative"]' +
#    '["admin_level"="2"]' +
#    '(-52.204992,-69.392213,63.434391,10.501664);' +
#    'out tags;')

if False:
    tmp = gpx_loader.get_relations_in_object(relation_id, level)
    with open('geom.json', 'w') as f:
        f.write(json.dumps(tmp))

# print repr(tmp)
