import rospy
from geometry_msgs.msg import Twist

def movement():
    rospy.init_node("go drag")
    pub = rospy.Publisher("cmd_vel", Twist, queue_size=10)
    velocity_msg = Twist()
    velocity_msg.linear.x = 0.5
    distance = 5
    substitution = 0
    t0 = rospy.Time.now().to_sec()
    while(substitution  <distance):
        pub.publish(velocity_msg)
        t1 = rospy.Time.now().to_sec()
        substitution = velocity_msg.linear.x * (t1-t0)
    velocity_msg.linear.x = 0
    pub.publish(velocity_msg)
    rospy.loginfo("Hedefe varildi")
    
    
    
movement()
