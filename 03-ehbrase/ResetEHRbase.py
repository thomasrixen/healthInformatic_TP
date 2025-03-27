#!/usr/bin/python3

# Copyright (c) 2024, Sebastien Jodogne, ICTEAM UCLouvain, Belgium
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


import OpenEHRClient

import argparse

parser = argparse.ArgumentParser(description = 'Reset an EHRbase server')

parser.add_argument('--url', 
                    default = 'http://localhost:8001/ehrbase/rest',
                    help = 'Address of the REST API of EHRbase')
parser.add_argument('--username',
                    default = 'ehrbase-admin',
                    help = 'Username to the REST API')
parser.add_argument('--password',
                    default = 'EvenMoreSecretPassword',
                    help = 'Password to the REST API')

args = parser.parse_args()

client = OpenEHRClient.OpenEHRClient(url = args.url,
                                     username = args.username,
                                     password = args.password)

client.reset()
