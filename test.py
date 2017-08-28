#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import sys

from shapely.geometry import MultiPolygon

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


relation_id = 0
level = 2
inner_level = 8
name = u'Kiribati'
fname = str(name).replace(" ", "_").lower()
country_code = 'KI'

if True:
    tmp = gpx_loader.get_data(
        '[out:json];'
        'area' +
        '["name:en"="' + str(name) + '"]' +
        '["boundary"="administrative"]' +
        '["admin_level"="2"];' +
        'convert rel_info' +
        '  ::id = id() - 3600000000,' +
        '  "name" = t["name"],' +
        '  "name:en" = t["name:en"],' +
        '  "admin_level" = t["admin_level"];' +
        'out;')

    print json.dumps(tmp, sort_keys=True, indent=2)

    relation_id  = tmp['elements'][0]['id']
    name         = tmp['elements'][0]['tags']['name:en']
    fname = str(name).replace(" ", "_").lower()

    with open('out_%s.json' % fname, 'w') as f:
        f.write(json.dumps(tmp, sort_keys=True, indent=2))
        f.write('\n')
        f.flush()

area_id = relation_id + 3600000000


if True:
    tmp = gpx_loader.get_relations_in_object(relation_id, inner_level)
    #tmp = gpx_loader.get_from_overpass(
    #    '[out:json][timeout:900];' +
    #    'relation' +
    #    ('["admin_level"="%s"]' % inner_level) +
    #    ('["is_in:country_code"="%s"]' % country_code) +
    #    '["type"="boundary"]' +
    #    '["boundary"="administrative"];' +
    #    'out tags;', False, True)

    with open('rels_%s.json' % fname, 'w') as f:
        f.write(json.dumps(tmp, sort_keys=True, indent=2))
        f.write('\n')
        f.flush()
    # data = gpx_loader.get_relations_in_object(relation_id, 3)
    # print '--------------------------------------------------------------------'
    # print
    # print repr(data)
    # print
    # data = gpx_loader.get_relations_in_object(relation_id, 4)
    # print '--------------------------------------------------------------------'
    # print
    # print repr(data)
    # print


# Test new geometry building!
if False:
    data = None

    data =  gpx_loader.get_geometry_for_relation(relation_id)
    with open('geom_%s.json' % name, 'w') as f:
        f.write(json.dumps(data, sort_keys=True, indent=2))
        f.write('\n')
        f.flush()

    #with open('geom_%s_%s.json' % (fname, relation_id), 'r') as f:
    #    data = json.loads(f.read())

    obj = gpx_data.geojson_to_geometry(data)
    if isinstance(obj, MultiPolygon):
        for i in range(0, len(obj)):
            gpx_store.store_kml(obj[i], relation_id, level, fname + "_" + str(i))
    else:
        gpx_store.store_kml(obj, relation_id, level, fname)

# tmp = gpx_loader.get_data(
#    'relation' +
#    '["type"="boundary"]' +
#    '["boundary"="administrative"]' +
#    '["admin_level"="2"]' +
#    '(-52.204992,-69.392213,63.434391,10.501664);' +
#    'out tags;')

if False:
    tmp = gpx_loader.get_relations_in_object(relation_id, level)
    with open('rel_%s.json' % fname, 'w') as f:
        f.write(json.dumps(tmp, sort_keys=True, indent=2))
        f.write('\n')
        f.flush()

# print repr(tmp)
