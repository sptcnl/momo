#!/usr/bin/env python3
"""
TB6612FNG 듀얼 모터 드라이버 바퀴 테스트 코드
모터1 → (AIN1_1=16, AIN2_1=18, PWMA_1=12)
모터2 → (AIN1_2=15, AIN2_2=29, PWMA_2=11)
STBY=22
"""

from time import sleep
import RPi.GPIO as GPIO
import signal
import sys

# GPIO 설정 (BOARD 모드)
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# 핀 정의 (기존 번호 그대로)
AIN1_1 = 16   # 모터1 방향1
AIN2_1 = 18   # 모터1 방향2
PWMA_1 = 12   # 모터1 PWM

AIN1_2 = 15   # 모터2 방향1
AIN2_2 = 29   # 모터2 방향2
PWMA_2 = 11   # 모터2 PWM

STBY = 22     # Standby

PWM_FREQ = 1000  # 1kHz
pwma_1 = None
pwma_2 = None


class TB6612FNG:
    def __init__(self):
        self.setup_gpio()

    def setup_gpio(self):
        """GPIO 핀 초기화"""
        GPIO.setup(AIN1_1, GPIO.OUT)
        GPIO.setup(AIN2_1, GPIO.OUT)
        GPIO.setup(PWMA_1, GPIO.OUT)
        GPIO.setup(AIN1_2, GPIO.OUT)
        GPIO.setup(AIN2_2, GPIO.OUT)
        GPIO.setup(PWMA_2, GPIO.OUT)
        GPIO.setup(STBY, GPIO.OUT)

        global pwma_1, pwma_2
        pwma_1 = GPIO.PWM(PWMA_1, PWM_FREQ)
        pwma_2 = GPIO.PWM(PWMA_2, PWM_FREQ)
        pwma_1.start(0)
        pwma_2.start(0)
        GPIO.output(STBY, GPIO.LOW)

    def set_motor(self, motor, speed, direction):
        """motor: 0=모터1, 1=모터2"""
        speed = max(0, min(100, speed))
        GPIO.output(STBY, GPIO.HIGH)

        if motor == 0:
            if direction == 0:
                GPIO.output(AIN1_1, GPIO.HIGH)
                GPIO.output(AIN2_1, GPIO.LOW)
            else:
                GPIO.output(AIN1_1, GPIO.LOW)
                GPIO.output(AIN2_1, GPIO.HIGH)
            pwma_1.ChangeDutyCycle(speed)

        elif motor == 1:
            if direction == 0:
                GPIO.output(AIN1_2, GPIO.HIGH)
                GPIO.output(AIN2_2, GPIO.LOW)
            else:
                GPIO.output(AIN1_2, GPIO.LOW)
                GPIO.output(AIN2_2, GPIO.HIGH)
            pwma_2.ChangeDutyCycle(speed)

    def forward(self, speed=70):
        self.set_motor(0, speed, 0)
        self.set_motor(1, speed, 0)

    def backward(self, speed=70):
        self.set_motor(0, speed, 1)
        self.set_motor(1, speed, 1)

    def left(self, speed=70):
        self.set_motor(0, speed * 0.3, 0)
        self.set_motor(1, speed, 0)

    def right(self, speed=70):
        self.set_motor(0, speed, 0)
        self.set_motor(1, speed * 0.3, 0)

    def spin_left(self, speed=60):
        self.set_motor(0, speed, 1)
        self.set_motor(1, speed, 0)

    def spin_right(self, speed=60):
        self.set_motor(0, speed, 0)
        self.set_motor(1, speed, 1)

    def stop(self):
        pwma_1.ChangeDutyCycle(0)
        pwma_2.ChangeDutyCycle(0)
        GPIO.output(STBY, GPIO.LOW)

    def cleanup(self):
        self.stop()
        GPIO.cleanup()


def signal_handler(sig, frame):
    print("\n\n🛑 테스트 종료! GPIO 정리 중...")
    motor.cleanup()
    sys.exit(0)


def wheel_test_sequence():
    """바퀴 테스트 시퀀스"""
    print("🚗 TB6612FNG 바퀴 테스트 시작! 종료하려면 Ctrl+C")

    global motor
    motor = TB6612FNG()

    try:
        while True:
            print("\n📤 전진 (2초)")
            motor.forward(70)
            sleep(2)

            print("🛑 정지 (0.5초)")
            motor.stop()
            sleep(0.5)

            print("📤 후진 (2초)")
            motor.backward(70)
            sleep(2)

            print("🛑 정지 (0.5초)")
            motor.stop()
            sleep(0.5)

            print("🔄 좌회전 (2초)")
            motor.left(60)
            sleep(2)

            print("🛑 정지 (0.5초)")
            motor.stop()
            sleep(0.5)

            print("🔄 우회전 (2초)")
            motor.right(60)
            sleep(2)

            print("🛑 정지 (1초)")
            motor.stop()
            sleep(1)

            print("⚡ 제자리 좌회전 (1.5초)")
            motor.spin_left(50)
            sleep(1.5)
            motor.stop()
            sleep(0.3)

            print("⚡ 제자리 우회전 (1.5초)")
            motor.spin_right(50)
            sleep(1.5)
            motor.stop()
            sleep(1)

            print("-" * 40)

    except KeyboardInterrupt:
        pass
    finally:
        motor.cleanup()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    wheel_test_sequence()