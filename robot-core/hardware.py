#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
from sensor_msgs.msg import Range
from std_msgs.msg import Bool, Float32
from geometry_msgs.msg import Twist
import cv2
from gpiozero import DistanceSensor
import RPi.GPIO as GPIO
import numpy as np

class RobotHardware:
    def __init__(self):
        # 기존 하드웨어 초기화 (변경 없음)
        self.cascade_path = "/home/sptcnl/haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.distance_sensor = DistanceSensor(echo=21, trigger=4)
        
        self.left_in3, self.left_in4, self.left_ena = 24, 23, 25
        self.right_in3, self.right_in4, self.right_enb = 18, 17, 27
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in [self.left_in3, self.left_in4, self.left_ena,
                    self.right_in3, self.right_in4, self.right_enb]:
            GPIO.setup(pin, GPIO.OUT)
        
        self.left_pwm = GPIO.PWM(self.left_ena, 1000)
        self.right_pwm = GPIO.PWM(self.right_enb, 1000)
        self.left_pwm.start(0)
        self.right_pwm.start(0)
        
        self.current_speed = 40
        self.stop()

    def detect_face(self):
        ret, frame = self.cap.read()
        if not ret:
            return False, 0.0
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
        distance = self.distance_sensor.distance * 100
        
        return len(faces) > 0, distance

    def execute_velocity(self, linear_x, angular_z):
        speed = max(0, min(100, int(abs(linear_x) * 100)))
        self.set_speed(speed)
        
        if abs(linear_x) < 0.01:
            self.stop()
        elif angular_z > 0.1:
            self.right_turn()
        elif angular_z < -0.1:
            self.left_turn()
        elif linear_x > 0:
            self.forward()
        else:
            self.backward()

    # 기존 모터 메서드들 (forward, backward, left_turn, right_turn, stop, set_speed) 그대로 유지
    def forward(self):
        GPIO.output(self.left_in3, GPIO.HIGH); GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.HIGH); GPIO.output(self.right_in4, GPIO.LOW)

    def backward(self):
        GPIO.output(self.left_in3, GPIO.LOW); GPIO.output(self.left_in4, GPIO.HIGH)
        GPIO.output(self.right_in3, GPIO.LOW); GPIO.output(self.right_in4, GPIO.HIGH)

    def left_turn(self):
        GPIO.output(self.left_in3, GPIO.LOW); GPIO.output(self.left_in4, GPIO.HIGH)
        GPIO.output(self.right_in3, GPIO.HIGH); GPIO.output(self.right_in4, GPIO.LOW)

    def right_turn(self):
        GPIO.output(self.left_in3, GPIO.HIGH); GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.LOW); GPIO.output(self.right_in4, GPIO.HIGH)

    def stop(self):
        GPIO.output(self.left_in3, GPIO.LOW); GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.LOW); GPIO.output(self.right_in4, GPIO.LOW)
        self.left_pwm.ChangeDutyCycle(0)
        self.right_pwm.ChangeDutyCycle(0)

    def set_speed(self, speed: int):
        speed = max(0, min(100, speed))
        self.current_speed = speed
        self.left_pwm.ChangeDutyCycle(speed)
        self.right_pwm.ChangeDutyCycle(speed)

    def cleanup(self):
        self.stop()
        if self.cap:
            self.cap.release()
        self.left_pwm.stop()
        self.right_pwm.stop()
        cv2.destroyAllWindows()
        GPIO.cleanup()

class FaceFollowingRobotNode(Node):
    def __init__(self):
        super().__init__('face_following_robot')
        
        # 하드웨어 초기화
        self.hardware = RobotHardware()
        
        # Publisher들
        self.face_pub = self.create_publisher(Bool, '/face_detected', 10)
        self.distance_pub = self.create_publisher(Range, '/distance_sensor', 10)
        self.status_pub = self.create_publisher(Float32, '/robot_status', 10)  # 0:stop, 1:follow
        
        # Subscriber
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        # 타이머 (50ms 주기 = 20Hz)
        timer_period = 0.05
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        self.get_logger().info('🤖 Face Following Robot Node 시작됨')
        self.hardware.start_camera()

    def timer_callback(self):
        # 얼굴 감지 + 센서 데이터 수집
        face_detected, distance_cm = self.hardware.detect_face()
        
        # 얼굴 감지 토픽
        face_msg = Bool()
        face_msg.data = face_detected
        self.face_pub.publish(face_msg)
        
        # 거리 센서 토픽 (Range 메시지)
        distance_msg = Range()
        distance_msg.header.stamp = self.get_clock().now().to_msg()
        distance_msg.header.frame_id = 'distance_sensor_link'
        distance_msg.radiation_type = Range.INFRARED
        distance_msg.field_of_view = 0.1
        distance_msg.min_range = 2.0
        distance_msg.max_range = 400.0
        distance_msg.range = float(distance_cm / 100.0)  # meters
        self.distance_pub.publish(distance_msg)
        
        # 자동 추적 로직 (거리 50cm 이내에서만)
        if face_detected and distance_cm > 50:
            # 자동 앞으로 (cmd_vel 대신 직접 제어)
            self.hardware.forward()
            self.hardware.set_speed(40)
            status_msg = Float32()
            status_msg.data = 1.0  # following
            self.status_pub.publish(status_msg)
        elif face_detected and distance_cm < 30:
            self.hardware.stop()
            status_msg = Float32()
            status_msg.data = 0.5  # too close
            self.status_pub.publish(status_msg)
        else:
            status_msg = Float32()
            status_msg.data = 0.0  # idle
            self.status_pub.publish(status_msg)

    def cmd_vel_callback(self, msg):
        """수동 제어용 cmd_vel 수신"""
        linear_x = msg.linear.x
        angular_z = msg.angular.z
        self.hardware.execute_velocity(linear_x, angular_z)

    def destroy_node(self):
        self.hardware.cleanup()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = FaceFollowingRobotNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()