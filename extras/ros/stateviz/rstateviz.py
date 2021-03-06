#!/usr/bin/env python
'''
rstateviz.py: ROS rviz script for visualizing quadcopter state in 3D space

Copyright (C) 2018 Simon D. Levy

Adapted from 

  https://github.com/ros-visualization/visualization_tutorials/blob/indigo-devel/interactive_marker_tutorials/scripts/basic_controls.py

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

NODE_NAME = 'stateviz'

MARKER_COLOR    = 1.0, 0.0, 0.0
MARKER_RESOURCE = 'package://stateviz/arrowhead.stl'
MARKER_START    = 0.08, 0.08, 0.
MARKER_SCALE    = .02

import rospy
from interactive_markers.interactive_marker_server import InteractiveMarkerServer, InteractiveMarker
from visualization_msgs.msg import Marker, InteractiveMarkerControl
from geometry_msgs.msg import Point
from tf.broadcaster import TransformBroadcaster
from tf.transformations import quaternion_from_euler

import numpy as np
import sys
import argparse
from threading import Thread
from time import sleep

br = None
euler = None
translat = None

def _errmsg(message):
    sys.stderr.write(message + '\n')
    sys.exit(1)

class _MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(1)

def normalizeQuaternion(orientation):

    norm = orientation.x**2 + orientation.y**2 + orientation.z**2 + orientation.w**2
    s = norm**(-0.5)
    orientation.x *= s
    orientation.y *= s
    orientation.z *= s
    orientation.w *= s

def frameCallback(msg):

    global br, euler, translat
    time = rospy.Time.now()

    rotation = quaternion_from_euler(*euler)

    br.sendTransform(translat, rotation, time, 'vehicle_frame', 'map')                
    
def processFeedback(feedback):

    server.applyChanges()

def handleFile(cmdargs):
    return

def handleBluetooth(cmdargs):
    return

def handleSerial(cmdargs):
    return

def handleRandomWalk(cmdargs):

    global euler, translat

    DELAY = .01
    LINEAR_SPEED = .5
    YAW_FACTOR = .06
    CLIMB_FACTOR = .005

    x,y,z = 0,0,0
    yaw = 0

    s = LINEAR_SPEED * DELAY

    while True:

        euler = (0, 0, yaw)

        x += s * np.cos(yaw)
        y += s * np.sin(yaw) 
        z += CLIMB_FACTOR * np.random.randn()
        translat = (x, y, z)

        yaw += YAW_FACTOR * np.random.randn()

        # Yield to main thread
        sleep(DELAY)
 
def threadFunc(cmdargs):

    if not cmdargs.filename is None:
        handleFile(cmdargs)

    elif not cmdargs.bluetooth is None:
        handleBluetooth(cmdargs) 

    elif not cmdargs.serial is None:
        handleSerial(cmdargs)

    elif not cmdargs.randseed is None:
        np.random.seed(int(cmdargs.randseed))

    handleRandomWalk(cmdargs) 
    
if __name__=='__main__':

    parser = _MyArgumentParser(description='Visualize incoming vehicle-state messages.' +
            'If no options provided, do a random walk.')

    parser.add_argument('-f', '--filename',    help='read state data from file')
    parser.add_argument('-b', '--bluetooth',   help='read state data from Bluetooth device')
    parser.add_argument('-s', '--serial',      help='read state data from serial port')
    parser.add_argument('-r', '--randseed',    help='seed the random number generator')

    cmdargs = parser.parse_args()

    thread = Thread(target=threadFunc, args = (cmdargs,))
    thread.daemon = True
    thread.start()

    rospy.init_node(NODE_NAME)
    br = TransformBroadcaster()
    rospy.Timer(rospy.Duration(0.01), frameCallback)
    server = InteractiveMarkerServer(NODE_NAME)

    vehicleMarker = InteractiveMarker()
    vehicleMarker.header.frame_id = 'vehicle_frame'
    vehicleMarker.pose.position = Point(*MARKER_START)
    vehicleMarker.scale = 1
    vehicleMarker.name = 'quadcopter'
    q = quaternion_from_euler(0, 0, 0)
    vehicleMarker.pose.orientation.x = q[0]
    vehicleMarker.pose.orientation.y = q[1]
    vehicleMarker.pose.orientation.z = q[2] 
    vehicleMarker.pose.orientation.w = q[3]
    normalizeQuaternion(vehicleMarker.pose.orientation)

    vehicleMesh = Marker()
    vehicleMesh.type = Marker.MESH_RESOURCE
    vehicleMesh.mesh_resource = MARKER_RESOURCE
    vehicleMesh.scale.x, vehicleMesh.scale.y, vehicleMesh.scale.z = (tuple([vehicleMarker.scale*MARKER_SCALE]))*3
    vehicleMesh.color.r, vehicleMesh.color.g, vehicleMesh.color.b = MARKER_COLOR
    vehicleMesh.color.a = 1.0

    vehicleControl =  InteractiveMarkerControl()
    vehicleControl.always_visible = True
    vehicleControl.markers.append(vehicleMesh)

    vehicleMarker.controls.append(vehicleControl)

    server.insert(vehicleMarker, processFeedback)

    server.applyChanges()

    rospy.spin()
