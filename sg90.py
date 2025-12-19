import RPi.GPIO as GPIO
from time import sleep
import threading
import sys

GPIO.setmode(GPIO.BCM)
servo_pin = 12
GPIO.setup(servo_pin, GPIO.OUT) 
servo = GPIO.PWM(servo_pin, 50)
servo.start(0)

servo_min_duty = 3
servo_max_duty = 12

running = False
tail_thread = None

def set_servo_degree(degree):
    if degree > 180: degree = 180
    elif degree < 0: degree = 0
    duty = servo_min_duty + (degree * (servo_max_duty - servo_min_duty) / 180.0)
    servo.ChangeDutyCycle(duty)
    sleep(0.015)  # 더 빠르게

def tail_wag_loop():
    """별도 스레드에서 꼬리 흔들기"""
    global running
    while running:
        # 좌우 빠른 흔들기
        for deg in range(60, 120, 5):
            if not running: break
            set_servo_degree(deg)
        for deg in range(120, 60, -5):
            if not running: break
            set_servo_degree(deg)

def stop_tail():
    """꼬리 즉시 정지"""
    global running, tail_thread
    running = False
    if tail_thread and tail_thread.is_alive():
        tail_thread.join(timeout=0.1)  # 스레드 종료 대기
    set_servo_degree(90)

try:
    print("명령어: 1(시작), 0(정지), e(종료)")
    while True:
        cmd = input("명령어: ").strip()
        
        if cmd == '1' and not running:
            running = True
            tail_thread = threading.Thread(target=tail_wag_loop, daemon=True)
            tail_thread.start()
            print("🐕 꼬리 흔들기 시작!")
            
        elif cmd == '0':
            stop_tail()
            print("🛑 꼬리 정지!")
            
        elif cmd == 'e':
            stop_tail()
            break
            
        else:
            print("1(시작), 0(정지), e(종료)")
            
except KeyboardInterrupt:
    print("\nCtrl+C 종료")
finally:
    stop_tail()
    servo.ChangeDutyCycle(0)
    servo.stop()
    GPIO.cleanup()