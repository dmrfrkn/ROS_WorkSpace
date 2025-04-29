import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

class HedefeGit():
    def __init__(self):
        rospy.init_node("duz_git")
        rospy.Subscriber("odom", Odometry,self.odomCallback)
        rospy.spin()
        
    def odomCallBack(self,mesaj):
        print(mesaj.pose.pose.position.x)


HedefeGit()