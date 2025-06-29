#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
from mavros_msgs.srv import CommandInt
from mavros_msgs.msg import AttitudeTarget
from geopy.distance import distance

# İki konum arasındaki mesafeyi hesaplayan yardımcı fonksiyon
def distance_calculator(plane_loc, air_defence_loc):
    return distance(plane_loc, air_defence_loc).meters


class KamikazeNode:

    def __init__(self):
        rospy.init_node("kamikaze_gorev_node")

        # İlk hedef lokasyon (hava savunma noktasına gitmeden önceki hedef)
        self.first_loc_latitude = -35.356467
        self.first_loc_longitude = 149.160763
        self.first_loc_latitude_srv = -353453529
        self.first_loc_longitude_srv = 1491593658
        self.first_loc_list = [self.first_loc_latitude, self.first_loc_longitude]

        # Kamikaze hedef lokasyonu
        self.kamikaze_latitude = -35.362879
        self.kamikaze_longitude = 149.165168
        self.kamikaze_latitude_srv = -353628790
        self.kamikaze_longitude_srv = 1491651680
        self.kamikaze_loc_list = [self.kamikaze_latitude, self.kamikaze_longitude]

        # Konum ve mesafe değişkenleri
        self.latitude = None
        self.longitude = None
        self.altitude = None

        # Görev kontrol indeksleri
        self.index = 0      # İlk hedefe gitme kontrolü
        self.index_2 = 0    # Kamikaze noktasına gitme kontrolü
        self.index3 = 0     # Dalış başlatma kontrolü
        self.index4 = 0     # Pas geçme kontrolü

        # Publisher: Attitude kontrolü için
        self.angle_settings = rospy.Publisher("/mavros/setpoint_raw/attitude", AttitudeTarget, queue_size=10)

        # Subscriberlar
        self.global_loc_sub = rospy.Subscriber("/mavros/global_position/global", NavSatFix, self.get_global_location)
        self.local_loc_sub = rospy.Subscriber("/mavros/global_position/local", Odometry, self.get_local_location_alt)

        rospy.spin()


    def get_local_location_alt(self, msg):
        # Altitude bilgisini al
        self.altitude = msg.pose.pose.position.z
        rospy.loginfo(f"Yükseklik: {self.altitude:.2f} m")


    def get_global_location(self, msg):
        self.latitude = msg.latitude
        self.longitude = msg.longitude

        # İHA'nın anlık konumu ile mesafeleri hesapla
        current_pos = [self.latitude, self.longitude]
        dist_to_first = distance_calculator(current_pos, self.first_loc_list)
        dist_to_kamikaze = distance_calculator(current_pos, self.kamikaze_loc_list)

        rospy.loginfo(f"İlk hedefe uzaklık: {dist_to_first:.2f} m")
        rospy.loginfo(f"Kamikaze noktasına uzaklık: {dist_to_kamikaze:.2f} m")

        attitude_msg = AttitudeTarget()

        # İlk hedefe git (sadece bir kez)
        if self.index == 0:
            try:
                goto_srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
                response = goto_srv(broadcast=0, frame=6, command=192,
                                    x=self.first_loc_latitude_srv,
                                    y=self.first_loc_longitude_srv,
                                    z=100)
                self.index += 1
                rospy.loginfo("İlk lokasyona yönlendirildi.")
            except rospy.ServiceException:
                rospy.logwarn("İlk lokasyona giderken hata oluştu.")

        # İlk hedefe ulaşıldıysa kamikaze hedef noktasına git
        if dist_to_first < 100 and self.index_2 == 0:
            rospy.loginfo("Kamikaze lokasyonuna yönlendiriliyor.")
            try:
                kamikaze_srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
                response2 = kamikaze_srv(broadcast=0, frame=6, command=192,
                                         x=self.kamikaze_latitude_srv,
                                         y=self.kamikaze_longitude_srv,
                                         z=100)
                self.index_2 += 1
            except rospy.ServiceException:
                rospy.logwarn("Kamikaze lokasyonuna giderken hata oluştu.")

        # Kamikaze konumuna yakınsa ve yüksekliği uygunsa dalış başlat
        if dist_to_kamikaze < 175 and self.index_2 > 0 and self.altitude and self.altitude > 20:
            self.index3 += 1
            rospy.loginfo("Kamikaze dalışı başlatıldı.")
            # 45 derece eğimle ileri dalış (örnek quaternion değerleri)
            attitude_msg.orientation.x = 0.0
            attitude_msg.orientation.y = 0.382  # yaklaşık 45 derece pitch
            attitude_msg.orientation.z = 0.0
            attitude_msg.orientation.w = 0.9238795
            self.angle_settings.publish(attitude_msg)

        # Alçak irtifaya ulaşıldığında pas geç (tekrar yönlendirme)
        if self.altitude and self.altitude < 20 and self.index3 > 0 and self.index4 == 0:
            self.index4 += 1
            rospy.loginfo("Düşük irtifa! Pas geçme işlemi başlatılıyor.")
            try:
                pass_srv = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
                response3 = pass_srv(broadcast=0, frame=6, command=192,
                                     x=self.kamikaze_latitude_srv,
                                     y=self.kamikaze_longitude_srv,
                                     z=100)
            except rospy.ServiceException:
                rospy.logwarn("Pas geçme işlemi sırasında hata.")


# Node başlat
if __name__ == "__main__":
    try:
        KamikazeNode()
    except rospy.ROSInterruptException:
        pass
