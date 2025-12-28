import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

# 모터1
AIN1_1 = 5
AIN2_1 = 6
PWMA_1 = 12

# 모터2
AIN1_2 = 16
AIN2_2 = 20
PWMA_2 = 13

STBY = 25

pins = [AIN1_1, AIN2_1, PWMA_1, AIN1_2, AIN2_2, PWMA_2, STBY]
for p in pins:
    GPIO.setup(p, GPIO.OUT)

GPIO.output(STBY, GPIO.HIGH)

pwm1 = GPIO.PWM(PWMA_1, 1000)
pwm2 = GPIO.PWM(PWMA_2, 1000)
pwm1.start(0)
pwm2.start(0)

# 모터1 정방향
GPIO.output(AIN1_1, GPIO.HIGH)
GPIO.output(AIN2_1, GPIO.LOW)
pwm1.ChangeDutyCycle(70)

# 모터2 역방향
GPIO.output(AIN1_2, GPIO.LOW)
GPIO.output(AIN2_2, GPIO.HIGH)
pwm2.ChangeDutyCycle(40)

sleep(3)

GPIO.cleanup()