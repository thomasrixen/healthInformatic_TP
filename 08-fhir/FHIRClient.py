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


import requests
import requests.auth


# Class that represents a connection to some FHIR server.
class FHIRClient:

    # Constructor for the FHIR connection: An URL, an username, and a
    # password are expected. It defaults to the base URL of the FHIR
    # API an OpenMRS server running on the localhost.
    def __init__(self,
                 url = 'http://localhost:8003/openmrs/ws/fhir2/R4',
                 username = 'admin',
                 password = 'Admin123'):
        # Make sure that the URL does not end with a slash
        if url.endswith('/'):
            self.url = url[0 : len(url) - 1]
        else:
            self.url = url

        self.auth = requests.auth.HTTPBasicAuth(username, password)


    # Return one FHIR Resource, given its type (typically "Patient",
    # "Encounter", or "Observation") and its FHIR identifier. This is
    # an invokation of a FHIR "Instance service".
    def get_resource(self, resource_type, resource_identifier):
        r = requests.get('%s/%s/%s' % (self.url, resource_type, resource_identifier), auth = self.auth)
        r.raise_for_status()
        return r.json()


    # List all the FHIR Resources of a given type that are stored in
    # the FHIR server. The "criteria" parameters can be used to
    # provide search criteria. This method implements paging. This is
    # an invokation of a FHIR "Type service".
    def list_resources(self, resource_type, criteria = {}, max_results = 20):
        result = []

        next_url = '%s/%s' % (self.url, resource_type)
        next_criteria = criteria

        while True:
            r = requests.get(next_url, params = next_criteria, auth = self.auth)
            r.raise_for_status()

            for entry in r.json().get('entry', []):
                result.append(entry['resource'])
                if (max_results != 0 and
                    len(result) >= max_results):
                    return result

            n = list(filter(lambda x: x['relation'] == 'next', r.json() ['link']))
            if len(n) == 0:
                return result  # We are done
            elif len(n) == 1:
                next_url = n[0]['url']  # Where to query the rest of the search set
                next_criteria = {}
            else:
                assert(False)  # Should never happen


    # Upload a new FHIR Resource onto the remote FHIR server. This is
    # an invokation of a FHIR "Type service". The method returns a
    # completed version of the FHIR Resource, which notably includes
    # the "id" field containing the FHIR identifier of the uploaded
    # Resource.
    def upload_resource(self, content):
        if not 'resourceType' in content:
            raise Exception('Missing field "resourceType" in FHIR Resource')

        r = requests.post('%s/%s' % (self.url, content['resourceType']),
                          json = content, auth = self.auth)
        r.raise_for_status()
        return r.json()
