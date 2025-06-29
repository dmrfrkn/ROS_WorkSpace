#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#! /usr/bin/env python
import rospy
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
from mavros_msgs.srv import CommandInt
from mavros_msgs.msg import AttitudeTarget
from geopy.distance import distance

def distance_calculator(plane_loc,air_Defence_loc):
        mesafe=distance(plane_loc,air_Defence_loc).meters
        return mesafe


class kamikaze_node:


    def __init__(self):

        #-----------------first location to go -------------------#
        self.first_loc_latitude_srv=-353453529#-353564670
        self.first_loc_longtitude_srv=1491593658#1491607630
        self.first_loc_latitude=-35.356467
        self.first_loc_longtitude=149.160763
        self.first_loc_list=[self.first_loc_latitude,self.first_loc_longtitude]
        
        self.index=0
        self.index3=0
        self.index4=0
        


        #-----------------kamikaze lokasyonları------------------#
        self.latitude_kamikaze_srv=-353628790
        self.longitude_kamikaze_srv=1491651680
        self.latitude_kamikaze=-35.362879
        self.longitude_kamikaze=149.165168
        self.kamikaze_loc_list=[self.latitude_kamikaze,self.longitude_kamikaze]
        self.index_2=0
        
        self.latitude=None
        self.longitude=None
        self.altitude=None
        self.global_location_list=[10,20]
        self.mesafe_x=None

        rospy.init_node("kamikaze_görev_node")

        self.angle_settings=rospy.Publisher("/mavros/setpoint_raw/attitude",AttitudeTarget)
        #----------------------Subscriber-----------------------------#
        self.global_loc_sub=rospy.Subscriber("/mavros/global_position/global",NavSatFix,self.get_global_location)
        self.local_loc_sub=rospy.Subscriber("/mavros/global_position/local",Odometry,self.get_local_location_alt)
        #-----------------------Service tanımlamaları-----------------#
        
        
        rospy.spin()



    def get_local_location_alt(self,msg):
        self.altitude=msg.pose.pose.position.z
        rospy.logout(self.altitude)

        


    def get_global_location(self,msg):
        self.latitude=msg.latitude
        self.longitude=msg.longitude
        rospy.logout(self.latitude)
        print("kamikaze test fonksiyonuna girdi")
        first_loc_to_iha_loc_distance=distance_calculator([self.latitude,self.longitude],self.first_loc_list)
        iha_loc_to_kamikaze_distance=distance_calculator([self.latitude,self.longitude],self.kamikaze_loc_list)
        print("ilk konum ile iha konumu arası mesafe:",first_loc_to_iha_loc_distance)
        print("iha konumu ile kamikaze arası mesafe:",iha_loc_to_kamikaze_distance)
        print("yükseklik:",self.altitude)
        angel_set_pos=AttitudeTarget()

        if self.index==0:
             
            try:
                service=rospy.ServiceProxy("/mavros/cmd/command_int",CommandInt)
                response_mode=service(broadcast=0,frame=6,command=192,x=self.first_loc_latitude_srv,y=self.first_loc_longtitude_srv,z=100)

                self.index +=1
            except:
                rospy.logwarn("Lokasyona giderken bir hata oluşmuş olabilir")
                 
                
        else:
            print("-------")


            


        if first_loc_to_iha_loc_distance<100 and self.index_2==0:

            print("Kamimaze noktasına gidiliyor")



            try:
                service_2=rospy.ServiceProxy("/mavros/cmd/command_int",CommandInt)
                response_mode2=service_2(broadcast=0,frame=6,command=192,x=self.latitude_kamikaze_srv,y=self.longitude_kamikaze_srv,z=100)
                self.index_2 +=1


            except:
                print("kamikaze lokasyonuna gidiyor")
        if iha_loc_to_kamikaze_distance<175 and self.index_2>0:    #self.index_2>0:

            
            self.index3 +=1


            if self.altitude>20:


                print("kamikaze dalışına başladı")

                angel_set_pos.orientation.x=0.0
                angel_set_pos.orientation.y=0.382
                angel_set_pos.orientation.z=0.0
                angel_set_pos.orientation.w=0.9238795
                self.angle_settings.publish(angel_set_pos)

        if self.altitude<20 and self.index3>0:

            self.index4 +=1

            if self.index4==1:


                try:
                    service_3=rospy.ServiceProxy("/mavros/cmd/command_int",CommandInt)
                    response_mode3=service_3(broadcast=0,frame=6,command=192,x=self.latitude_kamikaze_srv,y=self.longitude_kamikaze_srv,z=100)
                    self.index3 +=1


                except:

                    print("pas geçme işlemi başlad")
class_of_kamikaze=kamikaze_node()