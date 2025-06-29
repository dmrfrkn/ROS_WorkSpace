#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy 
from ogretici_paket.msg import BataryaDurum

def mesajYayinla():
    rospy.init_node("yayinci_dugumu",anonymous=True)
    pub = rospy.Publisher("batarya_konusu",BataryaDurum,queue_size=10)
    rate  = rospy.Rate(1)
    while not rospy.is_shutdown():
        durum = "%42"
        rospy.loginfo(durum)
        pub.publish(durum)
        rate.sleep()
        
mesajYayinla()