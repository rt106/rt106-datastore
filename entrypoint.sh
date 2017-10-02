#!/bin/sh

( cd /rt106; python /rt106/dataServer.py)

# If using a local file system datastore, a simple HTTP server can be
# configured for debugging to serve the source and derived images.
# Environment variables need to be set to the locations of the local stores.
#
#( cd $DATASTORE_LOCAL_SOURCE_PATH; python -m SimpleHTTPServer 8000) &
#( cd $DATASTORE_LOCAL_DERIVED_PATH; python -m SimpleHTTPServer 8001)
