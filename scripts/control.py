#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from math import cos,sin,sqrt,pow,atan2
from geometry_msgs.msg import Point
from nav_msgs.msg import Odometry,Path
from morai_msgs.msg import CtrlCmd, EventInfo
from std_msgs.msg import Int16, Bool
import numpy as np
from tf.transformations import euler_from_quaternion
from kurrier.msg import mission, obstacle   # 사용자 정의 메시지 임포트 
from morai_msgs.srv import MoraiEventCmdSrv
from enum import Enum

class Gear(Enum):
    P = 1
    R = 2
    N = 3
    D = 4

class pure_pursuit :
    def __init__(self):
        rospy.init_node('control', anonymous=True)
        rospy.Subscriber("/lattice_path", Path, self.path_callback)
        rospy.Subscriber("/odom", Odometry, self.odom_callback)
        rospy.Subscriber("/obstacle_info", obstacle, self.yolo_callback)
        rospy.Subscriber("/mission", mission, self.mission_callback)
        rospy.Subscriber("traffic_light_color", Int16, self.traffic_callback)
        rospy.Subscriber("/check_finish", Bool, self.finish_callback)

        self.stop_pub = rospy.Publisher('/is_stop', Bool, queue_size=1)
        self.ctrl_cmd_pub = rospy.Publisher('/ctrl_cmd',CtrlCmd, queue_size=10)
        self.ctrl_cmd_msg=CtrlCmd()
        self.ctrl_cmd_msg.longlCmdType=2

        self.is_path=False
        self.is_odom=False
        self.is_yolo=False

        self.traffic_light_color = ""
        self.obstacle = obstacle()
        self.forward_point=Point()
        self.current_postion=Point()
        self.is_look_forward_point=False
        self.vehicle_length=3
        self.lfd=5

        self.is_waiting_time = False
        self.count = 0
        self.mission_info = mission()

        self.is_finish = False
        self.is_stopped = False
        self.M7_complete = False
        
        # 기어 변경 서비스 설정
        rospy.loginfo("connecting service")
        rospy.wait_for_service('/Service_MoraiEventCmd', timeout=5)
        self.event_cmd_srv = rospy.ServiceProxy('Service_MoraiEventCmd', MoraiEventCmdSrv)
        rospy.loginfo("service connected")

        rate = rospy.Rate(15) # 15hz
        while not rospy.is_shutdown():

            if self.is_path ==True and self.is_odom==True  :
                
                vehicle_position=self.current_postion
                self.is_look_forward_point= False

                translation=[vehicle_position.x, vehicle_position.y]

                t=np.array([
                        [cos(self.vehicle_yaw), -sin(self.vehicle_yaw),translation[0]],
                        [sin(self.vehicle_yaw),cos(self.vehicle_yaw),translation[1]],
                        [0                    ,0                    ,1            ]])

                det_t=np.array([
                       [t[0][0],t[1][0],-(t[0][0]*translation[0]+t[1][0]*translation[1])],
                       [t[0][1],t[1][1],-(t[0][1]*translation[0]+t[1][1]*translation[1])],
                       [0      ,0      ,1                                               ]])

                for num,i in enumerate(self.path.poses) :
                    path_point=i.pose.position

                    global_path_point=[path_point.x,path_point.y,1]
                    local_path_point=det_t.dot(global_path_point)           
                    if local_path_point[0]>0 :
                        dis=sqrt(pow(local_path_point[0],2)+pow(local_path_point[1],2))
                        if dis>= self.lfd :
                            self.forward_point=path_point
                            self.is_look_forward_point=True
                            break
                
                theta=atan2(local_path_point[1],local_path_point[0])
                default_vel = 10

                if self.is_look_forward_point :
                    # steering
                    self.ctrl_cmd_msg.steering = atan2(2.0 * self.vehicle_length * sin(theta), self.lfd)  
                    normalized_steer = abs(self.ctrl_cmd_msg.steering)/0.6981          

                    # velocity
                    if self.mission_info.mission_num == 71:
                        if not self.M7_complete:
                            if not self.is_stopped:
                                self.stop_vehicle()
                            else:
                                # 초록불에만 출발
                                if self.traffic_light_color==3:
                                    self.ctrl_cmd_msg.velocity = default_vel*(1.0-(self.obstacle.collision_probability/100))*(1-0.5*normalized_steer)
                                    self.is_stopped = False
                                    self.M7_complete = True
                                else:
                                    self.ctrl_cmd_msg.velocity = 0
                        else:
                            self.ctrl_cmd_msg.velocity = default_vel

                    elif self.mission_info.mission_num == 8:
                        if self.is_finish:
                            # if not self.is_stopped:
                                self.stop_vehicle()
                                self.send_gear_cmd(Gear.P.value)
                        else:
                            self.ctrl_cmd_msg.velocity = default_vel

                    elif self.mission_info.mission_num == 3:
                        if self.mission_info.count == 1:
                            self.stop_vehicle()
                        else:
                            self.ctrl_cmd_msg.velocity = default_vel*(1-0.6*normalized_steer)
                            self.is_stopped = False

                    elif self.mission_info.mission_num == 6:
                        if self.mission_info.count == 1:
                            self.stop_vehicle()
                        else:
                            self.ctrl_cmd_msg.velocity = default_vel
                            self.is_stopped = False
                    else:
                        self.ctrl_cmd_msg.velocity = default_vel*(1.0-(self.obstacle.collision_probability/100))*(1-0.6*normalized_steer)

                else : 
                    rospy.loginfo_once("no found forward point")
                    self.ctrl_cmd_msg.steering=0.0
                    self.ctrl_cmd_msg.velocity=0.0
                
                self.ctrl_cmd_pub.publish(self.ctrl_cmd_msg)

            self.is_path = self.is_odom = False
            rate.sleep()

    def path_callback(self,msg):
        self.is_path=True
        self.path=msg      
        
    def yolo_callback(self,msg):
        self.is_yolo = True
        self.obstacle = msg

    def mission_callback(self,msg):
        self.mission_info = msg

    def odom_callback(self,msg):
        self.is_odom=True
        odom_quaternion=(msg.pose.pose.orientation.x,msg.pose.pose.orientation.y,msg.pose.pose.orientation.z,msg.pose.pose.orientation.w)
        _,_,self.vehicle_yaw=euler_from_quaternion(odom_quaternion)
        self.current_postion.x=msg.pose.pose.position.x
        self.current_postion.y=msg.pose.pose.position.y

    def traffic_callback(self, msg):
        self.traffic_color = msg 

    def finish_callback(self, msg):
        self.is_finish = msg.data

    def send_gear_cmd(self, gear_mode):
        #기어 변경 요청을 서비스 콜을 통해 전송하고 성공 여부를 반환
        try:
            gear_cmd = EventInfo()
            gear_cmd.option = 3
            gear_cmd.ctrl_mode = 3
            gear_cmd.gear = gear_mode

            response = self.event_cmd_srv(gear_cmd)

            if response:
                rospy.loginfo(f"Gear successfully changed to {gear_mode}")
                rospy.sleep(1)  # 기어 변경 후 안정화 시간 추가
                return True
            else:
                rospy.logerr(f"Failed to change gear to {gear_mode}")
                return False
        except rospy.ServiceException as e:
            rospy.logerr(f"Service call failed: {e}")
            return False
        
    def stop_vehicle(self):
        # 차량을 완전히 정지시키기 위해 속도를 0으로 설정하고 조향 각도를 0으로 설정, 브레이크를 적용
        self.ctrl_cmd_msg.velocity = 0.0
        self.ctrl_cmd_msg.steering = 0.0  # 조향 각도를 0으로 설정
        self.ctrl_cmd_msg.brake = 1.0  # 최대 제동력
        self.ctrl_cmd_pub.publish(self.ctrl_cmd_msg)
        # 완전정지를 위해 3초 대기
        rospy.sleep(3)
        rospy.loginfo("Vehicle stopped") 
        # 정지후 다른 노드들 행동을 기다리기 위해 정지신호 pub후 3초 추가 대기
        self.is_stopped = True
        self.stop_pub.publish(self.is_stopped)
        rospy.sleep(3)
        #브레이크 끄기
        self.ctrl_cmd_msg.brake = 0

        
if __name__ == '__main__':
    try:
        test_track=pure_pursuit()
    except rospy.ROSInterruptException:
        pass
