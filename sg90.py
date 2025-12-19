import RPi.GPIO as GPIO
from time import sleep

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
    sleep(0.02)

running = False  # 꼬리 동작 상태

def tail_wag_continuous():
    """무한 꼬리 흔들기"""
    global running
    print("꼬리 흔들기 시작! (0 또는 Ctrl+C로 멈춤)")
    while running:
        # 빠른 좌우 흔들기
        for degree in range(60, 120, 5):
            if not running: break
            set_servo_degree(degree)
        if not running: break
        for degree in range(120, 60, -5):
            if not running: break
            set_servo_degree(degree)
        if not running: break

try:
    print("명령어: 1(시작), 0(정지), e(종료)")
    while True:
        cmd = input("명령어 입력: ").strip()
        
        if cmd == '1':
            if not running:
                running = True
                tail_wag_continuous()  # 새 스레드 없이 순차 실행
                
        elif cmd == '0':
            running = False
            set_servo_degree(90)  # 중립 위치
            print("꼬리 정지!")
            
        elif cmd == 'e':
            running = False
            break
            
        else:
            print("명령어: 1(시작), 0(정지), e(종료)")

except KeyboardInterrupt:
    print("\nCtrl+C로 종료")
finally:
    running = False
    set_servo_degree(90)
    servo.ChangeDutyCycle(0)
    servo.stop()
    GPIO.cleanup()
    print("GPIO 정리 완료")