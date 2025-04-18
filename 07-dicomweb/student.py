#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# In this exercise, your goal is to implement a simple Web viewer that
# displays DICOM images. Your Web application will query the content
# of a DICOMweb server (using the QIDO-RS API) and will retrieve the
# individual DICOM slices rendered as PNG images (using WADO-RS).
#
# You will use the Orthanc demo server accessible at:
# https://orthanc.uclouvain.be/demo/
#
# The root of the DICOMweb API of this demo server is located at:
# https://orthanc.uclouvain.be/demo/dicom-web/
#
# The user-friendly version of the documentation of the DICOMweb API
# is available at:
# https://www.dicomstandard.org/using/dicomweb


import DICOMwebClient
import flask
import json

app = flask.Flask(__name__)

@app.route('/')
def redirection():
    return flask.redirect('index.html', code = 302)

@app.route('/index.html')
def get_index():
    with open('index.html', 'r') as f:
        return flask.Response(f.read(), mimetype = 'text/html')

@app.route('/app.js')
def get_javascript():
    with open('app.js', 'r') as f:
        return flask.Response(f.read(), mimetype = 'text/javascript')


@app.route('/lookup-studies', methods = [ 'POST' ])
def lookup_studies():
    # This route retrieves the list of the DICOM studies corresponding
    # to a specific patient ID, patient name, and/or study description
    # (using a QIDO-RS request).
    #
    # Inputs: The body of the HTTP request is a JSON object containing
    # 3 fields: "patient-id" is the patient's identifier in the
    # hospital, "patient-name" is the name of the patient, and
    # "study-description" is the description of the study.
    # 
    # These fields are empty if no filtering is requested by the user,
    # which is allowed by the QIDO-RS specification. If all of these
    # fields are empty, the route shall retrieve all the studies
    # present in the Orthanc demo server to which we are connected.
    #
    # The 400 "Bad Request" code must be returned if some mandatory
    # input field is missing.
    #
    # Outputs: The body of the HTTP response must be a JSON array
    # containing the 4 following fields for each matching DICOM study:
    # "patient-id" is the hospital identifier of the matching patient,
    # "patient-name" is the name of the matching patient,
    # "study-description" is the description of the matching study,
    # and "study-instance-uid" is the DICOM identifier of the matching
    # study.

    # TODO
    return flask.Response('Not Implemented\n', 501)
        

@app.route('/lookup-series', methods = [ 'POST' ])
def lookup_series():
    # This route retrieves the list of the DICOM series associated
    # with a given DICOM study (using a QIDO-RS request).
    #
    # Inputs: The body of the HTTP request is a JSON object containing
    # 1 field: "study-instance-uid" is the DICOM identifier of the
    # study of interest.
    #
    # The 400 "Bad Request" code must be returned if the
    # "study-instance-uid" field is missing or empty. The 404 "Not
    # Found" code must be returned if "study-instance-uid" matches no
    # DICOM study in the DICOMweb server.
    #
    # Outputs: The body of the HTTP response must be a JSON array
    # containing the following 3 fields for each matching series:
    # "modality" is the type of medical imaging device that was used
    # to acquire this specific series ("CT", "MR",...),
    # "series-description" is the description of the matching series,
    # and "series-instance-uid" is the DICOM identifier of the
    # matching series.
    
    # TODO
    return flask.Response('Not Implemented\n', 501)


@app.route('/lookup-instances', methods = [ 'POST' ])
def lookup_instances():
    # This route retrieves the list of all the DICOM instances (i.e.,
    # DICOM files) corresponding to a specific study and series (using
    # a QIDO-RS request).
    #
    # Inputs: The body of the HTTP request is a JSON object containing
    # 2 fields: "study-instance-uid" is the DICOM identifier of the
    # study of interest, and "series-instance-uid" is the DICOM
    # identifier of the series of interest.
    #
    # The 400 "Bad Request" code must be returned if one of the two
    # input fields is missing or empty. The 404 "Not Found" code must
    # be returned if no matching DICOM series can be found.
    #
    # Outputs: The body of the HTTP response must be a JSON array
    # containing the DICOM identifier (SOP Instance UID) of the
    # instances that are part of the series.
    #
    # The instances shall be sorted by increasing integer value of the
    # "InstanceNumber" (0x0020, 0x0013) DICOM tag to ensure that the
    # individual slices are displayed in the correct order by the Web
    # viewer. Pay attention to the fact that this tag can be absent,
    # in which case you can assume that it equals "1".
    
    # TODO
    return flask.Response('Not Implemented\n', 501)


@app.route('/render-instance', methods = [ 'POST' ])
def render_instance():
    # This route issues a WADO-RS request to render a DICOM instance as a PNG file.
    #
    # Inputs: The body of the HTTP request is a JSON object containing
    # 3 fields: "study-instance-uid" is the DICOM identifier of the
    # study, "series-instance-uid" is the DICOM identifier of the
    # series, and "sop-instance-uid" is the DICOM identifier of the
    # instance.
    #
    # The 400 "Bad Request" code must be returned if some mandatory
    # input field is missing or empty. The 404 "Not Found" code must
    # be returned if the instance cannot be found on the DICOMweb server.
    #
    # Outputs: The body of the HTTP response must contain a PNG file.
    
    # TODO
    return flask.Response('Not Implemented\n', 501)


if __name__ == '__main__':
    app.run(debug = True)
