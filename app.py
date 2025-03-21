#!/usr/bin/env python

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
    difference = currentOrientation[0] - neutralOrientation[0]
    
    # Normalize the difference to the range of -180 to 180 degrees
    difference = (difference + 180) % 360 - 180
    
    if -90 <= difference <= 90:
        control_value = difference / 90.0  # Scale to -1 to 1
    else:
        # Clamp to -1 or 1 if outside ±90 degrees
        control_value = -1 if difference < -90 else 1
    
    print(control_value)
    control = [control_value, 0, 0]
    ctrlsEventPipe.parent_send(control)
    return ' '



def ctrlSend(ctrlsData, eventPipe):
    if eventPipe.child_poll():
        orientation = eventPipe.child_recv()
    else:
        orientation = (0, 0, 0)

    print()
    print(neutralOrientation)
    print(orientation)
    print(orientation[0])
    print()
    ctrlsData.aileron = orientation[0]

    return ctrlsData

if __name__ == '__main__':
    ctrlsConn = CtrlsConnection()
    ctrlsEventPipe = ctrlsConn.connect_rx('localhost', 5503, ctrlSend)
    ctrlsConn.connect_tx('localhost', 5504)
    ctrlsConn.start()

    app.run('0.0.0.0', 5000, debug=True)

