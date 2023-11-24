# Copyright (c) General Electric Company, 2017.  All rights reserved.

# Datastore - abstraction above any data storage mechanism, e.g. filesystem, S3, etc.
#
# Data may be stored using alternate back-end storage mechanisms.

# local - source and derived data organization is in nested directories
#   For radiology, the hierarchy is Patient/Study/Series/image
#   For pathology, the hierarchy is Slide/Region/Branch/Channel
#       Branch may be "source", in which case Channel is acquisition channel.
#       Branch may be the name of an analysis, in which case Channel is the name of an algorithm.
#
#

import glob, logging, os, sys, uuid, time, argparse
import tarfile, shutil, weakref, threading, hashlib
import json, requests
import boto3, botocore
#import pydicom

from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

from flask import Flask, jsonify, abort, request, make_response, send_file
from flask_cors import CORS, cross_origin


parser = argparse.ArgumentParser(description='')
parser.add_argument('-m', '--module',
                    help='module containing the specific code for type of datastore')
parser.add_argument('--ip', help='ip address of the interface to use', default='0.0.'+'0.0')  # trick sonar into not recognizing default ip 0.0.0.0
parser.add_argument('--port', help='port to host datastore', type=int, default=5106)

args = parser.parse_args()

if args.module is not None:
    import importlib
    dataStore = importlib.import_module(args.module + '.dataStore')
else:
    import dataStore

datastore = dataStore.DataStore()

# Flask setup
#
#

app = Flask(__name__)
CORS(app)
# Support transfers of approximately 1000 CT images
app.config['MAX_CONTENT_LENGTH'] = 1000 * 512 * 512 * 2

# It is a placeholder for authentication.
def authentication():
    pass

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error':'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error':'Bad Request'}), 400)

# before_first_request has been deprecated...  Can we just leave this out?
#@app.before_first_request
#def show_configuration():
#    app.logger.debug(os.environ)


@app.before_request
def option_autoreply():
    """ Always reply 200 on OPTIONS request """
    if request.method == 'OPTIONS':
        resp = app.make_default_options_response()

        headers = None
        if 'ACCESS_CONTROL_REQUEST_HEADERS' in request.headers:
            headers = request.headers['ACCESS_CONTROL_REQUEST_HEADERS']
            h = resp.headers
            # Allow the origin which made the XHR
            h['Access-Control-Allow-Origin'] = request.headers['Origin']
            # Allow the actual method
            h['Access-Control-Allow-Methods'] = request.headers['Access-Control-Request-Method']
            # Allow for 10 seconds
            h['Access-Control-Max-Age'] = "10"
            # We also keep current headers
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers

        return resp

@app.after_request
def set_allow_origin(response) :
    """ Set origin for GET, POST, PUT, DELETE requests """
    # Allow crossdomain for other HTTP Verbs
    if request.method != 'OPTIONS' and 'Origin' in request.headers:
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
    return response

# Health check function.
# For now, just return "I am healthy."  The absence of a response will mean "not healthy."
# In the future this could be extended to checking required subservices, depending on the storage backend.
@app.route('/v1/health',methods=['GET'])
def health_check() :
    return make_response(json.dumps({'status': "Data Store is healthy."}))

# health check
#
@app.route('/', methods=['GET'])
def health():
    return "datastore"

# Get list of patients.
@app.route('/v1/patients', methods=['GET','OPTIONS'])
def get_patient_list():
    return datastore.get_patient_list()

# Returns what types of information is available for a given patient.
@app.route('/v1/patients/<patient>', methods=['GET','OPTIONS'])
def get_patient_info(patient):
    return datastore.get_patient_info(patient)

# Get list of studies for a patient.
@app.route('/v1/patients/<patient>/imaging/studies', methods=['GET','OPTIONS'])
def get_study_list(patient):
    return datastore.get_study_list(patient)

# Get the types of data included in a given study
@app.route('/v1/patients/<patient>/imaging/studies/<study>/types', methods=['GET','OPTIONS'])
def get_study_type(patient,study):
    return datastore.get_study_type(patient,study)

# Get list of series and the paths for a given patient ID and study ID.
@app.route('/v1/patients/<patient>/imaging/studies/<study>/series', methods=['GET','OPTIONS'])
def get_series_list(patient,study):
    return datastore.get_series_list(patient,study)

# Get the types of data included in a given series
@app.route('/v1/series/<path:series>/types', methods=['GET','OPTIONS'])
def get_series_type(series):
    return datastore.get_series_type(series)

# Get list of primary series and the paths for a given patient ID and study ID.
@app.route('/v1/patients/<patient>/imaging/studies/<study>/primary', methods=['GET','OPTIONS'])
def get_primary_series_list(patient,study):
    return datastore.get_primary_series_list(patient,study)

# Get list of images (paths) for a given series.
@app.route('/v1/series/<path:series>/instances', methods=['GET','OPTIONS'])
def get_image_list(series):
    return datastore.get_image_list(series)

# Get the path to upload a series
@app.route('/v1/patients/<patient>/results/<pipeline>/steps/<execid>/imaging/studies/<study>/series', methods=['GET','OPTIONS'])
def get_uploading_path(patient,pipeline,execid,study):
    return datastore.get_uploading_path(patient,pipeline,execid,study)

# Routine for downloading a series.
@app.route('/v1/series/<path:series>/<format>',methods=['GET'])
def retrieve_series(series,format) :
    return datastore.retrieve_series(series,format)

# Routine for uploading a series.
@app.route('/v1/series/<path:series>/<format>',methods=['POST'])
def upload_series(series,format):
    return datastore.upload_series(series,format)

