#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import student
import unittest

from grading_toolbox import grade, grade_feedback

PARAMETERS = [ 'voltage', 'resistance', 'current', 'power' ]

class Tests(unittest.TestCase):
    @grade(3)
    def test_celsius(self):
        response = student.app.test_client().post('/convert-celsius', json = {
            'celsius' : 15
        })
        self.assertEqual(200, response.status_code)
        self.assertAlmostEqual(59, response.json['fahrenheit'], places = 6)
        self.assertAlmostEqual(288.15, response.json['kelvin'], places = 6)

        response = student.app.test_client().post('/convert-celsius', json = {
            'celsius' : -10.3
        })
        self.assertEqual(200, response.status_code)
        self.assertAlmostEqual(13.46, response.json['fahrenheit'], places = 6)
        self.assertAlmostEqual(262.85, response.json['kelvin'], places = 6)

    @grade(2)
    def test_bad_celsius(self):
        response = student.app.test_client().post('/convert-celsius', json = {})
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/convert-celsius', json = {
            'celsius' : 'invalid'
        })
        self.assertEqual(400, response.status_code)

    def test_electricity_vr(self):
        response = student.app.test_client().post('/compute-electricity', json = {
            'voltage' : 12,
            'resistance' : 18
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json.keys()))
        self.assertAlmostEqual(2 / 3, response.json['current'], places = 6)
        self.assertAlmostEqual(8, response.json['power'], places = 6)

        response = student.app.test_client().post('/compute-electricity', json = {
            'voltage' : 12,
            'resistance' : 50
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json.keys()))
        self.assertAlmostEqual(0.24, response.json['current'], places = 6)
        self.assertAlmostEqual(2.88, response.json['power'], places = 6)

        response = student.app.test_client().post('/compute-electricity', json = {
            'voltage' : 30,
            'resistance' : 5
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json.keys()))
        self.assertAlmostEqual(6, response.json['current'], places = 6)
        self.assertAlmostEqual(180, response.json['power'], places = 6)

    def test_electricity_vi(self):
        response = student.app.test_client().post('/compute-electricity', json = {
            'voltage' : 30,
            'current' : 6
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json.keys()))
        self.assertAlmostEqual(5, response.json['resistance'], places = 6)
        self.assertAlmostEqual(180, response.json['power'], places = 6)

    def test_electricity_vp(self):
        response = student.app.test_client().post('/compute-electricity', json = {
            'voltage' : 30,
            'power' : 180
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json.keys()))
        self.assertAlmostEqual(5, response.json['resistance'], places = 6)
        self.assertAlmostEqual(6, response.json['current'], places = 6)

    def test_electricity_ri(self):
        response = student.app.test_client().post('/compute-electricity', json = {
            'resistance' : 5,
            'current' : 6
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json.keys()))
        self.assertAlmostEqual(30, response.json['voltage'], places = 6)
        self.assertAlmostEqual(180, response.json['power'], places = 6)

    def test_electricity_rp(self):
        response = student.app.test_client().post('/compute-electricity', json = {
            'resistance' : 5,
            'power' : 180
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json.keys()))
        self.assertAlmostEqual(30, response.json['voltage'], places = 6)
        self.assertAlmostEqual(6, response.json['current'], places = 6)

    def test_electricity_ip(self):
        response = student.app.test_client().post('/compute-electricity', json = {
            'current' : 6,
            'power' : 180
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json.keys()))
        self.assertAlmostEqual(30, response.json['voltage'], places = 6)
        self.assertAlmostEqual(5, response.json['resistance'], places = 6)

    @grade(2)
    def test_electricity_all(self):
        for i in PARAMETERS:
            for j in PARAMETERS:
                if i != j:
                    request = {
                        i : 7,
                        j : 11
                    }
                    response = student.app.test_client().post('/compute-electricity', json=request)
                    self.assertEqual(200, response.status_code)
                    self.assertEqual(2, len(response.json.keys()))

                    for k in PARAMETERS:
                        if k != i and k != j:
                            request[k] = response.json[k]

                    self.assertAlmostEqual(request['voltage'], request['resistance'] * request['current'], places = 6)
                    self.assertAlmostEqual(request['power'], request['current'] * request['voltage'], places = 6)

    @grade(2)
    def test_bad_electricity_1(self):
        # 0 parameter provided
        response = student.app.test_client().post('/compute-electricity', json = {})
        self.assertEqual(400, response.status_code)

        # 1 parameter provided
        for i in PARAMETERS:
            response = student.app.test_client().post('/compute-electricity', json = {
                i : 1
            })
            self.assertEqual(400, response.status_code)

        # 3 parameters provided
        for i in PARAMETERS:
            request = {}
            for j in PARAMETERS:
                if i != j:
                    request[j] = 1
            response = student.app.test_client().post('/compute-electricity', json = request)
            self.assertEqual(400, response.status_code)

        # 4 parameters provided
        request = {}
        for i in PARAMETERS:
            request[i] = 1
        response = student.app.test_client().post('/compute-electricity', json = request)
        self.assertEqual(400, response.status_code)

        # Not-a-number provided
        request = {}
        for i in PARAMETERS:
            for j in PARAMETERS:
                if i != j:
                    request = {
                        i : 1,
                        j : 'invalid'
                    }
                response = student.app.test_client().post('/compute-electricity', json = request)
                self.assertEqual(400, response.status_code)

if __name__ == '__main__':
    unittest.main()
