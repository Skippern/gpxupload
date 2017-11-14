#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os

import chardet
import yaml

__LOG = logging.getLogger('gpx_config')

def store_config(obj):
    config_file = '%s/.gpx_upload.yaml' % os.environ['HOME']
    try:
        with open(config_file, 'w') as f:
            f.write(yaml.dump(obj, Dumper=yaml.Dumper))
    except IOError:
        pass

def load_config():
    obj = {
        'cache_dir': '%s/.cache/gpx' % os.environ['HOME'],
        'enable_upload': True,
        'overpass_server': 'http://overpass-api.de/api/interpreter',
        'languages': { 'en', },
        'track_visibility': 'public'
    }
    config_file = '%s/.gpx_upload.yaml' % os.environ['HOME']
    try:
        with open(config_file, 'r') as f:
            loaded = yaml.load(f, Loader=yaml.Loader)
            for key in loaded.keys():
                obj[key] = loaded[key]
    except IOError:
        try:
            with open(config_file, 'w') as f:
                f.write(yaml.dump(obj, Dumper=yaml.Dumper))
        except IOError:
            pass
    return obj
