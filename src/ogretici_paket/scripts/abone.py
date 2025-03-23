#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from ogretici_paket.msg import BataryaDurum



def bataryaFonskiyonu(mesaj):
    rospy.loginfo("Robot şarji: %s"%mesaj.batarya)
    
def mesajDinle():
    rospy.init_node("abone_dugumu")
    rospy.Subscriber("batarya_konusu",BataryaDurum,bataryaFonskiyonu)
    rospy.spin()
    
mesajDinle()
