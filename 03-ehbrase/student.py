#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE: During the development, make sure to run:
#
# $ docker compose up
#
# This will start an EHRbase server on your computer using Docker
# Compose. Docker Compose provides an easy way to start at the same
# time the EHRbase server together with the PostgreSQL server.
#
# Hints:
#
# - To check that EHRbase is running, you can open
#   "http://localhost:8001/ehrbase/swagger-ui/index.html" using your
#   Web browser, with username "ehrbase-user" and password
#   "SuperSecretPassword" (without the quotes). Note that this page
#   contains the documentation of the REST API of openEHR CDR.
#
# - You can reinitialize EHRbase by executing "./ResetEHRbase.py"


import OpenEHRClient
import flask
import os
import uuid

app = flask.Flask(__name__)


global_credentials = None

def get_composer_name():
    return global_credentials['openehr-composer']

@app.route('/')
def redirection():
    return flask.redirect('index.html', code = 302)

@app.route('/index.html')
def get_index():
    with open('resources/index.html', 'r') as f:
        return flask.Response(f.read(), mimetype = 'text/html')

@app.route('/app.js')
def get_javascript():
    with open('resources/app.js', 'r') as f:
        return flask.Response(f.read(), mimetype = 'text/javascript')



def app_initialize(credentials, pathToResources):
    # This function must install the two openEHR templates
    # "Basic.v0.opt" and "MonitoredPatient.v0.opt", which are located
    # in the directory specified by the "pathToResources" argument,
    # into the openEHR CDR. The credentials to the EHRbase server are
    # available in the "credentials" argument. This function can be
    # invoked multiple times, so your code must check whether the
    # template has not already been installed before proceeding with
    # the installation.
    #
    # Hints:
    # - The file "./resources/ArchetypeDesignerExport.zip" can be
    #   imported into the openEHR Archetype Designer to inspect the
    #   content of the templates.
    # - For all the exercises, have a look at the integration tests!
    #   This will help you developing the code.

    global global_credentials
    global_credentials = credentials

    ehr_client = OpenEHRClient.OpenEHRClient(credentials['url'], credentials['username'], credentials['password'])



    # Check if the templates are already installed using the listTemplates method
    templates = ehr_client.listTemplates()
    if 'Basic.v0' not in templates:
        ehr_client.addTemplate(os.path.join(pathToResources, 'Basic.v0.opt'))
    if 'MonitoredPatient.v0' not in templates:
        ehr_client.addTemplate(os.path.join(pathToResources, 'MonitoredPatient.v0.opt'))
    
    

@app.route('/create-patient', methods = [ 'POST' ])
def create_patient():
    # This route creates a new EHR in the openEHR CDR. The demographic
    # information about the patient is provided by adding a new
    # composition deriving from template "MonitoredPatient.v0" in the
    # EHR. Note that there must be one and only one
    # "MonitoredPatient.v0" composition in each EHR.
    #
    # Inputs: The body of the HTTP request must be a JSON object
    # containing one single field entitled "patient-name", which
    # specifies the name of the patient.
    #
    # The field "monitoredpatient.v0/composer|name" of the composition
    # must be filled using the result of the "get_composer_name()"
    # function. Throughout this exercise, this "composer" information
    # is needed because INGInious runs one single EHRbase server that
    # is shared by all the students.
    #
    # Outputs: The body of the HTTP response must be a JSON object
    # containing one single field entitled "ehr-id", which indicates
    # the identifier of the newly created EHR.
    #
    # Hint: You can generate a sample "simplified JSON flat"
    # composition to identify all the possible fields by typing the
    # command line after EHRbase is started using "docker compose up":
    #
    # $ curl -u ehrbase-user:SuperSecretPassword http://localhost:8001/ehrbase/rest/ecis/v1/template/MonitoredPatient.v0/example?format=FLAT
    #
    # Make sure to read the integration tests to identify the required fields.

    # Get the patient name from the request
    data = flask.request.get_json()
    patient_name = data.get('patient-name')

    if not patient_name:
        return flask.Response('Patient name is required', status=300)
    
    ehr_client = OpenEHRClient.OpenEHRClient(global_credentials['url'], global_credentials['username'], global_credentials['password'])

    ehr_id = ehr_client.createEHR()

    composition = {
        "monitoredpatient.v0/territory|code" : "BE",
        "monitoredpatient.v0/territory|terminology" : "ISO_3166-1",
        "monitoredpatient.v0/composer|name" : get_composer_name(),
        'monitoredpatient.v0/demographics_container/person/name': patient_name
    }

    composition_uid = ehr_client.addComposition(ehr_id, 'MonitoredPatient.v0', composition)

    return flask.jsonify({'ehr-id': ehr_id})



