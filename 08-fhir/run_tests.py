#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import OpenMRSClient
import datetime
import requests
import student
import sys
import time
import unittest
import uuid

from grading_toolbox import grade, grade_feedback




class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.credentials = {
            'openmrs-url' : 'http://localhost:8003/openmrs/ws/rest',
            'fhir-url' : 'http://localhost:8003/openmrs/ws/fhir2/R4',
            'username' : 'admin',
            'password' : 'Admin123',
        }
        cls.client = OpenMRSClient.OpenMRSClient(url='http://localhost:8003/openmrs/ws/rest',
                                                 username='admin',
                                                 password='Admin123')
        student.app_initialize(cls.credentials)


    def test_create_patient(self):
        name = str(uuid.uuid4())
        response = student.app.test_client().post('/create-patient', json = {
            'given-name' : 'Hello',
            'family-name' : name,
            'gender' : 'X',
            'birth-date' : '2001-01-03',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        self.assertTrue('patient-uuid' in response.json)
        self.assertTrue('visit-uuid' in response.json)

        try:
            patient = Tests.client.get_patient(response.json['patient-uuid'])
            visit = Tests.client.get_visit(response.json['visit-uuid'])
            self.assertEqual(patient['person']['display'], 'Hello ' + name)
            self.assertEqual(patient['person']['gender'], 'U')
            self.assertTrue(patient['person']['birthdate'].startswith('2001-01-03'))

            self.assertEqual(visit['patient']['uuid'], patient['uuid'])

            visits = Tests.client.list_visits(response.json['patient-uuid'])
            self.assertEqual(1, len(visits))
            self.assertEqual(response.json['visit-uuid'], visits[0])
            self.assertEqual(visit['stopDatetime'], None)

            self.assertEqual(0, len(Tests.client.list_encounters(response.json['visit-uuid'])))
        finally:
            Tests.client.delete_patient(response.json['patient-uuid'])

    def test_find_patient(self):
        name = str(uuid.uuid4())
        patient1 = Tests.client.create_patient('Hello', name, 'F', '2015-01-01')
        patient2 = Tests.client.create_patient('World', name, 'M', '2016-01-01')

        try:
            response = student.app.test_client().post('/find-patients', json = {
                'query' : name,
            })
            self.assertEqual(200, response.status_code)
            self.assertEqual(2, len(response.json))

            a = list(filter(lambda x: x['name'] == 'Hello ' + name, response.json))
            b = list(filter(lambda x: x['name'] == 'World ' + name, response.json))
            self.assertEqual(1, len(a))
            self.assertEqual(1, len(b))
            
            self.assertEqual(5, len(a[0]))
            self.assertEqual(a[0]['patient-uuid'], patient1)
            self.assertEqual(a[0]['birth-date'], '2015-01-01')
            self.assertEqual(a[0]['gender'], 'F')
            self.assertEqual(a[0]['patient-id'], Tests.client.get_patient_identifier(patient1))
            
            self.assertEqual(5, len(b[0]))
            self.assertEqual(b[0]['patient-uuid'], patient2)
            self.assertEqual(b[0]['birth-date'], '2016-01-01')
            self.assertEqual(b[0]['gender'], 'M')
            self.assertEqual(b[0]['patient-id'], Tests.client.get_patient_identifier(patient2))

        finally:
            Tests.client.delete_patient(patient1)
            Tests.client.delete_patient(patient2)

    @grade(2)
    def test_notes(self):
        name = str(uuid.uuid4())
        patient = Tests.client.create_patient('Welcome', name, 'X', '2017-01-07')

        try:
            response = student.app.test_client().get('/notes?patient-uuid=%s' % patient)
            self.assertEqual(500, response.status_code)  # No visit

            response = student.app.test_client().post('/record-note', json = {
                'patient-uuid' : patient,
                'text' : 'Hello 1',
            })
            self.assertEqual(500, response.status_code)  # No visit

            visit = Tests.client.create_visit(patient)

            response = student.app.test_client().get('/notes?patient-uuid=%s' % patient)
            self.assertEqual(200, response.status_code)
            self.assertEqual(2, len(response.json))

            patient_info = response.json['patient']
            self.assertEqual(5, len(patient_info))
            self.assertEqual(patient_info['birth-date'], '2017-01-07')
            self.assertEqual(patient_info['gender'], 'U')
            self.assertEqual(patient_info['id'], Tests.client.get_patient_identifier(patient))
            self.assertEqual(patient_info['name'], 'Welcome %s' % name)
            self.assertEqual(patient_info['visit-uuid'], visit)
            self.assertEqual(0, len(response.json['notes']))
            self.assertEqual(0, len(Tests.client.list_encounters(visit)))

            response = student.app.test_client().post('/record-note', json = {
                'patient-uuid' : patient,
                'text' : 'Hello 1',
            })
            self.assertEqual(200, response.status_code)
            self.assertEqual(2, len(response.json))

            encounter = Tests.client.get_encounter(response.json['encounter-uuid'])
            observation = Tests.client.get_observation(response.json['observation-uuid'])
            self.assertEqual(patient, encounter['patient']['uuid'])
            self.assertEqual(visit, encounter['visit']['uuid'])
            self.assertEqual('Visit Note', encounter['encounterType']['display'])
            self.assertEqual('Text of encounter note', observation['concept']['display'])
            self.assertEqual(encounter['uuid'], observation['encounter']['uuid'])

            encounters = Tests.client.list_encounters(visit)
            self.assertEqual(1, len(encounters))
            self.assertEqual(response.json['encounter-uuid'], encounters[0])
            self.assertEqual(1, len(Tests.client.list_observations(encounters[0])))

            response = student.app.test_client().get('/notes?patient-uuid=%s' % patient)
            self.assertEqual(200, response.status_code)

            self.assertEqual(response.json['patient'], patient_info)
            self.assertEqual(1, len(response.json['notes']))

            self.assertEqual(2, len(response.json['notes'][0]))
            self.assertTrue('time' in response.json['notes'][0])
            self.assertEqual('Hello 1', response.json['notes'][0]['text'])

            time.sleep(1.1)
            response = student.app.test_client().post('/record-note', json = {
                'patient-uuid' : patient,
                'text' : 'Hello 2',
            })
            self.assertEqual(200, response.status_code)

            time.sleep(1.1)
            response = student.app.test_client().post('/record-note', json = {
                'patient-uuid' : patient,
                'text' : 'Hello 3',
            })
            self.assertEqual(200, response.status_code)

            response = student.app.test_client().get('/notes?patient-uuid=%s' % patient)
            self.assertEqual(200, response.status_code)

            self.assertEqual(response.json['patient'], patient_info)
            self.assertEqual(3, len(response.json['notes']))
            self.assertTrue(response.json['notes'][0]['time'] >= response.json['notes'][1]['time'])
            self.assertTrue(response.json['notes'][1]['time'] >= response.json['notes'][2]['time'])
            self.assertEqual('Hello 1', response.json['notes'][2]['text'])
            self.assertEqual('Hello 2', response.json['notes'][1]['text'])
            self.assertEqual('Hello 3', response.json['notes'][0]['text'])

            encounters = Tests.client.list_encounters(visit)
            self.assertEqual(3, len(encounters))
            for encounter_uuid in encounters:
                encounter = Tests.client.get_encounter(encounter_uuid)
                self.assertEqual('Visit Note', encounter['encounterType']['display'])
                observations = Tests.client.list_observations(encounter_uuid)
                self.assertEqual(1, len(observations))
                observation = Tests.client.get_observation(observations[0])
                self.assertEqual('Text of encounter note', observation['concept']['display'])
                self.assertTrue(observation['value'].startswith('Hello '))

        finally:
            Tests.client.delete_patient(patient)


if __name__ == '__main__':
    unittest.main(argv = [ sys.argv[0] ])
