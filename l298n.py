import RPi.GPIO as GPIO
from time import sleep

# 왼쪽 모터드라이버 (L298N A)
left_in1 = 24
left_in2 = 23
left_ena = 25

# 오른쪽 모터드라이버 (L298N B)  
right_in3 = 18
right_in4 = 17
right_enb = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(left_in1, GPIO.OUT)
GPIO.setup(left_in2, GPIO.OUT)
GPIO.setup(left_ena, GPIO.OUT)
GPIO.setup(right_in3, GPIO.OUT)
GPIO.setup(right_in4, GPIO.OUT)
GPIO.setup(right_enb, GPIO.OUT)

# 초기 정지
GPIO.output(left_in1, GPIO.LOW)
GPIO.output(left_in2, GPIO.LOW)
GPIO.output(right_in3, GPIO.LOW)
GPIO.output(right_in4, GPIO.LOW)

left_pwm = GPIO.PWM(left_ena, 1000)
right_pwm = GPIO.PWM(right_enb, 1000)
left_pwm.start(0)
right_pwm.start(0)

print("로봇 자동차 제어 (별도 L298N 드라이버)")
print("w-전진 s-후진 a-좌회전 d-우회전")
print("l-저속 m-중속 h-고속 스페이스-정지 e-종료")
print("\n")

def motor_forward(speed=50):
    GPIO.output(left_in1, GPIO.HIGH)
    GPIO.output(left_in2, GPIO.LOW)
    GPIO.output(right_in3, GPIO.HIGH)
    GPIO.output(right_in4, GPIO.LOW)
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

def motor_backward(speed=50):
    GPIO.output(left_in1, GPIO.LOW)
    GPIO.output(left_in2, GPIO.HIGH)
    GPIO.output(right_in3, GPIO.LOW)
    GPIO.output(right_in4, GPIO.HIGH)
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

def motor_left(speed=60):
    GPIO.output(left_in1, GPIO.LOW)
    GPIO.output(left_in2, GPIO.HIGH)  # 왼쪽 후진
    GPIO.output(right_in3, GPIO.HIGH)
    GPIO.output(right_in4, GPIO.LOW)  # 오른쪽 전진
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

def motor_right(speed=60):
    GPIO.output(left_in1, GPIO.HIGH)
    GPIO.output(left_in2, GPIO.LOW)   # 왼쪽 전진
    GPIO.output(right_in3, GPIO.LOW)
    GPIO.output(right_in4, GPIO.HIGH) # 오른쪽 후진
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

def motor_stop():
    GPIO.output(left_in1, GPIO.LOW)
    GPIO.output(left_in2, GPIO.LOW)
    GPIO.output(right_in3, GPIO.LOW)
    GPIO.output(right_in4, GPIO.LOW)
    left_pwm.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(0)

def set_speed(speed):
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

try:
    while True:
        cmd = input().lower()
        
        if cmd == 'f':  # 전진
            print("전진")
            motor_forward(50)
            
        elif cmd == 'b':  # 후진
            print("후진")
            motor_backward(50)
            
        elif cmd == 'a':  # 좌회전
            print("좌회전")
            motor_left(60)
            
        elif cmd == 'd':  # 우회전
            print("우회전")
            motor_right(60)
            
        elif cmd == 'l':  # 저속
            print("저속")
            set_speed(30)
            
        elif cmd == 'm':  # 중속
            print("중속")
            set_speed(50)
            
        elif cmd == 'h':  # 고속
            print("고속")
            set_speed(80)
            
        elif cmd == 's':  # 정지
            print("정지")
            motor_stop()
            
        elif cmd == 'e':  # 종료
            print("종료")
            break
            
        else:
            print("명령어: f,b,a,d,l,m,h,s,e")
            
except KeyboardInterrupt:
    pass
finally:
    motor_stop()
    left_pwm.stop()
    right_pwm.stop()
    GPIO.cleanup()
    print("GPIO 정리 완료")