@app.route('/record-temperature', methods = [ 'POST' ])
def record_temperature():
    # This route records a new temperature by adding a new composition
    # deriving from template "Basic.v0" into an existing EHR. There can
    # be multiple "Basic.v0" compositions, each composition recording one
    # measure of the body temperature over time.
    #
    # Inputs: The body of the HTTP request must be a JSON object
    # containing three fields: "ehr-id" is the identifier of the
    # parent EHR (as obtained from "POST /create-patient"),
    # "temperature" is a floating-point number containing the body
    # temperature (expressed in Celsius), and "time" is the moment
    # were the measure was taken (encoded using the ISO 8601
    # standard).
    #
    # The field "basic/composer|name" of the composition must be
    # filled using the result of the "get_composer_name()" function.
    #
    # Outputs: The body of the HTTP response must be a JSON object
    # containing one single field entitled "composition-uid", which
    # indicates the identifier of the newly created composition.
    #
    # Hint: You can generate a sample "simplified JSON flat"
    # composition to identify all the possible fields by typing the
    # command line after EHRbase is started using "docker compose up":
    #
    # $ curl -u ehrbase-user:SuperSecretPassword http://localhost:8001/ehrbase/rest/ecis/v1/template/Basic.v0/example?format=FLAT
    #
    # Make sure to read the integration tests to identify the required fields.

    data = flask.request.get_json()
    ehr_id = data.get('ehr-id')
    temperature = data.get('temperature')
    time = data.get('time')

    if not ehr_id:
        return flask.Response('Patient name is required', status=300)
    if not temperature:
        return flask.Response('Temperature is required', status=300)
    if not time:
        return flask.Response('Time is required', status=300)
    
    ehr_client = OpenEHRClient.OpenEHRClient(global_credentials['url'], global_credentials['username'], global_credentials['password'])

    composition = {
        'basic/composer|name' : get_composer_name(),
        'basic/temperature/temperature|magnitude' : temperature,
        'basic/temperature/time' : time,
        'basic/temperature/temperature|unit' : 'Cel',
        'basic/territory|code' : 'BE',
        'basic/territory|terminology' : 'ISO_3166-1'
    }

    composition_uid = ehr_client.addComposition(ehr_id, 'Basic.v0', composition)

    return flask.jsonify({'composition-uid': composition_uid})


@app.route('/list-patients', methods = [ 'POST' ])
def list_patients():
    # This call lists all the patients that are stored in EHRbase and
    # that have been created by the composer whose name is provided by
    # the "get_composer_name()" function.
    #
    # Inputs: The route takes no argument.
    #
    # Outputs: The body of the HTTP response must be a JSON array that
    # contains one JSON object for each patient. Each of those JSON
    # objects must contain the following fields: "ehr-id" is the
    # identifier of the parent EHR and "patient-name" is the name of
    # the patient.
    #
    # Hint: If your code is too slow, try using AQL instead of a
    # "homemade" loop over the EHR and compositions.

    
    ehr_client = OpenEHRClient.OpenEHRClient(global_credentials['url'], global_credentials['username'], global_credentials['password'])

    ehr_ids = ehr_client.listEHRs()
    
    patients = []

    for ehr_id in ehr_ids:
        compositions = ehr_client.listCompositions(ehr_id)

        for composition_id in compositions:
            composition = ehr_client.getComposition(ehr_id, composition_id, OpenEHRClient.CompositionFormat.SIMPLIFIED_JSON_FLAT)    
            #pprint.pprint(composition)
            curr_composition = composition['composition']
            if composition['templateId'] == 'MonitoredPatient.v0' and curr_composition['monitoredpatient.v0/composer|name'] == get_composer_name():
                patients.append({
                    'ehr-id': ehr_id,
                    'patient-name': curr_composition['monitoredpatient.v0/demographics_container/person/name']
                })
                

    return flask.jsonify(patients)

@app.route('/list-temperatures', methods = [ 'POST' ])
def list_temperatures():
    # This route lists all the body temperatures that have been
    # recorded for one patient, sorted by increasing time.
    #
    # Inputs: The body of the HTTP request must be a JSON object
    # containing the field "ehr-id" that provides the identifier of
    # the parent EHR.
    #
    # The list must be limited to the compositions that have been
    # created by the composer whose name is provided by the
    # "get_composer_name()" function.
    #
    # Outputs: The body of the HTTP response must be a JSON array that
    # contains one JSON object for each recorded temperature for the
    # patient. Each of those JSON objects must contain the following
    # fields: "time" is the time of the recorded temperature and
    # "temperature" is the value of the recorded temperature
    # (expressed in Celsius). The items must be sorted by increasing
    # value of "time".
    #
    # Hint: If your code is too slow, try using AQL instead of a
    # "homemade" loop over the EHR and compositions.

    # TODO

    ehr_client = OpenEHRClient.OpenEHRClient(global_credentials['url'], global_credentials['username'], global_credentials['password'])

    ehr_id = flask.request.get_json().get('ehr-id')
    
    compositions = ehr_client.listCompositions(ehr_id)
    temperatures = []

    for composition_id in compositions:
        composition = ehr_client.getComposition(ehr_id, composition_id, OpenEHRClient.CompositionFormat.SIMPLIFIED_JSON_FLAT)

        if composition['templateId'] == 'Basic.v0':
            curr_composition = composition['composition']
            if 'basic/temperature/temperature|magnitude' in curr_composition:
                temperature = curr_composition['basic/temperature/temperature|magnitude']
                time = curr_composition['basic/temperature/time']
                temperatures.append({
                    'temperature': temperature,
                    'time': time
                })

    temperatures.sort(key=lambda x: x['time'])


    return flask.jsonify(temperatures)



if __name__ == '__main__':
    app_initialize({
        'url' : 'http://localhost:8001/ehrbase/rest',
        'username' : 'ehrbase-user',
        'password' : 'SuperSecretPassword',
        'openehr-composer' : str(uuid.uuid4()),
    }, ' /resources/')
    app.run(debug = True)
