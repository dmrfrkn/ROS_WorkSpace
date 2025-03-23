#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
from dronekit import connect,VehicleMode,LocationGlobalRelative
import time
from std_msgs.msg import Float64MultiArray



rospy.init_node("dronekit_node",anonymous=True)
vehicle=connect("127.0.0.1:14550",wait_ready=True)

latitude = -35.359860
longitude = 149.161451
altitude = 800
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



        
        
    
    
    
    







