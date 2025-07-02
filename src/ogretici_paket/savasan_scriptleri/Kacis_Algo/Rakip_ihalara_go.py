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

        # 🎯 İlk hedef konum (manevra öncesi)
        self.target_lat = -35.35793014
        self.target_lon = 149.16416095
        self.target_lat_srv = int(self.target_lat * 1e7)
        self.target_lon_srv = int(self.target_lon * 1e7)
        self.initial_alt = 125
        self.target_list = [self.target_lat, self.target_lon]

        # Rakip uçağın konumu
        self.rakip_lat = None
        self.rakip_lon = None

        # Konum ve kontrol değişkenleri
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.return_lat = None
        self.return_lon = None

        # Aşama kontrol bayrakları
        self.sent_target = False
        self.started_maneuver = False
        self.finished_dive = False
        self.climb_maneuver_done = False
        self.returned = False
        self.sent_to_rakip = False

        # Publisher ve Subscriber
        self.att_pub = rospy.Publisher("/mavros/setpoint_raw/attitude", AttitudeTarget, queue_size=10)
        rospy.Subscriber("/mavros/global_position/global", NavSatFix, self.get_global_location)
        rospy.Subscriber("/mavros/global_position/local", Odometry, self.get_altitude)
        rospy.Subscriber("/mavros_rakip/global_position/global", NavSatFix, self.get_rakip_position)

        rospy.spin()

    def get_altitude(self, msg):
        self.altitude = msg.pose.pose.position.z

    def get_rakip_position(self, msg):
        self.rakip_lat = msg.latitude
        self.rakip_lon = msg.longitude

    def get_global_location(self, msg):
        self.latitude = msg.latitude
        self.longitude = msg.longitude

        if None in [self.latitude, self.longitude, self.altitude]:
            return

        current_pos = [self.latitude, self.longitude]
        dist_to_target = distance_calculator(current_pos, self.target_list)

        rospy.loginfo(f"Hedefe mesafe: {dist_to_target:.2f} m | İrtifa: {self.altitude:.2f} m")

        # 1️⃣ İlk hedefe yönel
        if not self.sent_target:
            try:
                srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
                srv(broadcast=0, frame=6, command=192,
                    x=self.target_lat_srv, y=self.target_lon_srv, z=self.initial_alt)
                rospy.loginfo("İlk hedefe yönlendirildi.")
                self.sent_target = True
            except rospy.ServiceException:
                rospy.logwarn("İlk hedef yönlendirmesi başarısız.")

        # 2️⃣ Manevra başlat (100 m kala)
        if dist_to_target < 100 and not self.started_maneuver:
            rospy.loginfo("Manevra başlatılıyor: 45° dalış")
            self.return_lat = self.latitude
            self.return_lon = self.longitude

            attitude = AttitudeTarget()
            attitude.orientation.x = 0.0
            attitude.orientation.y = 0.382  # ≈45° pitch
            attitude.orientation.z = 0.0
            attitude.orientation.w = 0.9238795
            self.att_pub.publish(attitude)

            rospy.sleep(2)
            self.started_maneuver = True

        # 3️⃣ Dalış tamamlandıysa 30° sağa yönel
        if self.started_maneuver and not self.finished_dive and self.altitude < self.initial_alt - 1:
            rospy.loginfo("Sağa 30° yönelme başlatılıyor")

            attitude = AttitudeTarget()
            attitude.orientation.x = 0.0
            attitude.orientation.y = 0.0
            attitude.orientation.z = 0.195  # ≈30° yaw
            attitude.orientation.w = 0.9808
            self.att_pub.publish(attitude)

            rospy.sleep(2)
            self.finished_dive = True

        # 4️⃣ Eski irtifaya çıkarken sağa yönel
        if self.finished_dive and not self.climb_maneuver_done:
            rospy.loginfo("Eski irtifaya çıkarken sağa 30° yönelme uygulanıyor")

            attitude = AttitudeTarget()
            attitude.orientation.x = 0.0
            attitude.orientation.y = 0.0
            attitude.orientation.z = 0.195
            attitude.orientation.w = 0.9808
            self.att_pub.publish(attitude)

            rospy.sleep(2)
            self.climb_maneuver_done = True

        # 5️⃣ Eski irtifaya çık ve geri dönüş
        if self.finished_dive and self.altitude < self.initial_alt - 1 and not self.returned:
            try:
                srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)

                # Yükselme komutu
                srv(broadcast=0, frame=6, command=192,
                    x=int(self.latitude * 1e7), y=int(self.longitude * 1e7), z=self.initial_alt)
                rospy.sleep(5)

                # Geri dönüş konumuna git
                if self.return_lat is not None and self.return_lon is not None:
                    srv(broadcast=0, frame=6, command=192,
                        x=int(self.return_lat * 1e7),
                        y=int(self.return_lon * 1e7),
                        z=self.initial_alt)
                    rospy.loginfo("Manevra başlangıç noktasına geri dönüldü.")
                    self.returned = True
                else:
                    rospy.logwarn("Geri dönüş konumu kayıtlı değil.")
            except rospy.ServiceException:
                rospy.logwarn("Geri dönüşte hata oluştu.")

        # 6️⃣ Rakip uçağa yönel
        if self.returned and not self.sent_to_rakip:
            if self.rakip_lat is not None and self.rakip_lon is not None:
                try:
                    rospy.loginfo("Rakip uçağa yönlendiriliyor...")
                    srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
                    srv(broadcast=0, frame=6, command=192,
                        x=int(self.rakip_lat * 1e7),
                        y=int(self.rakip_lon * 1e7),
                        z=self.initial_alt)
                    rospy.loginfo("Rakip uçağa komut gönderildi.")
                    self.sent_to_rakip = True
                except rospy.ServiceException:
                    rospy.logwarn("Rakip uçağa yönlendirme sırasında hata.")
            else:
                rospy.logwarn("Rakip konumu alınamadı.")

if __name__ == "__main__":
    try:
        ManevraNode()
    except rospy.ROSInterruptException:
        pass
