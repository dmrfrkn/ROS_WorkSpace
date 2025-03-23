#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
from std_msgs.msg import Float64MultiArray
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time


vehicle = connect('127.0.0.1:14550', wait_ready=True)

def goto_callback(data):
    latitude = data.data[0]
    longitude = data.data[1]
    altitude = data.data[2]
    print("Navigating to:", latitude, longitude, altitude)
    vehicle.mode = VehicleMode("GUIDED")
    while not vehicle.mode.name == 'GUIDED':
        print("Waiting for vehicle to enter GUIDED mode")
        time.sleep(1)
    
    vehicle.armed = True
    while not vehicle.armed:
        print("Waiting for arming...")
        time.sleep(1)
    
    target_location = LocationGlobalRelative(latitude, longitude, altitude)
    vehicle.simple_goto(target_location)

def listener():
    rospy.init_node('dronekit_listener', anonymous=True)
    rospy.Subscriber("waypoint_cmd", Float64MultiArray, goto_callback)
    #rospy.spin()

if __name__ == '__main__':
    listener()