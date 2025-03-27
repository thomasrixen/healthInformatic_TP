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

var chart = null;


function refreshTemperatures() {
  var select = document.getElementById('patient-select');
  var id = select.value;
  if (id === '') {
    console.log('No patient');
    document.getElementById('temperature-div').style.visibility = 'hidden';
    return;
  }

  document.getElementById('temperature-div').style.visibility = 'visible';

  console.log(id);
  axios.post('list-temperatures', {
    'ehr-id' : id
  })
    .then(function(response) {
      var x = [];
      var y = [];
      for (var i = 0; i < response.data.length; i++) {
        x.push(response.data[i]['time']);
        y.push(response.data[i]['temperature']);
      }
      chart.data.labels = x;
      chart.data.datasets[0].data = y;
      chart.update();
    })
    .catch(function(response) {
      alert('Resource /temperatures not properly implemented in Flask');
    });
}


function refreshPatients() {
  axios.post('list-patients')
    .then(function(response) {
      var select = document.getElementById('patient-select');

      while (select.options.length > 0) {
        select.options.remove(0);
      }

      for (var i = 0; i < response.data.length; i++) {
        var id = response.data[i]['ehr-id'];
        var name = response.data[i]['patient-name'];
        select.appendChild(new Option(name, id));
      }
      refreshTemperatures();
    })
    .catch(function(response) {
      alert('Resource /list-patients not properly implemented in Flask');
    });
}


document.addEventListener('DOMContentLoaded', function() {
  chart = new Chart(document.getElementById('temperatures'), {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Temperature',
        data: [],
        fill: false
      }]
    },
    options: {
      animation: {
        duration: 0  // Disable animations
      },
      scales: {
        x: {
          ticks: {
            // Rotate the X label
            maxRotation: 45,
            minRotation: 45
          }
        }
      }
    }
  });

  refreshPatients();

  document.getElementById('patient-select').addEventListener('change', refreshTemperatures);

  document.getElementById('patient-button').addEventListener('click', function() {
    var name = document.getElementById('patient-input').value;
    if (name == '') {
      alert('No name was provided');
    } else {
      axios.post('create-patient', {
        'patient-name': name
      })
        .then(function(response) {
          document.getElementById('patient-input').value = '';
          refreshPatients();
        })
        .catch(function(response) {
          alert('Resource /create-patient not properly implemented in Flask');
        });
    }
  });

  document.getElementById('temperature-button').addEventListener('click', function() {
    var temperature = parseFloat(document.getElementById('temperature-input').value);
    if (isNaN(temperature)) {
      alert('Not a valid number');
    } else {
      axios.post('record-temperature', {
        'ehr-id': document.getElementById('patient-select').value,
        'temperature': temperature,
        'time': new Date().toISOString()
      })
        .then(function(response) {
          document.getElementById('temperature-input').value = '';
          refreshTemperatures();
        })
        .catch(function(response) {
          alert('Resource /record-temperature not properly implemented in Flask');
        });
    }
  });
});
