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


global previousCtrl
previousCtrl = [0, 0, 0]


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
    global previousCtrl



    aileron = 0
    elevator = 0

    differenceA = -(currentOrientation[0] - neutralOrientation[0])
    # differenceB = -(currentOrientation[1] - neutralOrientation[1])
    differenceG = (currentOrientation[2] - neutralOrientation[2])

    # Normalize the difference to the range of -180 to 180 degrees
    differenceA = (differenceA + 180) % 360 - 180
    # differenceB = (differenceB + 180) % 360 - 180
    differenceG = (differenceG + 180) % 360 - 180

    if -90 <= differenceA <= 90:
        aileron = differenceA / 90.0  # Scale to -1 to 1
    else:
        # Clamp to -1 or 1 if outside ±90 degrees
        aileron = -1 if differenceA < -90 else 1


    if -60 <= differenceG <= 60:
        elevator = differenceG / 60.0  # Scale to -1 to 1
    else:
        # Clamp to -1 or 1 if outside ±60 degrees
        elevator = -1 if differenceG < -60 else 1



    # rudder = differenceB



    print(aileron)


    control = [aileron, 0, elevator]
    ctrlsEventPipe.parent_send(control)
    previousCtrl = control
    return ' '



def ctrlSend(ctrlsData, eventPipe):
    global previousCtrl
    if eventPipe.child_poll():
        orientation = eventPipe.child_recv()
        previousCtrl = orientation
    else:
        orientation = previousCtrl
    ctrlsData.aileron = orientation[0]
    ctrlsData.elevator = orientation[2]
    # ctrlsData.rudder = orientation[2]

    return ctrlsData

if __name__ == '__main__':
    ctrlsConn = CtrlsConnection()
    ctrlsEventPipe = ctrlsConn.connect_rx('localhost', 5503, ctrlSend)
    ctrlsConn.connect_tx('localhost', 5504)
    ctrlsConn.start()

    app.run('0.0.0.0', 5000, debug=True)

