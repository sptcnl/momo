#!/usr/bin/env python3
"""
TB6612FNG 듀얼 모터 드라이버 바퀴 테스트 코드
Raspberry Pi BOARD 핀 번호 그대로 사용
핀 구성: PWMA=12, AIN1=16, AIN2=18, STBY=22, BIN1=15, BIN2=29, PWMB=11
"""

from time import sleep
import RPi.GPIO as GPIO
import signal
import sys

# GPIO 설정 (BOARD 모드 - 물리적 핀 번호)
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# 핀 정의 (기존 코드 그대로)
PWMA = 12    # 모터 A PWM
AIN1 = 16    # 모터 A 방향1
AIN2 = 18    # 모터 A 방향2
STBY = 22    # Standby (드라이버 활성화)
BIN1 = 15    # 모터 B 방향1
BIN2 = 29    # 모터 B 방향2
PWMB = 11    # 모터 B PWM

# PWM 설정
PWM_FREQ = 1000  # 1kHz (더 부드러운 제어)
pwma = None
pwmb = None

class TB6612FNG:
    def __init__(self):
        self.setup_gpio()
    
    def setup_gpio(self):
        """GPIO 핀 초기화"""
        GPIO.setup(PWMA, GPIO.OUT)
        GPIO.setup(AIN1, GPIO.OUT)
        GPIO.setup(AIN2, GPIO.OUT)
        GPIO.setup(STBY, GPIO.OUT)
        GPIO.setup(BIN1, GPIO.OUT)
        GPIO.setup(BIN2, GPIO.OUT)
        GPIO.setup(PWMB, GPIO.OUT)
        
        # PWM 객체 생성 및 시작 (0% duty cycle)
        global pwma, pwmb
        pwma = GPIO.PWM(PWMA, PWM_FREQ)
        pwmb = GPIO.PWM(PWMB, PWM_FREQ)
        pwma.start(0)
        pwmb.start(0)
        
        # STBY 비활성화 (초기 정지 상태)
        GPIO.output(STBY, GPIO.LOW)
    
    def set_motor(self, motor, speed, direction):
        """
        단일 모터 제어
        motor: 0=왼쪽(A), 1=오른쪽(B)
        speed: 0~100 (PWM 듀티사이클)
        direction: 0=정방향, 1=역방향
        """
        if speed < 0 or speed > 100:
            speed = max(0, min(100, speed))
        
        # STBY 활성화
        GPIO.output(STBY, GPIO.HIGH)
        
        if motor == 0:  # 왼쪽 모터 (A)
            if direction == 0:  # 정방향
                GPIO.output(AIN1, GPIO.HIGH)
                GPIO.output(AIN2, GPIO.LOW)
            else:  # 역방향
                GPIO.output(AIN1, GPIO.LOW)
                GPIO.output(AIN2, GPIO.HIGH)
            pwma.ChangeDutyCycle(speed)
            
        elif motor == 1:  # 오른쪽 모터 (B)
            if direction == 0:  # 정방향
                GPIO.output(BIN1, GPIO.HIGH)
                GPIO.output(BIN2, GPIO.LOW)
            else:  # 역방향
                GPIO.output(BIN1, GPIO.LOW)
                GPIO.output(BIN2, GPIO.HIGH)
            pwmb.ChangeDutyCycle(speed)
    
    def forward(self, speed=70):
        """전진"""
        self.set_motor(0, speed, 0)
        self.set_motor(1, speed, 0)
    
    def backward(self, speed=70):
        """후진"""
        self.set_motor(0, speed, 1)
        self.set_motor(1, speed, 1)
    
    def left(self, speed=70):
        """좌회전 (왼쪽 느리게/역방향)"""
        self.set_motor(0, speed*0.3, 0)  # 왼쪽 천천히
        self.set_motor(1, speed, 0)       # 오른쪽 빠르게
    
    def right(self, speed=70):
        """우회전 (오른쪽 느리게/역방향)"""
        self.set_motor(0, speed, 0)       # 왼쪽 빠르게
        self.set_motor(1, speed*0.3, 0)   # 오른쪽 천천히
    
    def spin_left(self, speed=60):
        """제자리 좌회전"""
        self.set_motor(0, speed, 1)  # 왼쪽 후진
        self.set_motor(1, speed, 0)  # 오른쪽 전진
    
    def spin_right(self, speed=60):
        """제자리 우회전"""
        self.set_motor(0, speed, 0)  # 왼쪽 전진
        self.set_motor(1, speed, 1)  # 오른쪽 후진
    
    def stop(self):
        """정지 (STBY 끄기)"""
        pwma.ChangeDutyCycle(0)
        pwmb.ChangeDutyCycle(0)
        GPIO.output(STBY, GPIO.LOW)
    
    def cleanup(self):
        """GPIO 정리"""
        self.stop()
        GPIO.cleanup()

def signal_handler(sig, frame):
    """Ctrl+C 처리"""
    print("\n\n🛑 테스트 종료! GPIO 정리 중...")
    motor.cleanup()
    sys.exit(0)

def wheel_test_sequence():
    """바퀴 테스트 시퀀스"""
    print("🚗 TB6612FNG 바퀴 테스트 시작!")
    print("종료하려면 Ctrl+C")
    
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
    # Ctrl+C 신호 처리 등록
    signal.signal(signal.SIGINT, signal_handler)
    
    wheel_test_sequence()