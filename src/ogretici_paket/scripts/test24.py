#!/usr/bin/env python3

import rospy
from mavros_msgs.msg import State
from mavros_msgs.srv import SetMode, CommandBool
from geometry_msgs.msg import PoseStamped

# Aracın durumu için bir geri çağırma (callback) fonksiyonu
current_state = State()
def state_cb(state):
    global current_state
    current_state = state

# Hedef pozisyonu belirleyen fonksiyon
def set_target_position(x, y, z):
    target_pose = PoseStamped()
    target_pose.header.stamp = rospy.Time.now()
    target_pose.pose.position.x = x
    target_pose.pose.position.y = y
    target_pose.pose.position.z = z
    return target_pose

if __name__ == "__main__":
    rospy.init_node("guided_node")

    # Aracın durumunu izleyen bir abone oluşturma
    state_sub = rospy.Subscriber("/mavros/state", State, state_cb)

    # Hedef pozisyon için bir yayıncı oluşturma
    local_pos_pub = rospy.Publisher("/mavros/setpoint_position/local", PoseStamped, queue_size=10)

    # GUIDED moda geçmek için servis istemcisi oluşturma
    set_mode_client = rospy.ServiceProxy("/mavros/set_mode", SetMode)

    # Araç arming (silahlandırma) servisi istemcisi oluşturma
    arm_client = rospy.ServiceProxy("/mavros/cmd/arming", CommandBool)

    rate = rospy.Rate(20)  # 20Hz

    # MAVROS'a bağlanmasını bekle
    while not rospy.is_shutdown() and not current_state.connected:
        rate.sleep()

    # İlk hedef pozisyonu belirleme (örneğin 0, 0, 2 metre)
    target_position = set_target_position(0, 0, 2)

    # Hedef pozisyonunu belirlemek için yeterli setpoint göndermek için bekleyin
    for _ in range(100):
        local_pos_pub.publish(target_position)
        rate.sleep()

    last_request = rospy.Time.now()

    while not rospy.is_shutdown():
        if current_state.mode != "GUIDED" and (rospy.Time.now() - last_request > rospy.Duration(5.0)):
            if set_mode_client(base_mode=0, custom_mode="GUIDED").mode_sent:
                rospy.loginfo("GUIDED mode enabled")
            last_request = rospy.Time.now()
        else:
            if not current_state.armed and (rospy.Time.now() - last_request > rospy.Duration(5.0)):
                if arm_client(True).success:
                    rospy.loginfo("Vehicle armed")
                last_request = rospy.Time.now()

        # Hedef pozisyonunu sürekli olarak gönder
        local_pos_pub.publish(target_position)
        rate.sleep()