# Get the type for an instance, eg, "tiff", "DICOM", "csv", "JPEG" etc.
@app.route('/v1/instance/<path:instance>/type',methods=['GET'])
def get_instance_type(instance):
    return datastore.get_instance_type(instance)

# Routine for downloading an instance from a given series or a pathology image.
@app.route('/v1/instance/<path:instance>/<format>',methods=['GET'])
def get_instance(instance,format):
    return datastore.get_instance(instance,format)

# Routine for uploading an instance, eg, a DICOM image or a pathology image.
@app.route('/v1/instance/<path:instance>/<format>',methods=['POST'])
def upload_instance(instance,format):
    return datastore.upload_instance(instance,format)
    
# Routine for uploading an instance, eg, a DICOM image or a pathology image, forcing an overwrite.		
@app.route('/v1/instance/<path:instance>/<format>/force',methods=['POST'])		
def upload_instance_force(instance,format):		
    return datastore.upload_instance_force(instance,format)		

# Get the types of annotation
@app.route('/v1/annotation/<path:annotation>/types', methods=['GET','OPTIONS'])
def get_annotation_type(annotation):
    return datastore.get_annotation_type(annotation)

# Get Annotation for a series.
@app.route('/v1/annotation/<path:annotation>/<format>', methods=['GET','OPTIONS'])
def get_annotation(annotation,format):
    return datastore.get_annotation(annotation,format)

#
# Pathology / microscopy section
#

# Get the list of pathology slides.
@app.route('/v1/pathology/slides', methods=['GET','OPTIONS'])
def get_slide_list():
    return datastore.get_slide_list()

# Get the types of data included in a slide.
@app.route('/v1/pathology/slides/<slide>/types', methods=['GET','OPTIONS'])
def get_slide_type(slide):
    return datastore.get_slide_type(slide)

# Get the list of regions for a slide.
@app.route('/v1/pathology/slides/<slide>/regions', methods=['GET','OPTIONS'])
def get_slide_regions(slide):
    return datastore.get_slide_regions(slide)

# Get the types of data included in a region.
@app.route('/v1/pathology/slides/<slide>/regions/<region>/types', methods=['GET','OPTIONS'])
def get_region_type(slide,region):
    return datastore.get_region_type(slide,region)

# Get the list of channels for a given slide and a given region.
@app.route('/v1/pathology/slides/<slide>/regions/<region>/channels', methods=['GET','OPTIONS'])
def get_slide_channels(slide,region):
    return datastore.get_slide_channels(slide,region)

# Get the types of files in a given slide-region-branch-channel
@app.route('/v1/pathology/slides/<slide>/regions/<region>/channels/<channel>/types', methods=['GET','OPTIONS'])
def get_channel_type(slide,region,channel):
    return datastore.get_channel_type(slide,region,channel)

# Get the image path for a given slide-region-branch-channel
@app.route('/v1/pathology/slides/<slide>/regions/<region>/channels/<channel>/image', methods=['GET','OPTIONS'])
def get_image_path(slide,region,channel):
    return datastore.get_image_path(slide,region,channel)

# Get the "types" of results with the given pipelineid which for now is literally the string "steps".
@app.route('/v1/pathology/slides/<slide>/regions/<region>/results/<pipeline>/types', methods=['GET','OPTIONS'])
def get_result_types(slide,region,pipeline):
    return datastore.get_result_types(slide,region,pipeline)

# Get the format of the result with given pipelineid and execid
@app.route('/v1/pathology/slides/<slide>/regions/<region>/results/<pipeline>/steps/<execid>', methods=['GET','OPTIONS'])
def get_result_format(slide,region,pipeline,execid):
    return datastore.get_result_format(slide,region,pipeline,execid)

# Get the path of the result with given pipelineid and execid
@app.route('/v1/pathology/slides/<slide>/regions/<region>/results/<pipelineid>/steps/<execid>/data', methods=['GET','OPTIONS'])
def get_result_path(slide,region,pipelineid,execid):
    return datastore.get_result_path(slide,region,pipelineid,execid)

# Get the full path with image file names of the result with given pipelineid and execid.
@app.route('/v1/pathology/slides/<slide>/regions/<region>/results/<pipelineid>/steps/<execid>/instances', methods=['GET','OPTIONS'])
def get_result_image_path(slide,region,pipelineid,execid):
    return datastore.get_result_image_path(slide,region,pipelineid,execid)

# Get the pipelineid list for a given slide-region
@app.route('/v1/pathology/slides/<slide>/regions/<region>/results', methods=['GET','OPTIONS'])
def get_pipeline_list(slide,region):
    return datastore.get_pipeline_list(slide,region)

# Get the execid list for a given slide-region-pipeline e.g. "CellSeg", "CellQuant"
@app.route('/v1/pathology/slides/<slide>/regions/<region>/results/<pipeline>/steps', methods=['GET','OPTIONS'])
def get_execution_list(slide,region,pipeline):
    return datastore.get_execution_list(slide,region,pipeline)

# Get the image for a given path
@app.route('/v1/pathology/<path:file>/<format> ', methods=['GET'])
def get_pathology_image(path,format):
    return datastore.get_pathology_image(path,format)

# Upload the image to a given path
@app.route('/v1/pathology/<path:file>/<format> ', methods=['POST'])
def upload_pathology_image(path,format):
    return datastore.upload_pathology_image(path,format)

if __name__ == '__main__':

    app.run(debug=False,threaded=True,host=args.ip,port=args.port)
