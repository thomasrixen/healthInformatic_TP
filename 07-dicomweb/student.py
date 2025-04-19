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

    data = flask.request.get_json()

    # Check required fields
    if not data:
        return flask.Response('Bad Request\n', 400)
    # Check if any of the required fields are missing
    if 'patient-id' not in data or 'patient-name' not in data or 'study-description' not in data:
        return flask.Response('Bad Request\n', 400)


    # Build criteria for QIDO-RS
    criteria = {}
    if data['patient-id']:
        criteria['PatientID'] = data['patient-id']
    if data['patient-name']:
        criteria['PatientName'] = data['patient-name']
    if data['study-description']:
        criteria['StudyDescription'] = data['study-description']

    # Connect to Orthanc demo server
    client = DICOMwebClient.DICOMwebClient(
        url='https://orthanc.uclouvain.be/demo/dicom-web/'
    )

    # Perform query
    studies = client.lookupStudies(criteria, onlyIdentifiers=False)

    results = []
    for study in studies:
        patient_id = study.get('00100020', {}).get('Value', [''])[0]
        patient_name = study.get('00100010', {}).get('Value', [{}])[0].get('Alphabetic', '')
        study_description = study.get('00081030', {}).get('Value', [''])[0]
        study_uid = study.get('0020000D', {}).get('Value', [''])[0]

        results.append({
            'patient-id': patient_id,
            'patient-name': patient_name,
            'study-description': study_description,
            'study-instance-uid': study_uid,
        })

    return flask.jsonify(results)
        

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
    
    
    data = flask.request.get_json()

    # 400 if missing or empty
    if 'study-instance-uid' not in data or not data['study-instance-uid'].strip():
        return flask.Response('Missing or empty study-instance-uid\n', 400)

    study_uid = data['study-instance-uid']

    client = DICOMwebClient.DICOMwebClient(
        url='https://orthanc.uclouvain.be/demo/dicom-web/'
    )

    # Send query
    series_list = client.lookupSeries({ 'StudyInstanceUID': study_uid }, onlyIdentifiers=False)

    # 404 if nothing found
    if not series_list:
        return flask.Response('No matching series\n', 404)

    results = []
    for series in series_list:
        results.append({
            'modality': series.get('00080060', {}).get('Value', [''])[0],
            'series-description': series.get('0008103E', {}).get('Value', [''])[0],
            'series-instance-uid': series.get('0020000E', {}).get('Value', [''])[0],
        })

    return flask.jsonify(results)


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
    
    data = flask.request.get_json()

    # Check presence and non-empty values
    if ('study-instance-uid' not in data or not data['study-instance-uid'].strip() or
        'series-instance-uid' not in data or not data['series-instance-uid'].strip()):
        return flask.Response('Missing or empty study/series instance UID\n', 400)

    study_uid = data['study-instance-uid']
    series_uid = data['series-instance-uid']

    client = DICOMwebClient.DICOMwebClient(
        url='https://orthanc.uclouvain.be/demo/dicom-web/'
    )

    # Lookup all instances in that series
    instances = client.lookupInstances({
        'StudyInstanceUID': study_uid,
        'SeriesInstanceUID': series_uid
    }, onlyIdentifiers=False)

    if not instances:
        return flask.Response('No matching instances\n', 404)

    # Extract UID + instance number (default = 1)
    def get_instance_info(instance):
        sop_uid = instance.get('00080018', {}).get('Value', [''])[0]
        instance_number = instance.get('00200013', {}).get('Value', [1])[0]
        return (int(instance_number) if isinstance(instance_number, int) else 1, sop_uid)

    sorted_instances = sorted([get_instance_info(i) for i in instances])
    sop_uids = [sop_uid for _, sop_uid in sorted_instances]

    return flask.jsonify(sop_uids)


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
    
    data = flask.request.get_json()

    # Step 1: Validate input
    if ('study-instance-uid' not in data or not data['study-instance-uid'].strip() or
        'series-instance-uid' not in data or not data['series-instance-uid'].strip() or
        'sop-instance-uid' not in data or not data['sop-instance-uid'].strip()):
        return flask.Response('Missing or empty UID field\n', 400)

    study_uid = data['study-instance-uid']
    series_uid = data['series-instance-uid']
    sop_uid = data['sop-instance-uid']

    client = DICOMwebClient.DICOMwebClient(
        url='https://orthanc.uclouvain.be/demo/dicom-web/'
    )

    # Step 2: Try to get the rendered PNG
    try:
        png_data = client.getRenderedInstance(
            study_uid, series_uid, sop_uid, decode=False
        )
    except:
        return flask.Response('Instance not found\n', 404)

    # Step 3: Return the PNG image
    return flask.Response(png_data, mimetype='image/png')
    


if __name__ == '__main__':
    app.run(debug = True)
