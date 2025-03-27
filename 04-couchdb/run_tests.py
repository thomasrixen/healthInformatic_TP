#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import CouchDBClient
import datetime
import os
import random
import requests
import student
import sys
import unittest
import uuid

from grading_toolbox import grade, grade_feedback



class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.credentials = {
            'url' : 'http://localhost:8002',
            'username' : 'admin',
            'password' : 'password',
            'couchdb-collection' : 'ehr',
        }
        cls.client = CouchDBClient.CouchDBClient(url=cls.credentials['url'],
                                                 username=cls.credentials['username'],
                                                 password=cls.credentials['password'])


    def test_twice_initialization(self):
        student.app_initialize(Tests.credentials)
        self.assertTrue(Tests.credentials['couchdb-collection'] in Tests.client.listDatabases())
        student.app_initialize(Tests.credentials)
        self.assertTrue(Tests.credentials['couchdb-collection'] in Tests.client.listDatabases())

    def test_create_patient(self):
        student.app_initialize(Tests.credentials)
        response = student.app.test_client().post('/create-patient', json = {
            'name' : 'HelloWorld1',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))
        self.assertTrue('id' in response.json)

        patient_id = response.json['id']
        patient = Tests.client.getDocument(Tests.credentials['couchdb-collection'], patient_id)
        self.assertEqual(4, len(patient))
        self.assertEqual('HelloWorld1', patient['name'])
        self.assertEqual('patient', patient['type'])
        self.assertEqual(patient_id, patient['_id'])
        self.assertTrue('_rev' in patient)

    def test_record_temperature(self):
        student.app_initialize(Tests.credentials)
        patient = student.app.test_client().post('/create-patient', json = {
            'name' : 'HelloWorld2',
        })
        self.assertEqual(200, patient.status_code)
        patient_id = patient.json['id']
        response = student.app.test_client().post('/record-temperature', json = {
            'patient_id' : patient_id,
            'temperature' : 37.2,
            'time' : '2025-03-01T14:15:16',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))
        self.assertTrue('id' in response.json)

        temperature = Tests.client.getDocument(Tests.credentials['couchdb-collection'], response.json['id'])
        self.assertEqual(6, len(temperature))
        self.assertEqual(patient_id, temperature['patient_id'])
        self.assertEqual('temperature', temperature['type'])
        self.assertEqual(response.json['id'], temperature['_id'])
        self.assertTrue('_rev' in temperature)
        self.assertTrue('time' in temperature)
        self.assertEqual(temperature['_id'], response.json['id'])

        t = datetime.datetime.strptime(temperature['time'], "%Y-%m-%dT%H:%M:%S.%f")
        delta = (datetime.datetime.now() - t)
        self.assertLess(abs(delta.total_seconds()), 10.0)  # Less than 10 seconds

    def test_list_patients(self):
        student.app_initialize(Tests.credentials)
        response = student.app.test_client().get('/patients')
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.json))

        patients = {}

        for i in range(10):
            name = str(uuid.uuid4())
            response = student.app.test_client().post('/create-patient', json = {
                'name' : name
            })
            self.assertEqual(200, response.status_code)
            patients[response.json['id']] = name

        response = student.app.test_client().get('/patients')
        self.assertEqual(200, response.status_code)
        self.assertEqual(10, len(response.json))

        for patient in response.json:
            self.assertTrue(patient['id'] in patients)
            self.assertEqual(patient['name'], patients[patient['id']])

    def test_list_temperatures(self):
        student.app_initialize(Tests.credentials)

        response = student.app.test_client().post('/create-patient', json = {
            'name' : 'HelloWorld4',
        })
        self.assertEqual(200, response.status_code)
        patient1 = response.json['id']

        response = student.app.test_client().post('/create-patient', json = {
            'name' : 'HelloWorld5',
        })
        self.assertEqual(200, response.status_code)
        patient2 = response.json['id']

        for p in [ patient1, patient2 ]:
            response = student.app.test_client().get('/temperatures?id=%s' % p)
            self.assertEqual(200, response.status_code)
            self.assertEqual(0, len(response.json))

        temperatures = {}
        for p in [ patient1, patient2 ]:
            t = list(range(10))
            random.shuffle(t)
            temperatures[p] = list(map(lambda x: x * 2.0 + 30.5, t))

            for x in temperatures[p]:
                response = student.app.test_client().post('/record-temperature', json = {
                    'patient_id' : p,
                    'temperature' : x,
                })

        for p in [ patient1, patient2 ]:
            response = student.app.test_client().get('/temperatures?id=%s' % p)
            self.assertEqual(200, response.status_code)
            self.assertEqual(10, len(response.json))
            for i in range(9):
                self.assertLess(response.json[i]['time'], response.json[i + 1]['time'])
            for i in range(10):
                self.assertAlmostEqual(response.json[i]['temperature'], temperatures[p][i], places=6)


if __name__ == '__main__':
    unittest.main(argv = [ sys.argv[0] ])
