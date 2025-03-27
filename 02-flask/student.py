#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import flask
app = flask.Flask(__name__)

@app.route('/')
def redirection():
    return flask.redirect('index.html', code = 302)

@app.route('/index.html')
def get_index():
    with open('index.html', 'r') as f:
        return flask.Response(f.read(), mimetype = 'text/html')

@app.route('/app.js')
def get_javascript():
    with open('app.js', 'r') as f:
        return flask.Response(f.read(), mimetype = 'text/javascript')


@app.route('/convert-celsius', methods = ['POST'])
def convert_celsius():
    # This route takes as argument a POST request to the REST API,
    # whose body contains a JSON object formatted as follows:
    #
    #   {
    #      "celsius": 20
    #   }
    #
    # The route must convert the degrees Celsius both to degrees
    # Fahrenheit and to Kelvins, and must send its response with a
    # body that contains a JSON object formatted as follows:
    #
    #   {
    #      "fahrenheit": 68.0,
    #      "kelvin": 293.15
    #   }
    #
    # All the values in the request must be floating-point numbers. An
    # "400 Bad Request" HTTP status must be returned in the case of a
    # badly formatted request.
    #
    # Sample command-line session using the "curl" tool:
    #
    #   $ curl http://localhost:5000/convert-celsius -H 'Content-Type: application/json' -d '{"celsius":41}'
    #   {
    #     "fahrenheit": 105.8,
    #     "kelvin": 314.15
    #   }

    ##############################################
    # TODO
    ##############################################

    data = flask.request.get_json()
    if not data:
        return flask.Response('Bad Request\n', 400)
    if 'celsius' not in data:
        return flask.Response('Bad Request\n', 400)
    if not isinstance(data['celsius'], (int, float)):
        return flask.Response('Bad Request\n', 400)
    
    celsius = float(data['celsius'])

    fahrenheit = celsius * 9/5 + 32
    kelvin = celsius + 273.15

    return flask.jsonify({
        "fahrenheit": fahrenheit,
        "kelvin": kelvin
        })


@app.route('/compute-electricity', methods = ['POST'])
def compute_electricity():
    # This route takes as argument a POST request to the REST API,
    # whose body contains a JSON object (dictionary) containing
    # exactly two among the following fields: "voltage", "resistance",
    # "current", and "power". Here is such a valid body:
    #
    #   {
    #      "current": 6,
    #      "resistance": 5
    #   }
    #
    # The route must compute the two missing values using the "V=R*I"
    # (Ohm's law) and "P=I*V" (electric power dissipated in resistive
    # circuits), and must send these two missing values as a JSON
    # object. Here is the body of the response for the example above:
    #
    #   {
    #      "power": 180,
    #      "voltage": 30
    #   }
    #
    # All the values in the request must be floating-point numbers. An
    # "400 Bad Request" HTTP status must be returned in the case of a
    # badly formatted request (not floating-point numbers, or number
    # of fields not equal to 2).
    #
    # Sample command-line session using the "curl" tool:
    #
    #   $ curl http://localhost:5000/compute-electricity -H 'Content-Type: application/json' -d '{"power":50,"voltage":40}'
    #   {
    #     "current": 1.25,
    #     "resistance": 32
    #   }


    ##############################################
    # TODO
    ##############################################

    data = flask.request.get_json()

    # Validate the request format
    if not data or len(data) != 2:
        return flask.jsonify({"error": "Request must contain exactly two numeric fields."}), 400

    try:
        # Extract the provided values
        known_values = {key: float(value) for key, value in data.items() if isinstance(value, (int, float))}
        if len(known_values) != 2:
            return flask.jsonify({"error": "Invalid input. Values must be numeric."}), 400
    except ValueError:
        return flask.jsonify({"error": "Invalid input. Ensure all values are numbers."}), 400

    # Extract values from known inputs
    voltage = known_values.get("voltage")
    resistance = known_values.get("resistance")
    current = known_values.get("current")
    power = known_values.get("power")

    # Compute missing values based on available inputs
    if voltage is not None and resistance is not None:
        current = voltage / resistance
        power = voltage * current

    elif voltage is not None and current is not None:
        resistance = voltage / current
        power = voltage * current

    elif voltage is not None and power is not None:
        current = power / voltage
        resistance = voltage / current

    elif resistance is not None and current is not None:
        voltage = resistance * current
        power = voltage * current

    elif resistance is not None and power is not None:
        current = (power / resistance) ** 0.5
        voltage = resistance * current

    elif current is not None and power is not None:
        voltage = power / current
        resistance = voltage / current

    else:
        return flask.jsonify({"error": "Invalid combination of values."}), 400

    # Prepare the response with missing values
    computed_values = {
        "voltage": voltage,
        "resistance": resistance,
        "current": current,
        "power": power
    }

    # Return only the newly computed values (not the input values)
    response_data = {key: value for key, value in computed_values.items() if key not in known_values}

    return flask.jsonify(response_data)




if __name__ == '__main__':
    app.run(debug = True)
