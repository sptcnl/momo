import cv2
import time
from gpiozero import DistanceSensor
import RPi.GPIO as GPIO

class RobotHardware:
    def __init__(self):
        # ========= 카메라 (USB) =========
        self.cascade_path = "/home/sptcnl/haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # ========= 거리 센서 =========
        self.distance_sensor = DistanceSensor(echo=21, trigger=4)

        # ========= 모터 핀 =========
        self.left_in3, self.left_in4, self.left_ena = 24, 23, 25
        self.right_in3, self.right_in4, self.right_enb = 18, 17, 27

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for pin in [
            self.left_in3, self.left_in4, self.left_ena,
            self.right_in3, self.right_in4, self.right_enb
        ]:
            GPIO.setup(pin, GPIO.OUT)

        self.left_pwm = GPIO.PWM(self.left_ena, 1000)
        self.right_pwm = GPIO.PWM(self.right_enb, 1000)
        self.left_pwm.start(0)
        self.right_pwm.start(0)

        # ========= 상태 =========
        self.is_moving = False
        self.current_speed = 40
        self.current_distance = 0.0
        self.face_detected = False

        self.stop()

    # ==============================
    # 카메라
    # ==============================
    def start_camera(self):
        ret, _ = self.cap.read()
        if ret:
            print("📷 USB 카메라 준비 완료")
        else:
            print("❌ USB 카메라 인식 실패")

    def detect_face(self):
        ret, frame = self.cap.read()
        if not ret:
            return False, 0.0, 0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)

        distance = self.distance_sensor.distance * 100
        self.current_distance = distance
        self.face_detected = len(faces) > 0

        # 얼굴 있으면 접근
        if self.face_detected and not self.is_moving:
            self.forward()
            self.set_speed(40)
            self.is_moving = True

        # 얼굴 없으면 정지
        if not self.face_detected and self.is_moving:
            self.stop()
            self.is_moving = False

        return self.face_detected, distance, len(faces)

    # ==============================
    # 모터 제어
    # ==============================
    def forward(self):
        GPIO.output(self.left_in3, GPIO.HIGH)
        GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.HIGH)
        GPIO.output(self.right_in4, GPIO.LOW)

    def backward(self):
        GPIO.output(self.left_in3, GPIO.LOW)
        GPIO.output(self.left_in4, GPIO.HIGH)
        GPIO.output(self.right_in3, GPIO.LOW)
        GPIO.output(self.right_in4, GPIO.HIGH)

    def left_turn(self):
        GPIO.output(self.left_in3, GPIO.LOW)
        GPIO.output(self.left_in4, GPIO.HIGH)
        GPIO.output(self.right_in3, GPIO.HIGH)
        GPIO.output(self.right_in4, GPIO.LOW)

    def right_turn(self):
        GPIO.output(self.left_in3, GPIO.HIGH)
        GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.LOW)
        GPIO.output(self.right_in4, GPIO.HIGH)

    def stop(self):
        GPIO.output(self.left_in3, GPIO.LOW)
        GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.LOW)
        GPIO.output(self.right_in4, GPIO.LOW)
        self.left_pwm.ChangeDutyCycle(0)
        self.right_pwm.ChangeDutyCycle(0)

    def set_speed(self, speed: int):
        speed = max(0, min(100, speed))
        self.current_speed = speed
        self.left_pwm.ChangeDutyCycle(speed)
        self.right_pwm.ChangeDutyCycle(speed)

    # ==============================
    # 종료 정리
    # ==============================
    def cleanup(self):
        print("🧹 하드웨어 정리 중...")
        self.stop()
        if self.cap:
            self.cap.release()
        self.left_pwm.stop()
        self.right_pwm.stop()
        cv2.destroyAllWindows()
        GPIO.cleanup()