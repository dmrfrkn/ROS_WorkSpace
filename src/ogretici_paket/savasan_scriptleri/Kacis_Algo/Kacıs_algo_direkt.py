#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
from mavros_msgs.srv import CommandInt
from mavros_msgs.msg import AttitudeTarget
from geometry_msgs.msg import PoseStamped
from geopy.distance import distance

class ManevraNode:
    def __init__(self):
        rospy.init_node("manevra_gorev_node")

        # Başlangıç irtifası ve hedefler
        self.initial_alt = 125.0
        self.target_dive_alt = self.initial_alt - 100.0  # 40m dalış hedefi
        self.forward_distance = 20.0  # ileri uçuş mesafesi (metre)
        self.side_maneuver_distance = 40.0  # yan manevra mesafesi (metre)
        self.side_maneuver_altitude_gain = 40.0  # manevrada irtifa artışı (metre)

        # Anlık pozisyonlar
        self.local_x = None
        self.local_y = None
        self.altitude = None

        # Rakip uçağın GPS konumu
        self.rakip_lat = None
        self.rakip_lon = None

        # Durum bayrakları
        self.state = 0  # Manevra aşamalarını tutacak

        # Publisher ve Subscriber
        self.att_pub = rospy.Publisher("/mavros/setpoint_raw/attitude", AttitudeTarget, queue_size=10)
        self.pos_pub = rospy.Publisher("/mavros/setpoint_position/local", PoseStamped, queue_size=10)
        rospy.Subscriber("/mavros/global_position/local", Odometry, self.local_position_callback)
        rospy.Subscriber("/mavros_rakip/global_position/global", NavSatFix, self.rakip_callback)

        rospy.sleep(3)  # İlk verilerin gelmesi için bekle
        self.control_loop()

    def local_position_callback(self, msg):
        self.local_x = msg.pose.pose.position.x
        self.local_y = msg.pose.pose.position.y
        self.altitude = msg.pose.pose.position.z

    def rakip_callback(self, msg):
        self.rakip_lat = msg.latitude
        self.rakip_lon = msg.longitude

    def publish_position(self, x, y, z):
        pose = PoseStamped()
        pose.header.stamp = rospy.Time.now()
        pose.header.frame_id = "map"
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        self.pos_pub.publish(pose)

    def publish_attitude(self, pitch=0.0, yaw=0.0):
        attitude = AttitudeTarget()
        attitude.type_mask = 128  # sadece orientation kullansın
        attitude.orientation.x = 0.0
        attitude.orientation.y = pitch  # pitch (y ekseni etrafı)
        attitude.orientation.z = yaw    # yaw (z ekseni etrafı)
        attitude.orientation.w = 0.9238795  # yaklaşık sabit
        self.att_pub.publish(attitude)

    def control_loop(self):
        rate = rospy.Rate(5)  # 5 Hz
        while not rospy.is_shutdown():
            if self.local_x is None or self.altitude is None:
                rate.sleep()
                continue

            rospy.loginfo(f"State: {self.state} | x={self.local_x:.2f} y={self.local_y:.2f} Altitude={self.altitude:.2f}")

            if self.state == 0:
                rospy.loginfo("🚀 45° dalış başlatılıyor...")
                self.publish_attitude(pitch=0.382)
                # Dalışta yatay pozisyon sabit kalmalı
                self.publish_position(self.local_x, self.local_y, self.target_dive_alt)
                self.state = 1
                rospy.sleep(1)

            elif self.state == 1:
                rospy.loginfo(f"Dalış kontrolü: Current Altitude={self.altitude:.2f} Target={self.target_dive_alt:.2f}")
                if self.altitude <= self.target_dive_alt + 1.0:
                    rospy.loginfo("⬇️ Dalış tamamlandı, ileri uçuşa geçiliyor...")
                    hedef_x = self.local_x + self.forward_distance
                    self.publish_attitude(pitch=0.0)
                    self.publish_position(hedef_x, self.local_y, self.altitude)
                    self.state = 2
                    rospy.sleep(3)

if __name__ == "__main__":
    try:
        ManevraNode()
    except rospy.ROSInterruptException:
        pass
