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

        # 🎯 Yeni hedef nokta (koordinatlar ve yükseklik)
        self.target_lat = -35.35974472
        self.target_lon = 149.16191501
        self.target_lat_srv = int(self.target_lat * 1e7)     # -353597447
        self.target_lon_srv = int(self.target_lon * 1e7)     # 1491619150
        self.target_list = [self.target_lat, self.target_lon]

        self.initial_alt = 583.8  # Yeni hedef yüksekliği (metre)

        # Konum ve durum bilgileri
        self.altitude = None
        self.latitude = None
        self.longitude = None

        self.sent_target = False
        self.started_maneuver = False
        self.finished_dive = False
        self.returned = False

        self.return_lat = None
        self.return_lon = None

        # Publisher
        self.att_pub = rospy.Publisher("/mavros/setpoint_raw/attitude", AttitudeTarget, queue_size=10)

        # Subscriberlar
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

        # 1. Hedefe yönlen
        if not self.sent_target:
            try:
                goto_srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
                goto_srv(broadcast=0, frame=6, command=192,
                         x=self.target_lat_srv, y=self.target_lon_srv, z=self.initial_alt)
                rospy.loginfo("Hedef noktasına yönlendirildi.")
                self.sent_target = True
            except rospy.ServiceException:
                rospy.logwarn("Hedefe yönlendirme hatası.")

        # 2. 100 metre kala manevraya başla
        if distance_to_target < 100 and not self.started_maneuver:
            rospy.loginfo("100m kala manevra başlıyor: 45° dalış")

            self.return_lat = self.latitude
            self.return_lon = self.longitude

            attitude = AttitudeTarget()
            attitude.orientation.x = 0.0
            attitude.orientation.y = 0.382  # 45° pitch
            attitude.orientation.z = 0.0
            attitude.orientation.w = 0.9238795
            self.att_pub.publish(attitude)

            self.started_maneuver = True

        # 3. Alçaldıysa sağa yönel
        if self.started_maneuver and not self.finished_dive and self.altitude < self.initial_alt - 20:
            rospy.loginfo("Dalış tamamlandı, şimdi sağa 30° yöneliyor")

            attitude = AttitudeTarget()
            attitude.orientation.x = 0.0
            attitude.orientation.y = 0.0
            attitude.orientation.z = 0.195  # 30° yaw
            attitude.orientation.w = 0.9808
            self.att_pub.publish(attitude)

            self.finished_dive = True

        # 4. Eski yüksekliğe çık, ardından manevra başlama noktasına geri dön
        if self.finished_dive and self.altitude < self.initial_alt - 5 and not self.returned:
            rospy.loginfo("Eski yüksekliğe çıkılıyor ve geri dönülüyor...")

            try:
                srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)

                # Önce yüksel
                srv(broadcast=0, frame=6, command=192,
                    x=int(self.latitude * 1e7), y=int(self.longitude * 1e7), z=self.initial_alt)
                rospy.sleep(5)

                # Ardından manevraya başlanan konuma dön
                if self.return_lat is not None and self.return_lon is not None:
                    srv(broadcast=0, frame=6, command=192,
                        x=int(self.return_lat * 1e7), y=int(self.return_lon * 1e7), z=self.initial_alt)
                    rospy.loginfo("Geri dönüş başarılı.")
                    self.returned = True
                else:
                    rospy.logwarn("Geri dönüş konumu kaydedilmedi.")

            except rospy.ServiceException:
                rospy.logwarn("Geri dönüş işlemi sırasında hata.")

if __name__ == "__main__":
    try:
        ManevraNode()
    except rospy.ROSInterruptException:
        pass
