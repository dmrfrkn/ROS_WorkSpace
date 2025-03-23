#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
import actionlib
from ogretici_paket.msg import GorevDurumAction, GorevDurumFeedback, GorevDurumResult

class ActionServer():
    def __init__(self):
        rospy.init_node("action_servet_dugum")
        self.a_server = actionlib.SimpleActionServer("gorev", GorevDurumAction,auto_start= False, execute_cb=self.cevapUret)
        self.a_server.start()
        rospy.spin()
        
        
    def cevapUret(self,istek):
        geri_bildirim = GorevDurumFeedback()
        sonuc = GorevDurumResult()
        rate = rospy.Rate(1)
        for i in range(1,istek.birim):
            durum = "%" + str(i*100/istek.birim)
            geri_bildirim.oran = durum
            self.a_server.publish_feedback(geri_bildirim)
            rate.sleep()
        sonuc.sonuc = "Görev tamamlandi!"
        self.a_server.set_succeeded(sonuc)
        
        
a_s = ActionServer()


