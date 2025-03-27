#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import OpenEHRClient
import os
import random
import student
import sys
import unittest
import uuid

from grading_toolbox import grade, grade_feedback



class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.credentials_user = {
            'url' : 'http://localhost:8001/ehrbase/rest',
            'username' : 'ehrbase-user',
            'password' : 'SuperSecretPassword',
            'openehr-composer' : str(uuid.uuid4()),
        }
        cls.credentials_admin = {
            'url' : 'http://localhost:8001/ehrbase/rest',
            'username' : 'ehrbase-admin',
            'password' : 'EvenMoreSecretPassword',
        }
        cls.client = OpenEHRClient.OpenEHRClient(url=cls.credentials_user['url'],
                                                 username=cls.credentials_user['username'],
                                                 password=cls.credentials_user['password'])


    def test_twice_initialization(self):
        student.app_initialize(Tests.credentials_user, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources'))
        self.assertTrue('Basic.v0' in Tests.client.listTemplates())
        self.assertTrue('MonitoredPatient.v0' in Tests.client.listTemplates())
        student.app_initialize(Tests.credentials_user, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources'))
        self.assertTrue('Basic.v0' in Tests.client.listTemplates())
        self.assertTrue('MonitoredPatient.v0' in Tests.client.listTemplates())

    def test_create_ehr(self):
        student.app_initialize(Tests.credentials_user, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources'))
        response = student.app.test_client().post('/create-patient', json = {
            'patient-name' : 'HelloWorld1',
        })
        self.assertEqual(200, response.status_code)
        ehr_id = response.json['ehr-id']
        ehr = Tests.client.getEHR(ehr_id)
        self.assertEqual(ehr_id, ehr['ehr_id']['value'])
        compositions = Tests.client.listCompositions(ehr_id)
        self.assertEqual(1, len(compositions))
        composition = Tests.client.getComposition(ehr_id, compositions[0])
        self.assertEqual(compositions[0], composition['compositionUid'])
        self.assertEqual(ehr_id, composition['ehrId'])
        self.assertEqual('MonitoredPatient.v0', composition['templateId'])
        self.assertEqual(composition['composition']['monitoredpatient.v0/_uid'], composition['compositionUid'])

        # Below are the mandatory fields when creating a "MonitoredPatient.v0" composition
        self.assertEqual(composition['composition']['monitoredpatient.v0/composer|name'], Tests.credentials_user['openehr-composer'])
        self.assertEqual(composition['composition']['monitoredpatient.v0/demographics_container/person/name'], 'HelloWorld1')
        self.assertEqual(composition['composition']['monitoredpatient.v0/territory|code'], 'BE')
        self.assertEqual(composition['composition']['monitoredpatient.v0/territory|terminology'], 'ISO_3166-1')

    def test_record_temperature(self):
        student.app_initialize(Tests.credentials_user, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources'))
        patient = student.app.test_client().post('/create-patient', json = {
            'patient-name' : 'HelloWorld2',
        })
        self.assertEqual(200, patient.status_code)
        ehr_id = patient.json['ehr-id']
        temperature = student.app.test_client().post('/record-temperature', json = {
            'ehr-id' : ehr_id,
            'temperature' : 37.2,
            'time' : '2025-03-01T14:15:16',
        })
        composition_uid = temperature.json['composition-uid']
        self.assertEqual(200, temperature.status_code)
        composition = Tests.client.getComposition(ehr_id, composition_uid)
        self.assertEqual(composition_uid, composition['compositionUid'])
        self.assertEqual(ehr_id, composition['ehrId'])
        self.assertEqual('Basic.v0', composition['templateId'])
        self.assertEqual(composition['composition']['basic/_uid'], composition['compositionUid'])

        # Below are the mandatory fields when creating a "Basic.v0" composition
        self.assertAlmostEqual(composition['composition']['basic/temperature/temperature|magnitude'], 37.2, places=6)
        self.assertEqual(composition['composition']['basic/composer|name'], Tests.credentials_user['openehr-composer'])
        self.assertEqual(composition['composition']['basic/temperature/temperature|unit'], 'Cel')
        self.assertEqual(composition['composition']['basic/temperature/time'], '2025-03-01T14:15:16')
        self.assertEqual(composition['composition']['basic/territory|code'], 'BE')
        self.assertEqual(composition['composition']['basic/territory|terminology'], 'ISO_3166-1')

    def test_list_patients(self):
        student.app_initialize(Tests.credentials_user, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources'))
        patients = student.app.test_client().post('/list-patients')
        self.assertEqual(200, patients.status_code)
        a = { x['ehr-id']:x for x in patients.json }
        patient = student.app.test_client().post('/create-patient', json = {
            'patient-name' : 'HelloWorld3',
        })
        self.assertEqual(200, patient.status_code)
        patients = student.app.test_client().post('/list-patients')
        self.assertEqual(200, patients.status_code)
        b = { x['ehr-id']:x for x in patients.json }
        self.assertEqual(len(b), len(a) + 1)
        self.assertFalse(patient.json['ehr-id'] in a)
        self.assertTrue(patient.json['ehr-id'] in b)
        self.assertEqual('HelloWorld3', b[patient.json['ehr-id']]['patient-name'])

    def test_list_temperatures(self):
        student.app_initialize(Tests.credentials_user, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources'))
        patient = student.app.test_client().post('/create-patient', json = {
            'patient-name' : 'HelloWorld4',
        })
        self.assertEqual(200, patient.status_code)
        ehr_id = patient.json['ehr-id']
        temperatures = student.app.test_client().post('/list-temperatures', json = {
            'ehr-id' : ehr_id
        })
        self.assertEqual(200, temperatures.status_code)
        self.assertEqual(0, len(temperatures.json))
        t = list(range(10))
        random.shuffle(t)
        for i in t:
            temperature = student.app.test_client().post('/record-temperature', json = {
                'ehr-id' : ehr_id,
                'temperature' : i * 2.0 + 30.5,
                'time' : '2025-03-01T14:%02d:16' % i,
            })
        temperatures = student.app.test_client().post('/list-temperatures', json = {
            'ehr-id' : patient.json['ehr-id']
        })
        self.assertEqual(200, temperatures.status_code)
        self.assertEqual(10, len(temperatures.json))
        for i in range(9):
            self.assertLess(temperatures.json[i]['time'], temperatures.json[i + 1]['time'])
        for i in range(10):
            j = float(temperatures.json[i]['time'].split(':') [1])
            temperature = j * 2.0 + 30.5
            self.assertAlmostEqual(temperatures.json[i]['temperature'], temperature, places=6)


if __name__ == '__main__':
    unittest.main(argv = [ sys.argv[0] ])
