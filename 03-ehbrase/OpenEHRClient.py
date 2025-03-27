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
import enum
import json
import requests
import requests.auth


# Enumeration that encodes the various file formats supported by the
# openEHR REST API
class CompositionFormat(enum.Enum):
    CANONICAL_JSON = 1
    SIMPLIFIED_JSON_FLAT = 2
    SIMPLIFIED_JSON_STRUCTURED = 3


# Class that represents a connection to some openEHR CDR (clinical
# data repository), including EHRbase
class OpenEHRClient:

    # Constructor for the connection: An URL, an username, and a
    # password are expected. The default values correspond to the
    # parameters in our "docker-compose.yml" configuration.
    def __init__(self,
                 url = 'http://localhost:8080/ehrbase/rest',
                 username = 'ehrbase-user',
                 password = 'SuperSecretPassword'):
        # Make sure that the URL does not end with a slash
        if url.endswith('/'):
            self.url = url[0 : len(url) - 1]
        else:
            self.url = url

        self.username = username
        self.password = password

    def _getAuthentication(self):
        return requests.auth.HTTPBasicAuth(self.username, self.password)

    def _getIdentifier(self, response):
        etag = response.headers.get('ETag')
        if (etag == None or
            len(etag) == 0):
            raise Exception('No ETag')

        if (etag[0] == '"' and
            etag[-1] == '"'):
            # Remove the surrounding quotes
            return etag[1 : len(etag) - 1]
        else:
            return etag


    # List all the templates that are defined in the openEHR CDR
    def listTemplates(self):
        r = requests.get('%s/openehr/v1/definition/template/adl1.4' % self.url,
                         auth = self._getAuthentication(),
                         headers = {
                             'Accept' : 'application/json',
                         })

        r.raise_for_status()

        return list(map(lambda x: x['template_id'], r.json()))


    # Define a new template in the openEHR CDR. The path must
    # correspond to a template definition produced by the Archetype
    # Designer tool (https://tools.openehr.org/designer/). The method
    # returns the identifier of the newly created template.
    def addTemplate(self, path):
        # NB: The 'r' flag for open() does not work on Microsoft
        # Windows, it is mandatory to use 'rb'
        with open(path, 'rb') as f:
            r = requests.post('%s/openehr/v1/definition/template/adl1.4' % self.url,
                              data = f.read(),
                              auth = self._getAuthentication(),
                              headers = {
                                  'Content-Type' : 'application/xml',
                              })

            if r.status_code != 204:
                raise Exception('Cannot add template')
            else:
                return self._getIdentifier(r)


    # Return the definition of a template. This method is notably
    # useful to find the AQL path associated with a field in an
    # openEHR composition.
    def getTemplate(self, templateId):
        r = requests.get('%s/ecis/v1/template/%s' % (self.url, templateId),
                         auth = self._getAuthentication(),
                         headers = {
                             'Accept' : 'application/json',
                         })

        r.raise_for_status()
        return r.json()


    # Return a sample composition for the given template. The file
    # format for the composition can be specified.
    def getSampleComposition(self, templateId, format = CompositionFormat.SIMPLIFIED_JSON_FLAT):
        if format == CompositionFormat.CANONICAL_JSON:
            url = '%s/openehr/v1/definition/template/adl1.4/%s/example' % (self.url, templateId)
        elif format == CompositionFormat.SIMPLIFIED_JSON_FLAT:
            url = '%s/ecis/v1/template/%s/example?format=FLAT' % (self.url, templateId)
        elif format == CompositionFormat.SIMPLIFIED_JSON_STRUCTURED:
            url = '%s/ecis/v1/template/%s/example?format=STRUCTURED' % (self.url, templateId)
        else:
            raise Exception('Enumeration out of range')

        r = requests.get(url,
                         auth = self._getAuthentication(),
                         headers = {
                             'Accept' : 'application/json',
                         })

        r.raise_for_status()
        return r.json()


    # Create a new EHR in the openEHR CDR, and return the identifier
    # of the newly created EHR.
    def createEHR(self):
        r = requests.post('%s/openehr/v1/ehr' % self.url,
                          auth = self._getAuthentication(),
                          headers = {
                              'Content-Type' : 'application/json',
                          })

        if r.status_code != 204:
            raise Exception('Cannot create EHR')
        else:
            return self._getIdentifier(r)


    # Return full information about the EHR with given information.
    # This method is provided for completeness, and should not be used
    # in this course.
    def getEHR(self, ehrId):
        r = requests.get('%s/openehr/v1/ehr/%s' % (self.url, ehrId),
                         auth = self._getAuthentication(),
                         headers = {
                             'Accept' : 'application/json',
                         })

        r.raise_for_status()
        return r.json()


    # Execute a AQL query (Archetype Query Language). Parameters can
    # be provided for the query. The rows that match the query can be
    # found in the "rows" field of the returned object.
    def executeAQL(self, query, params = {}):
        r = requests.post('%s/openehr/v1/query/aql' % self.url,
                          auth = self._getAuthentication(),
                          data = json.dumps({
                              'q' : query,
                              'query_parameters' : params,
                          }),
                          headers = {
                              'Content-Type' : 'application/json',
                              'Accept' : 'application/json',
                          })

        r.raise_for_status()
        return r.json()


    # List the identifiers of all the EHRs that are stored in the
    # openEHR CDR.
    def listEHRs(self):
        aql = self.executeAQL('SELECT e/ehr_id/value FROM EHR e')
        return list(map(lambda x: x[0], aql ['rows']))


    # List the identifiers of all the compositions that are stored
    # inside the EHR whose identifier is provided in argument.
    def listCompositions(self, ehrId):
        aql = self.executeAQL('SELECT c/uid/value FROM EHR e CONTAINS COMPOSITION c WHERE e/ehr_id/value=$ehrId', {
            'ehrId' : ehrId,
        })
        return list(map(lambda x: x[0], aql ['rows']))


    # Return the content of one composition, given the identifier of
    # the composition and the identifier of its parent EHR. The
    # returned file format can possibly be fine-tuned.
    def getComposition(self, ehrId, compositionId, format = CompositionFormat.SIMPLIFIED_JSON_FLAT):
        if format == CompositionFormat.CANONICAL_JSON:
            url = '%s/openehr/v1/ehr/%s/composition/%s' % (self.url, ehrId, compositionId)
        elif format == CompositionFormat.SIMPLIFIED_JSON_FLAT:
            url = '%s/ecis/v1/composition/%s?format=FLAT' % (self.url, compositionId)
        elif format == CompositionFormat.SIMPLIFIED_JSON_STRUCTURED:
            url = '%s/ecis/v1/composition/%s?format=STRUCTURED' % (self.url, compositionId)
        else:
            raise Exception('Enumeration out of range')

        r = requests.get(url,
                         auth = self._getAuthentication(),
                         headers = {
                             'Accept' : 'application/json',
                         })

        r.raise_for_status()
        return r.json()


    # Add one composition to the parent EHR whose identifier is
    # provided as an argument. The caller must also specify the
    # identifier of the template to be used (which is needed for the
    # simplified formats), as well as the file format that is used to
    # define the composition.
    def addComposition(self, ehrId, templateId, composition, format = CompositionFormat.SIMPLIFIED_JSON_FLAT):
        if format == CompositionFormat.CANONICAL_JSON:
            url = '%s/openehr/v1/ehr/%s/composition' % (self.url, ehrId)
        elif format == CompositionFormat.SIMPLIFIED_JSON_FLAT:
            url = '%s/ecis/v1/composition?ehrId=%s&templateId=%s&format=FLAT' % (self.url, ehrId, templateId)
        elif format == CompositionFormat.SIMPLIFIED_JSON_STRUCTURED:
            url = '%s/ecis/v1/composition?ehrId=%s&templateId=%s&format=STRUCTURED' % (self.url, ehrId, templateId)
        else:
            raise Exception('Enumeration out of range')

        r = requests.post(url,
                          auth = self._getAuthentication(),
                          data = json.dumps(composition),
                          headers = {
                              'Content-Type' : 'application/json',
                              'Accept' : 'application/json',
                          })

        r.raise_for_status()

        if format == CompositionFormat.CANONICAL_JSON:
            return self._getIdentifier(r)
        else:
            return r.json() ['compositionUid']


    # Properly fill the content a field of type "MULTIMEDIA" in a
    # composition of type simplified structured JSON. This method is
    # for advanced use cases, and is not used in the course.
    def setMultimediaContentIntoStructured(self, field, content, mimeType):
        # Reference is the DV_MULTIMEDIA class:
        # https://specifications.openehr.org/releases/RM/latest/data_types.html#_dv_multimedia_class

        assert(len(field) == 1)

        field[0]['content'] = [
            {
                '|size' : len(content),
                '|data' : base64.b64encode(content).decode('ascii'),
                '|mediatype' : mimeType,
            }
        ]


    # Properly fill the content a field of type "MULTIMEDIA" in a
    # composition of type simplified flat JSON. This method is for
    # advanced use cases, and is not used in the course.
    def setMultimediaContentIntoFlat(self, composition, field, content, mimeType):
        if '%s/content' % field in composition:
            del composition['%s/content' % field]

        composition['%s/content|size' % field] = len(content)
        composition['%s/content|data' % field] = base64.b64encode(content).decode('ascii')
        composition['%s/content|mediatype' % field] = mimeType


    # Retrieve the content a field of type "MULTIMEDIA" in a
    # composition of type simplified structured JSON. This method is
    # for advanced use cases, and is not used in the course.
    def getMultimediaContentFromStructured(self, field):
        assert(len(field) == 1 and
               'content' in field[0] and
               len(field[0]['content']) == 1 and
               '|data' in field[0]['content'][0] and
               '|size' in field[0]['content'][0])

        data = field[0]['content'][0]['|data']
        size = field[0]['content'][0]['|size']
        content = base64.b64decode(data)
        assert(len(content) == size)
        return content


    # Retrieve the content a field of type "MULTIMEDIA" in a
    # composition of type simplified flat JSON. This method is for
    # advanced use cases, and is not used in the course.
    def getMultimediaContentFromFlat(self, composition, field):
        data = composition['composition']['%s/content|data' % field]
        size = composition['composition']['%s/content|size' % field]
        content = base64.b64decode(data)
        assert(len(content) == size)
        return content


    # Delete the given EHR from an EHRbase server. This function is
    # not available in the generic openEHR REST API (i.e., it is
    # specific to EHRbase). The connection also requires the
    # "ehrbase-admin" credentials, and EHRbase must have been started
    # with the "ADMINAPI_ACTIVE" environment variable set to "true".
    def deleteEHR(self, ehrId):
        r = requests.delete('%s/admin/ehr/%s' % (self.url, ehrId),
                            auth = self._getAuthentication())
        r.raise_for_status()


    # Delete the given template from an EHRbase server. This function
    # is not available in the generic openEHR REST API (i.e., it is
    # specific to EHRbase). The connection also requires the
    # "ehrbase-admin" credentials, and EHRbase must have been started
    # with the "ADMINAPI_ACTIVE" environment variable set to "true".
    def deleteTemplate(self, templateId):
        r = requests.delete('%s/admin/template/%s' % (self.url, templateId),
                            auth = self._getAuthentication())
        r.raise_for_status()


    # Remove all the EHR and all the templates stored in a EHRbase
    # server. This function is not available in the generic openEHR
    # REST API (i.e., it is specific to EHRbase). The connection also
    # requires the "ehrbase-admin" credentials, and EHRbase must have
    # been started with the "ADMINAPI_ACTIVE" environment variable set
    # to "true".
    def reset(self):
        for ehrId in self.listEHRs():
            self.deleteEHR(ehrId)

        for templateId in self.listTemplates():
            self.deleteTemplate(templateId)
