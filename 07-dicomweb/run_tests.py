#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import PIL.Image
import io
import student
import sys
import unittest

from grading_toolbox import grade, grade_feedback

# The tests use the content of the Orthanc demo server on 2025-04-08

class Tests(unittest.TestCase):
    def test_bad_queries(self):
        response = student.app.test_client().post('/lookup-studies', json = {
            'patient-id': '',
            'patient-name': '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-studies', json = {
            'patient-id': '',
            'study-description': '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-studies', json = {
            'patient-name': '',
            'study-description': '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-studies', json = {
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-series', json = {
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-series', json = {
            'study-instance-uid' : '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-series', json = {
            'study-instance-uid' : 'nope',
        })
        self.assertEqual(404, response.status_code)

        response = student.app.test_client().post('/lookup-instances', json = {
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-instances', json = {
            'study-instance-uid' : '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-instances', json = {
            'series-instance-uid' : '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/lookup-instances', json = {
            'study-instance-uid' : 'nope',
            'series-instance-uid' : 'nope',
        })
        self.assertEqual(404, response.status_code)

        response = student.app.test_client().post('/lookup-instances', json = {
            'study-instance-uid' : '2.16.840.1.113669.632.20.1211.10000357775',
            'series-instance-uid' : 'nope',
        })
        self.assertEqual(404, response.status_code)

        response = student.app.test_client().post('/lookup-instances', json = {
            'study-instance-uid' : 'nope',
            'series-instance-uid' : '1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114285654497',
        })
        self.assertEqual(404, response.status_code)

        response = student.app.test_client().post('/render-instance', json = {
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/render-instance', json = {
            'series-instance-uid' : '',
            'sop-instance-uid' : '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/render-instance', json = {
            'study-instance-uid' : '',
            'sop-instance-uid' : '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/render-instance', json = {
            'study-instance-uid' : '',
            'series-instance-uid' : '',
        })
        self.assertEqual(400, response.status_code)

        response = student.app.test_client().post('/render-instance', json = {
            'study-instance-uid' : 'nope',
            'series-instance-uid' : '1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114285654497',
            'sop-instance-uid' : '1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114314060548',
        })
        self.assertEqual(404, response.status_code)

        response = student.app.test_client().post('/render-instance', json = {
            'study-instance-uid' : '2.16.840.1.113669.632.20.1211.10000357775',
            'series-instance-uid' : 'nope',
            'sop-instance-uid' : '1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114314060548',
        })
        self.assertEqual(404, response.status_code)

        response = student.app.test_client().post('/render-instance', json = {
            'study-instance-uid' : '2.16.840.1.113669.632.20.1211.10000357775',
            'series-instance-uid' : '1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114285654497',
            'sop-instance-uid' : 'nope',
        })
        self.assertEqual(404, response.status_code)

        response = student.app.test_client().post('/render-instance', json = {
            'study-instance-uid' : 'nope',
            'series-instance-uid' : 'nope',
            'sop-instance-uid' : 'nope',
        })
        self.assertEqual(404, response.status_code)

    def test_lookup_studies(self):
        def to_dict(json):
            s = {}
            for item in json:
                self.assertTrue('patient-id' in item)
                self.assertTrue('patient-name' in item)
                self.assertTrue('study-description' in item)
                self.assertTrue('study-instance-uid' in item)
                s[item['study-instance-uid']] = item
            return s
        
        response = student.app.test_client().post('/lookup-studies', json = {
            'patient-id': '',
            'patient-name': '',
            'study-description': '',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(8, len(response.json))

        s = to_dict(response.json)
        self.assertEqual('ozp00SjY2xG', s['1.2.840.113619.2.176.2025.1499492.7391.1171285944.390']['patient-id'])
        self.assertEqual('KNIX', s['1.2.840.113619.2.176.2025.1499492.7391.1171285944.390']['patient-name'])
        self.assertEqual('Knee (R)', s['1.2.840.113619.2.176.2025.1499492.7391.1171285944.390']['study-description'])

        self.assertEqual('fYET5.0', s['1.2.840.113745.101000.1008000.38048.4626.5933732']['patient-id'])
        self.assertEqual('COMUNIX', s['1.2.840.113745.101000.1008000.38048.4626.5933732']['patient-name'])
        self.assertEqual('Neck^1HEAD_NECK_PETCT', s['1.2.840.113745.101000.1008000.38048.4626.5933732']['study-description'])

        self.assertEqual('', s['1.2.840.113745.101000.1008000.38179.6792.6324567']['patient-id'])
        self.assertEqual('ASSURANCETOURIX', s['1.2.840.113745.101000.1008000.38179.6792.6324567']['patient-name'])
        self.assertEqual('Thorax^1WB_PETCT', s['1.2.840.113745.101000.1008000.38179.6792.6324567']['study-description'])

        self.assertEqual('HN_P001', s['1.3.6.1.4.1.14519.5.2.1.2193.7172.847236098565581057121195872945']['patient-id'])
        self.assertEqual('HN_P001', s['1.3.6.1.4.1.14519.5.2.1.2193.7172.847236098565581057121195872945']['patient-name'])
        self.assertEqual('RT^HEAD_NECK (Adult)', s['1.3.6.1.4.1.14519.5.2.1.2193.7172.847236098565581057121195872945']['study-description'])

        self.assertEqual('Vafk,T,6', s['2.16.840.1.113669.632.20.1211.10000098591']['patient-id'])
        self.assertEqual('PHENIX', s['2.16.840.1.113669.632.20.1211.10000098591']['patient-name'])
        self.assertEqual('CT2 tête, face, sinus', s['2.16.840.1.113669.632.20.1211.10000098591']['study-description'])

        self.assertEqual('SOtNwu', s['2.16.840.1.113669.632.20.1211.10000231621']['patient-id'])
        self.assertEqual('INCISIX', s['2.16.840.1.113669.632.20.1211.10000231621']['patient-name'])
        self.assertEqual('Tête^Dental (Adulte)', s['2.16.840.1.113669.632.20.1211.10000231621']['study-description'])

        self.assertEqual('vAD7q3', s['2.16.840.1.113669.632.20.1211.10000315526']['patient-id'])
        self.assertEqual('VIX', s['2.16.840.1.113669.632.20.1211.10000315526']['patient-name'])
        self.assertEqual('Extrémités inférieures^Pied_cheville_UHR (Adulte)', s['2.16.840.1.113669.632.20.1211.10000315526']['study-description'])

        self.assertEqual('5Yp0E', s['2.16.840.1.113669.632.20.1211.10000357775']['patient-id'])
        self.assertEqual('BRAINIX', s['2.16.840.1.113669.632.20.1211.10000357775']['patient-name'])
        self.assertEqual('IRM cérébrale, neuro-crâne', s['2.16.840.1.113669.632.20.1211.10000357775']['study-description'])

        response = student.app.test_client().post('/lookup-studies', json = {
            'patient-id': '*f*',
            'patient-name': '',
            'study-description': '',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))

        s = to_dict(response.json)
        self.assertTrue('2.16.840.1.113669.632.20.1211.10000098591' in s)  # PHENIX (Vafk,T,6)
        self.assertTrue('1.2.840.113745.101000.1008000.38048.4626.5933732' in s)  # COMUNIX (fYET5.0)

        response = student.app.test_client().post('/lookup-studies', json = {
            'patient-id': '',
            'patient-name': '*C*',
            'study-description': '',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.json))

        s = to_dict(response.json)
        self.assertTrue('1.2.840.113745.101000.1008000.38179.6792.6324567' in s)  # ASSURANCETOURIX
        self.assertTrue('1.2.840.113745.101000.1008000.38048.4626.5933732' in s)  # COMUNIX
        self.assertTrue('2.16.840.1.113669.632.20.1211.10000231621' in s)  # INCISIX

        response = student.app.test_client().post('/lookup-studies', json = {
            'patient-id': '',
            'patient-name': '',
            'study-description': '*Adulte*',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))

        s = to_dict(response.json)
        self.assertTrue('2.16.840.1.113669.632.20.1211.10000231621' in s)  # INCISIX
        self.assertTrue('2.16.840.1.113669.632.20.1211.10000315526' in s)  # VIX

    def test_lookup_series(self):
        def to_dict(json):
            s = {}
            for item in json:
                self.assertTrue('modality' in item)
                self.assertTrue('series-description' in item)
                self.assertTrue('series-instance-uid' in item)
                s[item['series-instance-uid']] = item
            return s

        response = student.app.test_client().post('/lookup-series', json = {
            'study-instance-uid' : '1.2.840.113745.101000.1008000.38179.6792.6324567'
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.json))

        s = to_dict(response.json)
        self.assertEqual('PT', s['1.3.12.2.1107.5.1.4.36085.2.0.517109821292363']['modality'])
        self.assertEqual('PET WB-uncorrected', s['1.3.12.2.1107.5.1.4.36085.2.0.517109821292363']['series-description'])
        self.assertEqual('1.3.12.2.1107.5.1.4.36085.2.0.517109821292363', s['1.3.12.2.1107.5.1.4.36085.2.0.517109821292363']['series-instance-uid'])

        self.assertEqual('PT', s['1.3.12.2.1107.5.1.4.36085.2.0.517714246252254']['modality'])
        self.assertEqual('PET WB', s['1.3.12.2.1107.5.1.4.36085.2.0.517714246252254']['series-description'])
        self.assertEqual('1.3.12.2.1107.5.1.4.36085.2.0.517714246252254', s['1.3.12.2.1107.5.1.4.36085.2.0.517714246252254']['series-instance-uid'])

        self.assertEqual('CT', s['1.3.12.2.1107.5.99.1.24063.4.0.446793548272429']['modality'])
        self.assertEqual('CT WB w/contrast 5.0 B30s', s['1.3.12.2.1107.5.99.1.24063.4.0.446793548272429']['series-description'])
        self.assertEqual('1.3.12.2.1107.5.99.1.24063.4.0.446793548272429', s['1.3.12.2.1107.5.99.1.24063.4.0.446793548272429']['series-instance-uid'])

        response = student.app.test_client().post('/lookup-series', json = {
            'study-instance-uid' : '2.16.840.1.113669.632.20.1211.10000231621'
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))

        self.assertEqual('CT', response.json[0]['modality'])
        self.assertEqual('Dentascan  0.75  H60s', response.json[0]['series-description'])
        self.assertEqual('1.3.12.2.1107.5.1.4.54693.30000006053107175587500014744', response.json[0]['series-instance-uid'])

    def test_lookup_instances(self):
        response = student.app.test_client().post('/lookup-instances', json = {
            'study-instance-uid' : '1.3.6.1.4.1.14519.5.2.1.2193.7172.847236098565581057121195872945',
            'series-instance-uid' : '1.3.6.1.4.1.14519.5.2.1.2193.7172.329574933994116044160154909094',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))
        self.assertEqual('1.3.6.1.4.1.14519.5.2.1.2193.7172.227588763982019545194084732872', response.json[0])

        response = student.app.test_client().post('/lookup-instances', json = {
            'study-instance-uid' : '1.3.6.1.4.1.14519.5.2.1.2193.7172.847236098565581057121195872945',
            'series-instance-uid' : '1.3.6.1.4.1.14519.5.2.1.2193.7172.213354059528434006228837759936',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))
        self.assertEqual('1.3.6.1.4.1.14519.5.2.1.2193.7172.863063138942128758032875897774', response.json[0])

        response = student.app.test_client().post('/lookup-instances', json = {
            'study-instance-uid' : '2.16.840.1.113669.632.20.1211.10000357775',
            'series-instance-uid' : '1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114285654497',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(22, len(response.json))
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114314079549', response.json[0])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302945538', response.json[1])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114314060548', response.json[2])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302925537', response.json[3])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114314040547', response.json[4])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302906536', response.json[5])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114314021546', response.json[6])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302885535', response.json[7])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114314003545', response.json[8])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302867534', response.json[9])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114313982544', response.json[10])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302846533', response.json[11])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114313964543', response.json[12])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302828532', response.json[13])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114313943542', response.json[14])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302809531', response.json[15])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114313925541', response.json[16])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302789530', response.json[17])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114313904540', response.json[18])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302770529', response.json[19])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114313885539', response.json[20])
        self.assertEqual('1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114302750528', response.json[21])

    def test_render_instance(self):
        response = student.app.test_client().post('/render-instance', json = {
            'study-instance-uid' : '2.16.840.1.113669.632.20.1211.10000357775',
            'series-instance-uid' : '1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114285654497',
            'sop-instance-uid' : '1.3.46.670589.11.0.0.11.4.2.0.8743.5.5396.2006120114314060548',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual('image/png', response.headers['Content-Type'])
        image = PIL.Image.open(io.BytesIO(response.data))
        self.assertEqual('PNG', image.format)
        self.assertEqual(288, image.size[0])
        self.assertEqual(288, image.size[1])
        self.assertEqual('L', image.mode)

        response = student.app.test_client().post('/render-instance', json = {
            'study-instance-uid' : '2.16.840.1.113669.632.20.1211.10000098591',
            'series-instance-uid' : '1.2.840.113704.1.111.5692.1127828999.2',
            'sop-instance-uid' : '1.2.840.113704.7.1.1.6632.1127829031.2',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual('image/png', response.headers['Content-Type'])
        image = PIL.Image.open(io.BytesIO(response.data))
        self.assertEqual('PNG', image.format)
        self.assertEqual(512, image.size[0])
        self.assertEqual(358, image.size[1])
        self.assertEqual('L', image.mode)

if __name__ == '__main__':
    unittest.main(argv = [ sys.argv[0] ])
