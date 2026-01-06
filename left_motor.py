from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

AIN1_1 = 16
AIN2_1 = 18
PWMA_1 = 12
STBY = 22

GPIO.setup(AIN1_1, GPIO.OUT)
GPIO.setup(AIN2_1, GPIO.OUT)
GPIO.setup(PWMA_1, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

pwm1 = GPIO.PWM(PWMA_1, 1000)
pwm1.start(0)

try:
    GPIO.output(STBY, GPIO.HIGH)    # 드라이버 활성화
    GPIO.output(AIN1_1, GPIO.HIGH)  # 정방향
    GPIO.output(AIN2_1, GPIO.LOW)
    pwm1.ChangeDutyCycle(70)        # 70% 속도
    sleep(3)
finally:
    pwm1.ChangeDutyCycle(0)
    GPIO.output(STBY, GPIO.LOW)
    GPIO.cleanup()