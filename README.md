# gpxupload
[![Build Status](https://travis-ci.org/Skippern/gpxupload.svg?branch=master)](https://travis-ci.org/Skippern/gpxupload)

Automated (but somewhat slow) upload of GPX files to OpenStreetMap


# Installation

Clone this repository, or download the latest release. Install depending python modules.

`pip install -r dependencies.txt`

The script runs `python 2.7` and are tested on Mac OS X and Linux Ubuntu.

# Usage

`gpx_upload.py [options] <input_file>`

`fetch_kml.py [options] <obj_id> <obj_level>`


`--dry_run` Does not upload results

`--cache_dir` Location of cache

`--log_file` Location of log file

`<input_file>` GPX file to process

`<obj_id>` and `<obj_level>` Relation Object ID and admin_level from OpenStreetMap for the object to fetch as KML file.
