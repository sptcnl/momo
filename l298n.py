import RPi.GPIO as GPIO
from time import sleep

# 왼쪽 모터드라이버
left_in3 = 24
left_in4 = 23
left_ena = 25

# 오른쪽 모터드라이버
right_in3 = 18
right_in4 = 17
right_enb = 34

GPIO.setmode(GPIO.BCM)

# 핀 설정
GPIO.setup(left_in3, GPIO.OUT)
GPIO.setup(left_in4, GPIO.OUT)
GPIO.setup(left_ena, GPIO.OUT)
GPIO.setup(right_in3, GPIO.OUT)
GPIO.setup(right_in4, GPIO.OUT)
GPIO.setup(right_enb, GPIO.OUT)

# 초기 정지
GPIO.output(left_in3, GPIO.LOW)
GPIO.output(left_in4, GPIO.LOW)
GPIO.output(right_in3, GPIO.LOW)
GPIO.output(right_in4, GPIO.LOW)

# PWM 생성
left_pwm = GPIO.PWM(left_ena, 1000)
right_pwm = GPIO.PWM(right_enb, 1000)
left_pwm.start(0)
right_pwm.start(0)

print("로봇 자동차 제어")
print("f-전진 b-후진 a-좌회전 d-우회전")
print("l-저속 m-중속 h-고속 s-정지 e-종료")
print("\n")

def forward():
    GPIO.output(left_in3, GPIO.HIGH)
    GPIO.output(left_in4, GPIO.LOW)
    GPIO.output(right_in3, GPIO.HIGH)
    GPIO.output(right_in4, GPIO.LOW)

def backward():
    GPIO.output(left_in3, GPIO.LOW)
    GPIO.output(left_in4, GPIO.HIGH)
    GPIO.output(right_in3, GPIO.LOW)
    GPIO.output(right_in4, GPIO.HIGH)

def left_turn():
    GPIO.output(left_in3, GPIO.LOW)
    GPIO.output(left_in4, GPIO.HIGH)
    GPIO.output(right_in3, GPIO.HIGH)
    GPIO.output(right_in4, GPIO.LOW)

def right_turn():
    GPIO.output(left_in3, GPIO.HIGH)
    GPIO.output(left_in4, GPIO.LOW)
    GPIO.output(right_in3, GPIO.LOW)
    GPIO.output(right_in4, GPIO.HIGH)

def stop():
    GPIO.output(left_in3, GPIO.LOW)
    GPIO.output(left_in4, GPIO.LOW)
    GPIO.output(right_in3, GPIO.LOW)
    GPIO.output(right_in4, GPIO.LOW)
    left_pwm.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(0)

def set_speed(speed):
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

try:
    while True:
        cmd = input().lower().strip()
        
        if cmd == 'f':  # 전진
            print("전진")
            forward()
            set_speed(50)
        elif cmd == 'b':  # 후진
            print("후진")
            backward()
            set_speed(50)
        elif cmd == 'a':  # 좌회전
            print("좌회전")
            left_turn()
            set_speed(60)
        elif cmd == 'd':  # 우회전
            print("우회전")
            right_turn()
            set_speed(60)
        elif cmd == 'l':
            print("저속")
            set_speed(30)
        elif cmd == 'm':
            print("중속")
            set_speed(50)
        elif cmd == 'h':
            print("고속")
            set_speed(80)
        elif cmd == 's':  # 정지
            print("정지")
            stop()
        elif cmd == 'e':
            print("종료")
            break
        else:
            print("명령어: f,b,a,d,l,m,h,s,e")
            
except KeyboardInterrupt:
    print("\n중단")
finally:
    stop()
    left_pwm.stop()
    right_pwm.stop()
    GPIO.cleanup()
    print("GPIO 정리 완료")