import cv2
from gpiozero import DistanceSensor
import RPi.GPIO as GPIO
from time import sleep
import numpy as np
import sounddevice as sd
import soundfile as sf
import wave
from piper import PiperVoice
import subprocess
import os
import time

# GPIO 핀 설정 (모터 드라이버) - 초음파 핀 충돌 해결
left_in3 = 24
left_in4 = 23
left_ena = 25
right_in3 = 18
right_in4 = 17
right_enb = 27
ECHO_PIN = 21   # 초음파 에코 핀
TRIG_PIN = 4    # 초음파 트리거 핀

GPIO.setmode(GPIO.BCM)
GPIO.setup(left_in3, GPIO.OUT)
GPIO.setup(left_in4, GPIO.OUT)
GPIO.setup(left_ena, GPIO.OUT)
GPIO.setup(right_in3, GPIO.OUT)
GPIO.setup(right_in4, GPIO.OUT)
GPIO.setup(right_enb, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(TRIG_PIN, GPIO.OUT)

# PWM 생성
left_pwm = GPIO.PWM(left_ena, 1000)
right_pwm = GPIO.PWM(right_enb, 1000)
left_pwm.start(0)
right_pwm.start(0)

# 초음파 센서
distanceSensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)

# Piper TTS 초기화 (한 번만 로드)
print("🤖 음성 모델 로딩 중...")
voice = PiperVoice.load("en_US-lessac-medium.onnx")
print("✅ TTS 준비 완료!")

def tts_speak(text: str):
    """TTS 음성 출력"""
    try:
        wav_path = "/tmp/robot_speak.wav"
        with wave.open(wav_path, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        subprocess.run(["aplay", wav_path], check=True)
        os.remove(wav_path)  # 임시 파일 삭제
        return True
    except Exception as e:
        print(f"TTS 오류: {e}")
        return False

# 카메라 및 얼굴 감지 초기화
cascade_path = "/home/sptcnl/haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)  # Haar Cascade 로드[web:12][web:17]

# USB 카메라 초기화
cam_index = 0  # 필요시 1, 2로 변경
cap = cv2.VideoCapture(cam_index)  # USB 웹캠은 일반적으로 VideoCapture(0) 사용[web:2][web:7]
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    raise RuntimeError("USB 카메라를 열 수 없습니다. cam_index 또는 /dev/video* 를 확인하세요.")

# 상태 변수
last_speak_time = 0
SPEAK_COOLDOWN = 3.0  # 3초 쿨다운

# 모터 제어 함수들
def forward(speed=50):
    GPIO.output(left_in3, GPIO.HIGH)
    GPIO.output(left_in4, GPIO.LOW)
    GPIO.output(right_in3, GPIO.HIGH)
    GPIO.output(right_in4, GPIO.LOW)
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

def stop():
    GPIO.output(left_in3, GPIO.LOW)
    GPIO.output(left_in4, GPIO.LOW)
    GPIO.output(right_in3, GPIO.LOW)
    GPIO.output(right_in4, GPIO.LOW)
    left_pwm.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(0)

def left_turn(speed=60):
    GPIO.output(left_in3, GPIO.LOW)
    GPIO.output(left_in4, GPIO.HIGH)
    GPIO.output(right_in3, GPIO.HIGH)
    GPIO.output(right_in4, GPIO.LOW)
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

def right_turn(speed=60):
    GPIO.output(left_in3, GPIO.HIGH)
    GPIO.output(left_in4, GPIO.LOW)
    GPIO.output(right_in3, GPIO.LOW)
    GPIO.output(right_in4, GPIO.HIGH)
    left_pwm.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)

try:
    print("🚀 얼굴 추적 + TTS 반려로봇 시작 (ESC로 종료)")
    tts_speak("안녕하세요! 얼굴을 찾아서 따라갈게요!")
    
    while True:
        current_time = time.time()
        
        # 거리 측정
        distance_cm = distanceSensor.distance * 100
        print(f"거리: {distance_cm:5.1f}cm", end='\r')
        
        # 카메라 프레임 (USB 카메라)
        ret, frame = cap.read()
        if not ret:
            print("카메라 프레임을 읽지 못했습니다.")
            continue
        
        # USB 카메라는 기본이 BGR 포맷
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 얼굴 감지
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
        
        if len(faces) > 0:
            # 가장 큰 얼굴 선택
            (x, y, w, h) = max(faces, key=lambda rect: rect[2] * rect[3])
            face_center_x = x + w // 2
            frame_center_x = frame.shape[1] // 2
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (face_center_x, y + h//2), 5, (0, 0, 255), -1)
            
            error_x = face_center_x - frame_center_x
            print(f" | 얼굴: {error_x:+3d}px | ", end='')
            
            # TTS 발화 조건 (쿨다운 확인)
            if current_time - last_speak_time > SPEAK_COOLDOWN:
                if distance_cm > 150:
                    tts_speak("더 가까이 오세요!")
                    last_speak_time = current_time
                elif 100 < distance_cm <= 150:
                    tts_speak("따라갈게요!")
                    last_speak_time = current_time
            
            # 거리 100cm 이상이고 얼굴이 감지되면 추적
            if distance_cm > 100:
                if abs(error_x) < 50:  # 중앙
                    forward(40)
                    status = "전진"
                elif error_x < -50:  # 왼쪽 (우회전)
                    right_turn(50)
                    status = "우회전"
                else:  # 오른쪽 (좌회전)
                    left_turn(50)
                    status = "좌회전"
            else:
                stop()
                status = "가까움(정지)"
                if current_time - last_speak_time > SPEAK_COOLDOWN:
                    tts_speak("너무 가까워요! 멈췄어요!")
                    last_speak_time = current_time
        else:
            stop()
            status = "얼굴없음"
            print(" | 얼굴 없음        ", end='\r')
        
        # 상태 표시
        cv2.putText(frame, f"Dist: {distance_cm:.0f}cm", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, status, (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow("🤖 Face Tracking + TTS Robot", frame)
        
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break
            
        sleep(0.05)

except KeyboardInterrupt:
    print("\n⏹️  수동 중단")

finally:
    stop()
    if 'cap' in locals():
        cap.release()
    cv2.destroyAllWindows()
    left_pwm.stop()
    right_pwm.stop()
    GPIO.cleanup()
    print("✅ 모든 리소스 정리 완료")