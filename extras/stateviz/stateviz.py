#!/usr/bin/env python3
'''
stateviz.py: State visualizer 

Dependencies: numpy, matplotlib, pyserial, pybluez, https://github.com/simondlevy/PyRoboViz

Copyright (C) 2018 Simon D. Levy

This file is part of Hackflight.

Hackflight is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as 
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.
This code is distributed in the hope that it will be useful,     
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License 
along with this code.  If not, see <http:#www.gnu.org/licenses/>.
'''

import msppg
import argparse
import sys
import time
import math
from roboviz import Visualizer

MAP_SIZE_PIXELS = 800
MAP_SIZE_METERS = 32

def _errmsg(message):
    sys.stderr.write(message + '\n')
    sys.exit(1)

class _MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(1)

_request = msppg.serialize_STATE_Request()

class _MyVisualizer(Visualizer):

    def __init__(self, cmdargs, label):

        zero_angle = float(cmdargs.zero_angle) if not cmdargs.zero_angle is None else 0

        Visualizer.__init__(self, MAP_SIZE_PIXELS, MAP_SIZE_METERS, label, True, zero_angle)

class _StateParser(msppg.Parser):

    def __init__(self, readfun, writefun, closefun, visualizer):

        msppg.Parser.__init__(self)

        self.readfun = readfun
        self.writefun = writefun
        self.closefun = closefun

        # Create a Visualizer object with trajectory
        self.viz = visualizer

    def handle_STATE(self, altitude, variometer, positionX, positionY, heading, velocityForward, velocityRightward):

        self.viz.display(0, 0, math.degrees(heading))

        self.writefun(_request)

    def begin(self):

        self.writefun(_request)

        while True:

                try:

                    self.parse(self.readfun(1))

                except KeyboardInterrupt:

                    self.closefun()
                    break

def _handle_file(cmdargs):

    DT_SEC    = .01

    # Create a Visualizer object with trajectory
    viz = _MyVisualizer(cmdargs, 'From file: ' + cmdargs.filename)

    for line in open(cmdargs.filename):

        state = (float(s) for s in line.split())

        if not viz.display(*state):
            exit(0)

        time.sleep(DT_SEC)

def _handle_bluetooth(cmdargs):

    try:
        import bluetooth
    except:
        _errmsg('import bluetooth failed; make sure pybluez is installed')

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((cmdargs.bluetooth, 1))

    viz = _MyVisualizer(cmdargs, 'From bluetooth: ' + cmdargs.bluetooth)

    parser = _StateParser(sock.recv, sock.send, sock.close, viz)

    parser.begin()

def _handle_serial(cmdargs):

    try:
        import serial
    except:
        _errmsg('import serial failed; make sure pyserial is installed')

    port = serial.Serial(cmdargs.serial, 115200)

    viz = _MyVisualizer(cmdargs, 'From serial: ' + cmdargs.serial)

    parser = _StateParser(port.read, port.write, port.close, viz)

    parser.begin()

if __name__ == '__main__':

    parser = _MyArgumentParser(description='Visualize incoming vehicle-state messages.')

    parser.add_argument('-f', '--filename',    help='read state data from file')
    parser.add_argument('-b', '--bluetooth',   help='read state data from Bluetooth device')
    parser.add_argument('-s', '--serial',      help='read state data from serial port')
    parser.add_argument('-z', '--zero_angle',  help='starting angle in degrees')

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    cmdargs = parser.parse_args()

    if not cmdargs.filename is None:
        _handle_file(cmdargs)

    if not cmdargs.bluetooth is None:
        _handle_bluetooth(cmdargs)
    
    if not cmdargs.serial is None:
        _handle_serial(cmdargs)
