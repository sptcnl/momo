import cv2
from picamera2 import Picamera2
from gpiozero import DistanceSensor
from time import sleep
import numpy as np
import wave
from piper import PiperVoice
import subprocess
import os
import time
import l298n  # l298n.py import (함수들 직접 사용)

# 초음파 센서 (l298n.py의 right_in4=17과 충돌 → 핀 변경 필요)
distanceSensor = DistanceSensor(echo=22, trigger=5)  # echo/trigger 핀 변경 추천

# Piper TTS 초기화
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
        os.remove(wav_path)
        return True
    except Exception as e:
        print(f"TTS 오류: {e}")
        return False

# 카메라 및 얼굴 감지 초기화
cascade_path = "/home/sptcnl/haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()

# 상태 변수
last_speak_time = 0
SPEAK_COOLDOWN = 3.0

# l298n.py 함수들 직접 호출 (import 후 바로 사용 가능)
try:
    print("🚀 얼굴 추적 + TTS 반려로봇 시작 (ESC로 종료)")
    tts_speak("안녕하세요! 얼굴을 찾아서 따라갈게요!")
    
    while True:
        current_time = time.time()
        
        # 거리 측정
        distance_cm = distanceSensor.distance * 100
        print(f"거리: {distance_cm:5.1f}cm", end='\r')
        
        # 카메라 프레임
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
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
            
            # TTS 발화 조건
            if current_time - last_speak_time > SPEAK_COOLDOWN:
                if distance_cm > 150:
                    tts_speak("더 가까이 오세요!")
                    last_speak_time = current_time
                elif 100 < distance_cm <= 150:
                    tts_speak("따라갈게요!")
                    last_speak_time = current_time
            
            # 거리 100cm 이상이고 얼굴이 감지되면 l298n 함수 호출
            if distance_cm > 100:
                if abs(error_x) < 50:  # 중앙 - 전진
                    l298n.forward()
                    l298n.set_speed(40)
                    status = "전진"
                elif error_x < -50:  # 왼쪽 - 우회전
                    l298n.right_turn()
                    l298n.set_speed(50)
                    status = "우회전"
                else:  # 오른쪽 - 좌회전
                    l298n.left_turn()
                    l298n.set_speed(50)
                    status = "좌회전"
            else:
                l298n.stop()
                status = "가까움(정지)"
                if current_time - last_speak_time > SPEAK_COOLDOWN:
                    tts_speak("너무 가까워요! 멈췄어요!")
                    last_speak_time = current_time
        else:
            l298n.stop()
            status = "얼굴없음"
            print(" | 얼굴 없음        ", end='\r')
        
        # 상태 표시
        cv2.putText(frame, f"Dist: {distance_cm:.0f}cm", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, status, (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow("🤖 Face Tracking + TTS Robot", frame)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break
            
        sleep(0.05)

except KeyboardInterrupt:
    print("\n⏹️  수동 중단")

finally:
    l298n.stop()
    # l298n.py의 cleanup 부분 실행
    import RPi.GPIO as GPIO
    GPIO.cleanup()
    picam2.stop()
    cv2.destroyAllWindows()
    print("✅ 모든 리소스 정리 완료")