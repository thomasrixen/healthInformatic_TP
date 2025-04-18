#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import HL7Toolbox
import OpenMRSClient
import os
import requests
import student
import sys
import unittest

from grading_toolbox import grade, grade_feedback




class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.credentials = {
            'url' : 'http://localhost:8003/openmrs/ws/rest',
            'username' : 'admin',
            'password' : 'Admin123',
        }
        cls.client = OpenMRSClient.OpenMRSClient(url=cls.credentials['url'],
                                                 username=cls.credentials['username'],
                                                 password=cls.credentials['password'])
        student.app_initialize(cls.credentials)


    def setUp(self):
        # Make sure that the patient of interest in the HL7 messages
        # is removed before starting the tests
        patient = Tests.client.find_patient_by_custom_id('3333333333')
        if patient != None:
            Tests.client.delete_patient(patient)

    def send_message(self, message):
        response = student.app.test_client().post('/hl7', data=message, headers = {
            'Content-Type' : 'text/hl7v2',
        })
        self.assertEqual(200, response.status_code)
        return response.data

    def send_message_from_file(self, filename):
        with open(os.path.join(os.path.dirname(__file__), 'resources', filename), 'rb') as f:
            return self.send_message(f.read())

    def test_find_patient(self):
        self.assertEqual(Tests.client.find_patient_by_custom_id('3333333333'), None)
        response = student.app.test_client().get('/find-patient?custom-id=3333333333')
        self.assertEqual(404, response.status_code)

        patient_uuid = Tests.client.create_patient('Hello', 'World', 'M', '2002-03-04', custom_identifiers = [ '3333333333' ])
        response = student.app.test_client().get('/find-patient?custom-id=3333333333')
        self.assertEqual(404, response.status_code)

        visit_uuid = Tests.client.create_visit(patient_uuid, start_date_time = '2018-03-01')
        response = student.app.test_client().get('/find-patient?custom-id=3333333333')
        self.assertEqual(200, response.status_code)
        self.assertEqual(patient_uuid, response.json['patient-uuid'])
        self.assertEqual(visit_uuid, response.json['visit-uuid'])

    def test_register_patient(self):
        self.assertEqual(Tests.client.find_patient_by_custom_id('3333333333'), None)
        self.send_message_from_file('RegisterPatient.hl7')
        patient_uuid = Tests.client.find_patient_by_custom_id('3333333333')
        self.assertNotEqual(patient_uuid, None)

        patient = Tests.client.get_patient(patient_uuid)
        self.assertTrue(patient['person']['birthdate'].startswith('1965-11-12T'))
        self.assertEqual('FREDRICA SMITH', patient['person']['display'])
        self.assertEqual('F', patient['person']['gender'])

        visits = Tests.client.list_visits(patient_uuid)
        self.assertEqual(1, len(visits))
        visit = Tests.client.get_visit(visits[0])
        self.assertTrue(visit['startDatetime'].startswith('2018-03-01T'))

    def test_register_twice(self):
        self.send_message_from_file('RegisterPatient.hl7')
        ack = HL7Toolbox.parse_message(self.send_message_from_file('RegisterPatient.hl7'))
        self.assertEqual(2, len(ack))

    def test_acknowledgments(self):
        ack = HL7Toolbox.parse_message(self.send_message_from_file('RegisterPatient.hl7'))
        self.assertEqual(2, len(ack))
        self.assertEqual('MSH', str(ack[0][0]))
        self.assertEqual('|', str(ack[0][1]))
        self.assertEqual('^~\&', str(ack[0][2]))
        self.assertEqual('STUDENT', str(ack[0][3]))
        self.assertEqual('INGINIOUS', str(ack[0][4]))
        self.assertEqual('MS4_AZ', str(ack[0][5]))
        self.assertEqual('UCLOUVAIN', str(ack[0][6]))
        self.assertEqual('ADT^A04', str(ack[0][9]))
        self.assertEqual('MSA', str(ack[1][0]))
        self.assertEqual('AA', str(ack[1][1]))
        self.assertEqual('IHS-20180301110000.00120', str(ack[1][2]))

        ack = HL7Toolbox.parse_message(self.send_message_from_file('Unsupported.hl7'))
        self.assertEqual(2, len(ack))
        self.assertEqual('MSH', str(ack[0][0]))
        self.assertEqual('|', str(ack[0][1]))
        self.assertEqual('^~\&', str(ack[0][2]))
        self.assertEqual('GHH LAB, INC.', str(ack[0][3]))
        self.assertEqual('GOOD HEALTH HOSPITAL', str(ack[0][4]))
        self.assertEqual('ADT1', str(ack[0][5]))
        self.assertEqual('GOOD HEALTH HOSPITAL', str(ack[0][6]))
        self.assertEqual('ADT^A01', str(ack[0][9]))
        self.assertEqual('MSA', str(ack[1][0]))
        self.assertEqual('AE', str(ack[1][1]))  # You are not supposed to support ADT^A01 messages
        self.assertEqual('MSG00001', str(ack[1][2]))

    def test_record_vitals(self):
        patient_uuid = Tests.client.create_patient('Hello', 'World', 'M', '2002-03-04', custom_identifiers = [ '3333333333' ])
        visit_uuid = Tests.client.create_visit(patient_uuid, start_date_time = '2018-03-01')
        self.assertEqual(0, len(Tests.client.list_encounters(visit_uuid)))
        self.send_message_from_file('RegisterVitals.hl7')

        encounters = Tests.client.list_encounters(visit_uuid)
        self.assertEqual(1, len(encounters))

        encounter = Tests.client.get_encounter(encounters[0])
        self.assertEqual('Vitals', encounter['encounterType']['display'])

        observations = Tests.client.list_observations(encounters[0])
        self.assertEqual(2, len(observations))

        found_temperature = False
        found_weight = False

        for observation_uuid in observations:
            observation = Tests.client.get_observation(observation_uuid)
            if (observation['concept']['display'] == 'Weight (kg)' and
                abs(float(observation['value']) - 59.5) < 0.00001):
                found_weight = True
            elif (observation['concept']['display'] == 'Temperature (c)' and
                  abs(float(observation['value']) - 37.0) < 0.00001):
                found_temperature = True

        self.assertTrue(found_temperature)
        self.assertTrue(found_weight)

    def test_record_visit_note(self):
        patient_uuid = Tests.client.create_patient('Hello', 'World', 'M', '2002-03-04', custom_identifiers = [ '3333333333' ])
        visit_uuid = Tests.client.create_visit(patient_uuid, start_date_time = '2018-03-01')
        self.assertEqual(0, len(Tests.client.list_encounters(visit_uuid)))
        self.send_message_from_file('RegisterVisitNote.hl7')

        encounters = Tests.client.list_encounters(visit_uuid)
        self.assertEqual(1, len(encounters))

        encounter = Tests.client.get_encounter(encounters[0])
        self.assertEqual('Visit Note', encounter['encounterType']['display'])

        observations = Tests.client.list_observations(encounters[0])
        self.assertEqual(1, len(observations))

        observation = Tests.client.get_observation(observations[0])
        self.assertEqual('Text of encounter note', observation['concept']['display'])
        self.assertEqual('Family History: Colon Cancer Mother 57', observation['value'])


if __name__ == '__main__':
    unittest.main(argv = [ sys.argv[0] ])
