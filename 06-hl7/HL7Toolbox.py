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


import datetime
import hl7
import threading

_threadLock = threading.Lock()
_messageIdSequence = 0


# This function parses a string or an array of bytes using the
# "python-hl7" library. This function implements some normalization of
# the newline characters, which is useful to enhance the flexibility
# of "python-hl7".
def parse_message(data):
    if isinstance(data, bytes):
        # First convert to a standard "str" object, assuming UTF-8
        # encoding. More advanced implementations would take the
        # MSH-18 field into consideration to select the proper encoding.
        data = data.decode('UTF-8')

    # The python-hl7 library expects newlines to separated by '\r'
    # characters, so we first normalize the data
    data = data.replace('\r\n', '\n')  # Compatibility with DOS line endings
    data = data.replace('\n', '\r')
    
    return hl7.parse(data)


# This function generates a sequence of message identifiers, to be
# used when creating a new HL7 message. Such identifiers can notably
# be written to the MSH-10 (message control ID) field of the MSH
# segment. Note that the implementation is thread-safe by the use of a
# mutex.
def generate_message_id():
    global _messageIdSequence
    global _threadLock
    with _threadLock:
        _messageIdSequence += 1
        return 'LINFO2381_MSG_ID_%d' % _messageIdSequence


# Return the current "datetime".
def get_now():
    return datetime.datetime.utcnow()


# Format a "datetime" Python class so it can be used in HL7 fields
# with a "DTM" (Date/Time) data type.
def format_date_time(date_time):
    return datetime.datetime.strftime(date_time, '%Y%m%d%H%M%S')


# Format the current Date/Time for use in HL7 messages.
def format_now():
    return format_date_time(get_now())


# Convert a HL7 field of "DTM" (Date/Time) data type to a "datetime"
# Python class.
def parse_date_time(hl7_date_time):
    if not isinstance(hl7_date_time, str):
        hl7_date_time = str(hl7_date_time)

    if len(hl7_date_time) == 8:
        return datetime.datetime.strptime(hl7_date_time, '%Y%m%d')
    if len(hl7_date_time) == 12:
        return datetime.datetime.strptime(hl7_date_time, '%Y%m%d%H%M')
    elif len(hl7_date_time) == 14:
        return datetime.datetime.strptime(hl7_date_time, '%Y%m%d%H%M%S')
    else:
        raise Exception('Unsupported date time format: %s' % hl7_date_time)
