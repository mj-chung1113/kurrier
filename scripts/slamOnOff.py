#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from kurrier.msg import mission  # 사용자 정의 메시지 임포트
import subprocess
import time
from std_msgs.msg import Int16, Bool

class slamOnOffNode:
    def __init__(self):
        rospy.init_node('slamOnOff_node', anonymous=True)
        rospy.Subscriber("/mission", mission, self.mission_callback)
        rospy.Subscriber("/is_stop", Bool, self.stop_callback)

        self.mission_info = mission()
        self.is_first_slam_started = False
        self.is_second_slam_started = False
        self.is_stopped = False

        rate = rospy.Rate(15)  # 15hz
        while not rospy.is_shutdown():
            self.check_mission()
            rate.sleep()

    def mission_callback(self, msg):
        self.mission_info = msg

    def stop_callback(self, msg):
        self.is_stopped = msg.data

    def check_mission(self):
        if self.mission_info.mission_num == 3 and not self.is_first_slam_started:
            if self.is_stopped:
                # 1. slam 런치 파일 실행
                launch_command = ["roslaunch", "kurrier", "kurrierSlam.launch"]
                process = subprocess.Popen(launch_command)
                time.sleep(3)  # 필요한 만큼 대기 (예: 다른 작업 수행)
                self.is_first_slam_started = True

        elif self.mission_info.mission_num != 3 and self.is_first_slam_started:
            # 2. slam 런치 파일 종료
            self.is_first_slam_started = False
            #process.terminate()  # 또는 
            process.kill()
            process.wait()  # 프로세스가 종료될 때까지 대기

if __name__ == '__main__':
    try:
        slamOnOff_node = slamOnOffNode()
    except rospy.ROSInterruptException:
        pass
