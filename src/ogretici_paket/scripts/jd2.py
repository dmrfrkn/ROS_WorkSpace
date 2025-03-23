from dronekit import connect, VehicleMode, Vehicle, LocationGlobalRelative, Command
import time
from distutils.command.upload import upload
from pymavlink import mavutil
import numpy as np
import cv2
import math


iha = connect('127.0.0.1:14550', wait_ready=True, timeout=50, baud=921600)

one_time=True

komut=iha.commands



iha.parameters["TRIM_ARSPD_CM"] = 10
#print(iha.parameters["TRIM_ARSPD_CM"])

while True:
    roll_degeri=float(iha.attitude.roll)
    next_waypoint=komut.next # bir  sonraki waypointin hangisi olduğunu gösteriyor.
    irtifa=iha.location.global_relative_frame.alt
    time.sleep(.1)

    fark=15
    normal=fark/400 # 1 metrenin pwm değeri (kat sayi)
    valuem=1500-((irtifa-5)/normal)
    print(int(valuem))
    #print(f'normal= {normal}, valuem: {valuem}, irtifa: {irtifa}, irtifanormal=. {fark/normal} fark= {fark}')

    if next_waypoint == 5 :
        if one_time==True:
            time.sleep(.1)
            one_time==False
        print("5 e girdi")
        if (roll_degeri<.05 and roll_degeri>-.05):
            if irtifa>=4:
                iha.mode=VehicleMode("FBWA")
                print("override girdi")
                iha.channels.overrides['2']=int(valuem) + 50
                iha.flush()
            else:
                iha.channels.overrides['2']=1700
                iha.channels.overrides['2']=1500
                time.sleep(1)
                iha.channels.overrides['2'] = None
                #iha.channels.overrides = {}
                iha.flush()
                iha.mode=VehicleMode("AUTO")
                komut.next = 6

    if next_waypoint == 3:
        one_time==True
        #iha.mode=VehicleMode("FBWA")
        #iha.channels.overrides['2']=valuem
        # irtifa-next_waypoint_irtifa/400
        # 20-5=15https://meet.google.com/ecq-vgcc-iuw
        # 400/15= 26



        #15/400=0,0375 1 pwm 0,0375 metre değiştiriyor kaç pwm değiştirsek fark olur
        #valuem=trim-(fark/normal)

        # her 1 metre 26 pwm
        # trim-(irtifam)26