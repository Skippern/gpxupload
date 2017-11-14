#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os

import chardet
import yaml
import gpx_utils

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
        'languages': [ 'en', ],
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

def modify_config(args):
    config = load_config()
    if args.input_file == 'default':
        new_config = config.copy()
        new_config.pop(args.set, None)
        store_config(new_config)
        exit(0)
    if args.set == 'add_language':
        config['languages'].append(args.input_file)
        config['languages'] = gpx_utils.remove_duplicates(config['languages'])
    elif args.set == 'remove_language':
        if args.input_file == 'en':
            print 'You cannot remove English'
            exit(0)
        config['languages'].remove(args.input_file)
    elif args.set == 'track_visibility':
        if args.input_file != 'public' and args.input_file != 'private' and args.input_file != 'trackable' and args.input_file != 'identifiable':
            print 'Invalid argument, valid arguments are public, private, trackable, or identifiable'
            exit(0)
        config[args.set] = args.input_file
    else:
        config[args.set] = args.input_file
    store_config(config)
    exit(0)
