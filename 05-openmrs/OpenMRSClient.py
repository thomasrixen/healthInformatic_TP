#!/usr/bin/env python3

# Copyright (c) 2024-2025, Sebastien Jodogne, ICTEAM UCLouvain, Belgium
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import base64
import datetime
import json
import requests

# Class that represents a connection to some OpenMRS server.
class OpenMRSClient:

    # Constructor for the connection: An URL, an username, and a
    # password are expected.
    def __init__(self,
                 url = 'http://localhost:8003/openmrs/ws/rest',
                 username = 'admin',
                 password = 'Admin123'):
        # Make sure that the URL does not end with a slash
        if url.endswith('/'):
            self.url = url[0 : len(url) - 1]
        else:
            self.url = url

        self.auth = requests.auth.HTTPBasicAuth(username, password)


    # Internal method to look for the UUID of a resource given its
    # display name, inside a table of the OpenMRS data model.
    def _lookup_entity(self, table, display_name):
        r = requests.get('%s/v1/%s' % (self.url, table), auth = self.auth)
        r.raise_for_status()

        for result in r.json() ['results']:
            if result['display'] == display_name:
                return result['uuid']

        raise Exception('Unable to find entity with display name "%s" in table "%s"' %
                        (table, display_name))


    # Internal method to execute a POST request against OpenMRS with a JSON body.
    def _do_post_json(self, path, content):
        r = requests.post(self.url + path, json.dumps(content),
                          auth = self.auth,
                          headers = {
                              'Content-Type' : 'application/json'
                          })
        r.raise_for_status()
        return r.json()
        

    # Internal method to generate a new patient identifier.
    def _generate_patient_identifier(self):
        r = requests.get('%s/v1/idgen/identifiersource' % self.url, auth = self.auth)
        r.raise_for_status()

        generator = r.json() ['results'][0]  # Use the first available generator

        identifierType = generator['identifierType']['uuid']

        content = {
            'generateIdentifiers': True,
            'sourceUuid': generator['uuid'],
            'numberToGenerate': 1,
        }

        r = self._do_post_json('/v1/idgen/identifiersource', content)
        return (identifierType, r['identifiers'][0])


    # Retrieve the current date-time in a format that can be used in
    # the REST API of OpenMRS.
    def get_now(self):
        # OpenMRS doesn't support milliseconds or microseconds
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat()


    # Parse a string field returned by OpenMRS that contains a date-time.
    def parse_date_time(self, date_time):
        # https://stackoverflow.com/a/48539157
        try:
            return datetime.datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            return datetime.datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S%z')


    # Given a string field returned by OpenMRS that contains a
    # date-time, remove the time information, and return only the formatted date.
    def keep_only_date(self, date_time):
        return self.parse_date_time(date_time).strftime('%Y-%m-%d')


    # Add a new patient to OpenMRS and returns her UUID.
    def create_patient(self, given_name, family_name, gender, birth_date,
                       location = 'Unknown Location'):
        identifier = self._generate_patient_identifier()

        content = {
            'person' : {
                'names': [
                    {
                        'givenName': given_name,
                        'familyName': family_name,
                    }
                ],
                'gender': gender,
                'birthdate': birth_date,
                'addresses': [
                    {
                    }
                ]
            },
            'identifiers': [
                {
                    # Use an auto-generated patient identifier
                    'identifierType': identifier[0],
                    'identifier': identifier[1],
                    'location': self._lookup_entity('location', location),
                }
            ]
        }

        return self._do_post_json('/v1/patient', content) ['uuid']


    # Look for patients given their name or identifier, and return the
    # list of UUIDs of the matching patients. The query must contain
    # at least 2 characters. Note that if there are too many matches,
    # OpenMRS will only return a subset of the matching patients.
    def find_patients(self, query):
        r = requests.get('%s/v1/patient' % self.url, params = { 'q' : query }, auth = self.auth)
        r.raise_for_status()
        return list(map(lambda x: x['uuid'], r.json() ['results']))


    # Retrieve information about one patient, given her UUID.
    def get_patient(self, patient_uuid):
        r = requests.get('%s/v1/patient/%s' % (self.url, patient_uuid), auth = self.auth)
        r.raise_for_status()
        return r.json()
    

    # Retrieve the public identifier (not the UUID) of a patient, given her UUID.
    def get_patient_identifier(self, patient_uuid, identifier_type = 'OpenMRS ID'):
        patient = self.get_patient(patient_uuid)

        identifiers = []
        for identifier in patient['identifiers']:
            r = requests.get('%s/v1/patient/%s/identifier/%s' % (self.url, patient_uuid, identifier['uuid']), auth = self.auth)
            r.raise_for_status()
            if r.json() ['identifierType']['display'] == identifier_type:
                identifiers.append(r.json() ['identifier'])

        if len(identifiers) == 1:
            return identifiers[0]
        else:
            raise Exception('Unable to get identifier of patient: %s' % patient_uuid)


    # Update the content of a patient.
    def update_patient(self, patient_uuid, content):
        self._do_post_json('/v1/patient/%s' % patient_uuid, content)


    # Delete a patient, given her UUID.
    def delete_patient(self, patient_uuid):
        r = requests.delete('%s/v1/patient/%s' % (self.url, patient_uuid), auth = self.auth)
        r.raise_for_status()


    # List the visits associated with one patient, given her UUID.
    def list_visits(self, patient_uuid):
        r = requests.get('%s/v1/visit?patient=%s' % (self.url, patient_uuid), auth = self.auth)
        r.raise_for_status()
        return list(map(lambda x: x['uuid'], r.json() ['results']))


    # Retrieve information about one visit, given its UUID.
    def get_visit(self, visit_uuid):
        r = requests.get('%s/v1/visit/%s' % (self.url, visit_uuid), auth = self.auth)
        r.raise_for_status()
        return r.json()


    # Create a new visit associated with the patient whose UUID is provided as argument.
    # The method returns the UUID of the newly created visit.
    def create_visit(self, patient_uuid,
                     visit_type = 'Facility Visit',
                     start_date_time = None):
        content = {
            'patient' : patient_uuid,
            'visitType' : self._lookup_entity('visittype', visit_type),
        }

        if start_date_time != None:
            content['startDatetime'] = start_date_time
        
        return self._do_post_json('/v1/visit', content) ['uuid']


    # End the visit whose UUID is provided as argument.
    def end_visit(self, visit_uuid, stop_date_time = None):
        if stop_date_time == None:
            s = self.get_now()
        else:
            s = stop_date_time

        self._do_post_json('/v1/visit/%s' % visit_uuid, {
            'stopDatetime' : s,
        })


    # Delete a visit, given its UUID.
    def delete_visit(self, visit_uuid):
        r = requests.delete('%s/v1/visit/%s' % (self.url, visit_uuid), auth = self.auth)
        r.raise_for_status()


    # Create a new encounter associated with the visit whose UUID is
    # provided as argument. In the OpenMRS Reference Application, the
    # "encounter_type" can be "Vitals", "Attachment Upload", or "Visit Note".
    # The method returns the UUID of the newly created encounter.
    def create_encounter(self, visit_uuid, encounter_type,
                         form = None,
                         location = 'Unknown Location',
                         provider = 'UNKNOWN - Super User',
                         role = 'Unknown',
                         date_time = None):
        content = {
            'patient' : self.get_visit(visit_uuid) ['patient']['uuid'],
            'encounterType' : self._lookup_entity('encountertype', encounter_type),
            'visit' : visit_uuid,
            'encounterDatetime' : self.get_now(),
        }

        if form != None:
            content['form'] = self._lookup_entity('form', form)

        if location != None:
            content['location'] = self._lookup_entity('location', location)

        if provider != None:
            content['encounterProviders'] = [
                {
                    'provider' : self._lookup_entity('provider', provider),
                    'encounterRole' : self._lookup_entity('encounterrole', role)
                },
            ]

        if date_time != None:
            content['encounterDatetime'] = date_time

        return self._do_post_json('/v1/encounter', content) ['uuid']


    # List the encounters that are associated with the visit whose UUID is provided as argument.
    def list_encounters(self, visit_uuid):
        return list(map(lambda x: x['uuid'], self.get_visit(visit_uuid) ['encounters']))


    # Retrieve information about one encounter, given its UUID.
    def get_encounter(self, encounter_uuid):
        r = requests.get('%s/v1/encounter/%s' % (self.url, encounter_uuid), auth = self.auth)
        r.raise_for_status()
        return r.json()


    # List the observations that are associated with the encounter whose UUID is provided as argument.
    def list_observations(self, encounter_uuid):
        return list(map(lambda x: x['uuid'], self.get_encounter(encounter_uuid) ['obs']))


    # Retrieve information about one observation, given its UUID.
    def get_observation(self, observation_uuid):
        r = requests.get('%s/v1/obs/%s' % (self.url, observation_uuid), auth = self.auth)
        r.raise_for_status()
        return r.json()

    # Look for a concept, given its display name, and returns the UUID of this concept.
    def lookup_concept(self, concept_name):
        r = requests.get('%s/v1/concept' % self.url, params = { 'name' : concept_name }, auth = self.auth)
        r.raise_for_status()
        results = r.json() ['results']
        if len(results) != 1:
            raise Exception('Unknown concept: %s' % concept_name)
        else:
            return results[0]['uuid']


    # Create an observation, and associate it with the encounter whose
    # UUID is provided as argument. The observation maps one concept
    # (specified by its name) to one value (given as a string). In the
    # OpenMRS Reference application, notable concepts are "Temperature
    # (c)" and "Weight (kg)" for "Vitals" encounters, and "Text of
    # encounter note" for "Visit Note" encounters. The method returns
    # the UUID of the newly created observation.
    def create_observation(self, encounter_uuid, concept_name, value, comment = None):
        patient_uuid = self.get_encounter(encounter_uuid) ['patient']['uuid']
        person_uuid = self.get_patient(patient_uuid) ['person']['uuid']

        content = {
            'concept' : self.lookup_concept(concept_name),
            'encounter' : encounter_uuid,
            'obsDatetime' : self.get_encounter(encounter_uuid) ['encounterDatetime'],
            'person' : person_uuid,
            'value' : value,
        }

        if comment != None:
            content['comment'] = comment

        return self._do_post_json('/v1/obs', content) ['uuid']


    # Create an observation that contains a file attachment. The
    # observation is associated with the encounter whose UUID is
    # provided as argument, and maps one concept (specified by its
    # name) to a file whose binary content is "data". The display name
    # of the attachment is given by "title". In the OpenMRS Reference
    # application, the concept is typically "Attachment Upload" for
    # "Attachment Upload" encounters. The method returns the UUID of
    # the newly created observation.
    def create_observation_attachment(self, encounter_uuid, concept_name, title, data,
                                      filename = 'upload'):
        patient_uuid = self.get_encounter(encounter_uuid) ['patient']['uuid']
        person_uuid = self.get_patient(patient_uuid) ['person']['uuid']

        metadata = {
            'comment' : title,
            'concept' : self.lookup_concept(concept_name),
            'encounter' : encounter_uuid,
            'obsDatetime' : self.get_encounter(encounter_uuid) ['encounterDatetime'],
            'person' : person_uuid,
        }

        # https://talk.openmrs.org/t/create-complex-obs-with-rest-api-solved/22870/11
        parts = {
            'json' : (None, json.dumps(metadata)),
            'file': (filename, base64.b64encode(data).decode('ascii')),
        }

        r = requests.post('%s/v1/obs' % self.url, files=parts, auth = self.auth)
        r.raise_for_status()
        return r.json()


    # Explicitly ask OpenMRS to rebuild its search indexes. This is for advanced uses.
    def update_indexes(self):
        r = requests.post('%s/v1/searchindexupdate' % self.url, '', auth = self.auth)
        r.raise_for_status()
