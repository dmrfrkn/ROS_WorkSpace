#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from ogretici_paket.srv import GecenZaman

def istekteBulun(x):
    rospy.wait_for_service("zaman")
    try:
        servis = rospy.ServiceProxy("zaman",GecenZaman)
        cevap = servis(x)
        return cevap.gecen_sure
    except rospy.ServiceException:
        print("Servisle alakali hata")

hedef =float( input("Hedef konum giriniz"))

cikti = istekteBulun(hedef)
print("Hedefe varana kadar geçen süre" ,cikti)


