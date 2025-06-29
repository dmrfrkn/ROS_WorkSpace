#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
from mavros_msgs.srv import CommandInt
from mavros_msgs.msg import AttitudeTarget
from geopy.distance import distance

def distance_calculator(plane_loc, target_loc):
    return distance(plane_loc, target_loc).meters

class ManevraNode:

    def __init__(self):
        rospy.init_node("manevra_gorev_node")

        # Hedef nokta (100m kala manevra yapılacak)
        self.target_lat = -35.362000
        self.target_lon = 149.163500
        self.target_lat_srv = -353620000
        self.target_lon_srv = 1491635000
        self.target_list = [self.target_lat, self.target_lon]

        self.altitude = None
        self.latitude = None
        self.longitude = None

        self.sent_target = False
        self.started_maneuver = False
        self.finished_dive = False

        self.initial_alt = 100  # Başlangıç yüksekliği

        self.att_pub = rospy.Publisher("/mavros/setpoint_raw/attitude", AttitudeTarget, queue_size=10)

        rospy.Subscriber("/mavros/global_position/global", NavSatFix, self.get_global_location)
        rospy.Subscriber("/mavros/global_position/local", Odometry, self.get_altitude)

        rospy.spin()

    def get_altitude(self, msg):
        self.altitude = msg.pose.pose.position.z

    def get_global_location(self, msg):
        self.latitude = msg.latitude
        self.longitude = msg.longitude

        if self.latitude is None or self.longitude is None or self.altitude is None:
            return

        current_pos = [self.latitude, self.longitude]
        distance_to_target = distance_calculator(current_pos, self.target_list)

        rospy.loginfo(f"Mesafe hedefe: {distance_to_target:.2f} m - İrtifa: {self.altitude:.2f} m")

        # İlk olarak hedefe yönlen
        if not self.sent_target:
            try:
                goto_srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
                resp = goto_srv(broadcast=0, frame=6, command=192,
                                x=self.target_lat_srv, y=self.target_lon_srv, z=self.initial_alt)
                rospy.loginfo("Hedef noktasına yönlendirildi.")
                self.sent_target = True
            except rospy.ServiceException:
                rospy.logwarn("Hedefe yönlendirme hatası.")

        # Hedefe 100m kala manevrayı başlat
        if distance_to_target < 100 and not self.started_maneuver:
            rospy.loginfo("100m kala manevra başlıyor: 45° yatış ve 25m dalış")
            attitude = AttitudeTarget()
            attitude.orientation.x = 0.0
            attitude.orientation.y = 0.382  # ~45° pitch
            attitude.orientation.z = 0.0
            attitude.orientation.w = 0.9238795
            self.att_pub.publish(attitude)
            self.started_maneuver = True

        # 25m alçaldıysa sağa yönel
        if self.started_maneuver and not self.finished_dive and self.altitude < self.initial_alt - 20:
            rospy.loginfo("Dalış tamamlandı, şimdi sağa 30° yöneliyor")
            attitude = AttitudeTarget()
            attitude.orientation.x = 0.0
            attitude.orientation.y = 0.0
            attitude.orientation.z = 0.195  # ~30° yaw
            attitude.orientation.w = 0.9808
            self.att_pub.publish(attitude)
            self.finished_dive = True

        # Eski yüksekliğe çık
        if self.finished_dive and self.altitude < self.initial_alt - 5:
            rospy.loginfo("Eski yüksekliğe çıkılıyor...")
            try:
                srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
                srv(broadcast=0, frame=6, command=192,
                    x=self.target_lat_srv, y=self.target_lon_srv, z=self.initial_alt)
            except rospy.ServiceException:
                rospy.logwarn("Yükseklik geri dönüş hatası.")

if __name__ == "__main__":
    try:
        ManevraNode()
    except rospy.ROSInterruptException:
        pass
