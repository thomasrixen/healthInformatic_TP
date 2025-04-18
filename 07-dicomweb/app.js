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


var instances = [];


function LookupStudies() {
  axios.post('/lookup-studies', {
    'patient-id' : document.getElementById('patient-id').value,
    'patient-name' : document.getElementById('patient-name').value,
    'study-description' : document.getElementById('study-description').value
  }).then(function(response) {
    $('#studies').empty();
    $('#series').empty();
    instances = [];
    
    for (var i = 0; i < response.data.length; i++) {
      var study = response.data[i];
      var value = study['study-instance-uid'];
      var text = study['patient-id'] + ' - ' + study['patient-name'] + ' - ' + study['study-description'];
      $('#studies').append($('<option>', { value : value, text : text }));
    }

    LookupSeries();
  });
}


function LookupSeries() {
  var studyInstanceUID = $('#studies').val();

  if (studyInstanceUID !== null) {
    axios.post('/lookup-series', {
      'study-instance-uid' : studyInstanceUID
    }).then(function(response) {
      $('#series').empty();
      instances = [];
    
      for (var i = 0; i < response.data.length; i++) {
        var series = response.data[i];

        // Ignore the modalities that cannot be rendered as a PNG image
        if (series['modality'] != 'RTDOSE' &&
            series['modality'] != 'RTSTRUCT') {
          var value = series['series-instance-uid'];
          var text = series['modality'] + ' - ' + series['series-description'];
          $('#series').append($('<option>', { value : value, text : text }));
        }
      }

      LookupInstances();
    });
  }
}

function LookupInstances() {
  var studyInstanceUID = $('#studies').val();
  var seriesInstanceUID = $('#series').val();

  if (studyInstanceUID !== null &&
      seriesInstanceUID !== null) {
    axios.post('/lookup-instances', {
      'study-instance-uid' : studyInstanceUID,
      'series-instance-uid' : seriesInstanceUID
    }, {
    }).then(function(response) {
      instances = response.data;
      var currentInstance = Math.floor(instances.length / 2);

      document.getElementById('instances').max = instances.length - 1;
      document.getElementById('instances').value = currentInstance;
      
      UpdateCurrentInstance();
    });
  }
}


function UpdateCurrentInstance() {
  var currentInstance = document.getElementById('instances').value;
  
  if (currentInstance >= 0 &&
      currentInstance < instances.length) {
    axios.post('/render-instance', {
      'study-instance-uid' : $('#studies').val(),
      'series-instance-uid' : $('#series').val(),
      'sop-instance-uid' : instances[currentInstance],
    }, {
      responseType: 'arraybuffer'
    }).then(function(response) {
      var blob = new Blob([ response.data ], { type: 'image/png' });
      var urlCreator = window.URL || window.webkitURL;
      var dicomImage = document.getElementById('dicom');
      dicomImage.src = urlCreator.createObjectURL(blob);
    });
  }
}


document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('lookup').addEventListener('click', function(event) {
    LookupStudies();
  });

  document.getElementById('studies').addEventListener('change', function(event) {
    LookupSeries();
  });

  document.getElementById('series').addEventListener('change', function(event) {
    LookupInstances();
  });

  document.getElementById('instances').addEventListener('change', function(event) {
    UpdateCurrentInstance();
  });

  const isFirefox = navigator.userAgent.toLowerCase().includes('firefox');
  const mouseWheelEvent = isFirefox ? 'DOMMouseScroll' : 'mousewheel';

  document.getElementById('dicom').addEventListener(mouseWheelEvent, function(event) {
    var deltaY = isFirefox ? event.detail : event.deltaY;
    var currentInstance = parseInt(document.getElementById('instances').value, 10);

    if (deltaY < 0 &&
        currentInstance > 0) {
      document.getElementById('instances').value = currentInstance - 1;
      console.log(currentInstance);
      UpdateCurrentInstance();
    }
    else if (deltaY > 0 &&
             currentInstance + 1 < instances.length) {
      document.getElementById('instances').value = currentInstance + 1;
      UpdateCurrentInstance();
    }
  });
});
