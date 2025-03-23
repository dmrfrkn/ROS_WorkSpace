#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy 
from std_msgs.msg import Float64MultiArray

def waypoint_command():
    pub = rospy.Publisher('waypoint_cmd',Float64MultiArray,queue_size=10)
    rospy.init_node('waypoint_publisher', anonymous=True)
    rate =rospy.Rate(1)
    while not rospy.is_shutdown():
        waypoint = Float64MultiArray
        waypoint.data= [37.7749, -122.4194, 20.0]
        rospy.loginfo(waypoint)
        pub.publish(waypoint)
        rate.sleep()
        
if __name__ == '__main__':
    try:
        waypoint_command
    except rospy.ROSInterruptException:
        pass
        