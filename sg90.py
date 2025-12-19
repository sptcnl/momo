import RPi.GPIO as GPIO
from time import sleep
import math

GPIO.setmode(GPIO.BCM)
servo_pin = 12
GPIO.setup(servo_pin, GPIO.OUT) 
servo = GPIO.PWM(servo_pin, 50)
servo.start(0)

servo_min_duty = 3
servo_max_duty = 12

def set_servo_degree(degree):
    if degree > 180:
        degree = 180
    elif degree < 0:
        degree = 0
    duty = servo_min_duty + (degree * (servo_max_duty - servo_min_duty) / 180.0)
    servo.ChangeDutyCycle(duty)
    sleep(0.02)  # 부드러운 움직임을 위한 작은 딜레이

def tail_wag():
    """개 꼬리 흔들기 패턴: 좌우 빠르게 흔들기"""
    wag_count = 0
    while wag_count < 10:  # 10회 반복
        # 왼쪽으로 흔들기 (빠르게)
        for degree in range(60, 120, 4):  # 60도에서 120도로 4도씩 증가
            set_servo_degree(degree)
        for degree in range(120, 60, -4):  # 120도에서 60도로 4도씩 감소
            set_servo_degree(degree)
        
        # 오른쪽으로 흔들기 (반대 방향)
        for degree in range(120, 60, -4):
            set_servo_degree(degree)
        for degree in range(60, 120, 4):
            set_servo_degree(degree)
        
        wag_count += 1

def excited_tail_wag():
    """신난 꼬리 흔들기: 더 빠르고 크게"""
    wag_count = 0
    while wag_count < 15:
        # 큰 진폭으로 빠르게 흔들기
        for degree in range(45, 135, 6):
            set_servo_degree(degree)
        for degree in range(135, 45, -6):
            set_servo_degree(degree)
        wag_count += 1

try:
    print("꼬리 흔들기 시작! (Ctrl+C로 종료)")
    print("1: 기본 꼬리 흔들기")
    print("2: 신난 꼬리 흔들기")
    print("0: 정지")
    
    while True:
        cmd = input("명령어 입력 (1,2,0): ")
        
        if cmd == '1':
            print("기본 꼬리 흔들기 실행")
            tail_wag()
            
        elif cmd == '2':
            print("신난 꼬리 흔들기 실행!")
            excited_tail_wag()
            
        elif cmd == '0':
            set_servo_degree(90)  # 중립 위치
            print("꼬리 정지")
            
        else:
            print("명령어: 1(기본), 2(신남), 0(정지)")

except KeyboardInterrupt:
    print("\n프로그램 종료")
finally:
    servo.ChangeDutyCycle(0)
    servo.stop()
    GPIO.cleanup()
    print("GPIO 정리 완료")