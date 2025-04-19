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


var selectedPatientUUID = null;
var selectedVisitUUID = null;

$('#selected-patient-open-visit').click(function() {
  var url = 'http://localhost:8003/openmrs/coreapps/patientdashboard/patientDashboard.page?patientId=' + selectedPatientUUID + '&visitId=' + selectedVisitUUID;
  window.open(url, '_blank').focus();
});


function refreshPatient(uuid) {
  axios.get('notes', {
    'params' : {
      'patient-uuid' : uuid
    }
  }).catch(function() {
    alert('Error while reading notes for patient');
  }).then(function(response) {
    var patient = response.data['patient'];
    $('#selected-patient').show();
    $('#selected-patient-id').text(patient['id']);
    $('#selected-patient-name').text(patient['name']);
    $('#selected-patient-gender').text(patient['gender']);
    $('#selected-patient-birth-date').text(patient['birth-date']);

    $('#new-note').val('');
    
    var target = $('#clinical-notes');
    target.empty();
    
    var notes = response.data['notes'];
    for (var i = 0; i < notes.length; i++) {
      target.append($('<tr>')
                    .append($('<td>').text(notes[i]['time']))
                    .append($('<td>').text(notes[i]['text'])));
    }

    selectedPatientUUID = uuid;
    selectedVisitUUID = patient['visit-uuid'];
  });
}


$('#create-button').click(function() {
  var givenName = $('#patient-given-name').val();
  var familyName = $('#patient-family-name').val();
  var gender = $('input[name="patient-gender"]:checked').val();

  /**
   * Note: The displayed date format will differ from the actual
   * value: The displayed date is formatted based on the locale of the
   * user's browser, but the parsed value is always formatted
   * yyyy-mm-dd. https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/date
   **/
  var birthDate = $('#patient-birth-date').val();

  if (givenName.length < 2) {
    alert('Given name must have at least 2 characters');
  } else if (familyName.length < 2) {
    alert('Family name must have at least 2 characters');
  } else if (gender != 'F' && gender != 'M' && gender != 'X') {
    alert('Error in the gender');
  } else if (birthDate.length != 10) {
    alert('Error in the birth date');
  } else {
    axios.post('create-patient', {
      'given-name': givenName,
      'family-name': familyName,
      'gender': gender,
      'birth-date': birthDate,
    }).catch(function() {
      alert('Cannot create patient');
    }).then(function(response) {
      refreshPatient(response.data['patient-uuid']);
    });
  }
});


$('#search-button').click(function() {
  var query = $('#search-criteria').val();
  if (query.length < 2) {
    alert('Search criteria must have at least 2 characters');
  } else {    
    axios.post('find-patients', {
      query: query
    }).catch(function() {
      alert('Cannot search patients');
    }).then(function(response) {
      var target = $('#search-results');
      target.empty();

      // Don't use a "for" loop here, as the "value" must be used in callbacks
      $.each(response.data, function(key, value) {
        var row = $('<tr>');
        row.append($('<td>').text(value['patient-id']));
        row.append($('<td>').text(value['name']));
        row.append($('<td>').text(value['gender']));
        row.append($('<td>').text(value['age']));
        row.append($('<td>').text(value['birth-date']));

        var buttonSelect = $('<button>').text('Select');
        buttonSelect.click(function() {
          refreshPatient(value['patient-uuid']);
        });

        var buttonOpenMRS = $('<button>').text('Open in OpenMRS');
        buttonOpenMRS.click(function() {
          var url = 'http://localhost:8003/openmrs/coreapps/clinicianfacing/patient.page?patientId=' + value['patient-uuid'];
          window.open(url, '_blank').focus();
        });

        row.append($('<td>').append(buttonSelect).append(buttonOpenMRS));
        target.append(row);
      });
    });
  }
});


$('#record-note').click(function() {
  axios.post('record-note', {
    'patient-uuid' : selectedPatientUUID,
    'text' : $('#new-note').val()
  }).catch(function() {
    alert('Cannot record new note');
  }).then(function(response) {
    refreshPatient(selectedPatientUUID);
  });
});
