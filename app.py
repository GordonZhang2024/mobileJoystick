#!/usr/bin/env python3

"""
MobileJoystick | mobile FG controller
Copyright (C) 2025 Gordon Zhang

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from flask import Flask, render_template
from flask_cors import CORS
from flightgear_python.fg_if import CtrlsConnection
from socket import gethostbyname, gethostname
from time import sleep

DEBUG = True

app = Flask(__name__)
CORS(app)

neutralOrientation = (0, 0, 0) # First init it to disable some warnings
currentOrientation = (0, 0, 0)


"""
first Data: used by function data()
first group of orientation data will be set as neutral position
"""
firstData = True

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data/<a>/<b>/<g>')   # Motion data Alpha Beta Gamma
def data(a, b, g):
    global firstData, neutralOrientation, currentOrientation
    a, b, g = float(a), float(b), float(g)
    if firstData:
        neutralOrientation = [a, b, g]
        print('FD')
        firstData = False
    currentOrientation = [a, b, g]
    global ctrlsEventPipe

    controls = []
    for i in range(3):  # Process all three axes
        difference = currentOrientation[i] - neutralOrientation[i]

        # Normalize the difference to the range of -180 to 180 degrees
        difference = (difference + 180) % 360 - 180

        if -90 <= difference <= 90:
            controlValue = difference / 90.0  # Scale to -1 to 1
        else:
            # Clamp to -1 or 1 if outside ±90 degrees
            controlValue = -1 if difference < -90 else 1

        controls.append(controlValue)

    print(controls)
    ctrlsEventPipe.parent_send(controls)
    return ' '



def ctrlSend(ctrlsData, eventPipe):
    if eventPipe.child_poll():
        ctrl = eventPipe.child_recv()
    else:
        ctrl = (0, 0, 0)

    print()
    print(neutralOrientation)
    print(ctrl)
    print(ctrl[0])
    print()
    ctrlsData.aileron  = ctrl[0]
    ctrlsData.elevator = ctrl[1]
    ctrlsData.rudder   = ctrl[2]

    return ctrlsData

if __name__ == '__main__':
    ctrlsConn = CtrlsConnection()
    ctrlsEventPipe = ctrlsConn.connect_rx('localhost', 5503, ctrlSend)
    ctrlsConn.connect_tx('localhost', 5504)
    ctrlsConn.start()

    app.run('0.0.0.0', 5000, debug=True)

