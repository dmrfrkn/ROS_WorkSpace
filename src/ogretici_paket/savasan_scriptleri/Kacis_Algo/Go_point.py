#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import rospy
from mavros_msgs.srv import CommandInt
from std_msgs.msg import Header

class WaypointSender:
    def __init__(self):
        rospy.init_node("goto_gps_node")

        # Hedef GPS konumu
        self.target_lat = -35.35467   # derece cinsinden
        self.target_lon = 149.160763   # derece cinsinden
        self.altitude = 125            # hedef irtifa (metre)

        # MAVLink koordinat dönüşümü (1e7)
        self.target_lat_int = int(self.target_lat * 1e7)
        self.target_lon_int = int(self.target_lon * 1e7)

        rospy.wait_for_service("/mavros/cmd/command_int")
        try:
            goto_service = rospy.ServiceProxy("/mavros/cmd/command_int", CommandInt)
            rospy.loginfo("Servise bağlandı, konum gönderiliyor...")

            # CommandInt ile hedef konuma yönlendir
            resp = goto_service(
                broadcast=0,
                frame=6,              # MAV_FRAME_GLOBAL_RELATIVE_ALT
                command=192,          # MAV_CMD_NAV_WAYPOINT
                current=0,
                autocontinue=1,
                param1=0,             # Hold time
                param2=0,             # Acceptance radius
                param3=1,             # Pass through waypoint
                param4=0,             # Yaw angle
                x=self.target_lat_int,
                y=self.target_lon_int,
                z=self.altitude
            )

            if resp.success:
                rospy.loginfo("Konum başarıyla gönderildi!")
            else:
                rospy.logwarn("Konum gönderilemedi!")
        except rospy.ServiceException as e:
            rospy.logerr(f"Servis çağrısı başarısız: {e}")

if __name__ == "__main__":
    try:
        WaypointSender()
    except rospy.ROSInterruptException:
        pass
