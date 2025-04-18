/**
 * Copyright (c) 2024-2025, Sebastien Jodogne, ICTEAM UCLouvain, Belgium
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 **/


var countMessages = 0;


function formatNow() {
  var s = new Date().toISOString();
  // From "2025-04-01T18:51:34.733Z" to "20250401185134"
  return s.substr(0, 4) + s.substr(5, 2) + s.substr(8, 2) + s.substr(11, 2) + s.substr(14, 2) + s.substr(17, 2);
}


function createMSH(type) {
  countMessages += 1;
  return ('MSH|^~\&|LINFO2381|JavaScript|STUDENT|Python|' + formatNow() + '||' + type + '|MSG_ID_' + countMessages + '|P|2.1\r');
}


$('#find-patient-button').click(function() {
  axios.get('find-patient', {
    'params' : {
      'custom-id': $('#find-patient-custom-id').val()
    }
  }).catch(function() {
    alert('Unknown patient');
  }).then(function(response) {
    var url = ('http://localhost:8003/openmrs/coreapps/patientdashboard/patientDashboard.page?patientId=' +
               response.data['patient-uuid'] + '&visitId=' + response.data['visit-uuid']);
    window.open(url, '_blank').focus();
  });
});


$('#create-patient-button').click(function() {
  var birthDate = $('#create-patient-birth-date').val();
  // From "2020-03-02" to "20200302"
  birthDate = birthDate.substr(0, 4) + birthDate.substr(5, 2) + birthDate.substr(8, 2);

  var gender = $('input[name="create-patient-gender"]:checked').val();

  var now = formatNow();
  hl7 = (createMSH('ADT^A04') +
         'EVN|A04|' + now + '\r' +
         'PID|1||' + $('#create-patient-custom-id').val() + '^||' + $('#create-patient-family-name').val() +
         '^' + $('#create-patient-given-name').val() + '||' + birthDate + '|' + gender + '\r' +
         'PV1|1|||||||||||||||||||||||||||||||||||||||||||' + now + '\r');

  axios.post('hl7', hl7, {
    headers: {
      'Content-Type': 'text/hl7v2'
    }
  }).catch(function() {
    alert('Cannot handle HL7 message');
  }).then(function(response) {
    $('#find-patient-custom-id').val($('#create-patient-custom-id').val());
    $('#record-note-custom-id').val($('#create-patient-custom-id').val());
    $('#record-vitals-custom-id').val($('#create-patient-custom-id').val());
  });
});


$('#record-note-button').click(function() {
  var now = formatNow();
  hl7 = (createMSH('ORU^R01') +
         'PID|1||' + $('#record-note-custom-id').val() + '^\r' +
         'ORC|\r' +
         'OBR|1|||Visit Note|||' + now + '\r' +
         'OBX|1|TX|11488-4^Consult note||' + $('#record-note-content').val() + '\r');

  axios.post('hl7', hl7, {
    headers: {
      'Content-Type': 'text/hl7v2'
    }
  }).catch(function() {
    alert('Cannot handle HL7 message');
  });
});


$('#record-vitals-button').click(function() {
  var temperature = $('#record-vitals-temperature').val();
  var weight = $('#record-vitals-weight').val();

  if (temperature.length == 0 &&
      weight.length == 0) {
    alert('Temperature and weight cannot be both empty');
  }

  var now = formatNow();
  hl7 = (createMSH('ORU^R01') +
         'PID|1||' + $('#record-note-custom-id').val() + '^\r' +
         'ORC|\r' +
         'OBR|1|||Vitals|||' + now + '\r');

  var count = 1;

  if (temperature.length != 0) {
    hl7 += 'OBX|' + count + '|NM|8310-5^||' + temperature + '\r';
    count += 1;
  }

  if (weight.length != 0) {
    hl7 += 'OBX|' + count + '|NM|3141-9^||' + weight + '\r';
    count += 1;
  }

  axios.post('hl7', hl7, {
    headers: {
      'Content-Type': 'text/hl7v2'
    }
  }).catch(function() {
    alert('Cannot handle HL7 message');
  });
});
