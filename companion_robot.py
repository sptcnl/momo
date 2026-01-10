#!/usr/bin/env python3
"""
BitNet b1.58 반려로봇 - Raspberry Pi 최적화 완전 버전
fswebcam 얼굴감지 + 꼬리서보 + 음성인식(STT) + 감정분석 + TTS + 1-bit LLM
"""

import cv2
from face_emotion import get_current_emotion  # fswebcam 버전
from stt_whispercpp import stt_from_mic
from tts_piper import tts_play
import time
import threading
import RPi.GPIO as GPIO
import gc  # 메모리 관리용
import subprocess
import os
import sys

# BitNet 공식 바이너리 호출 (Python 바인딩 대신 안정적)
BITNET_MODEL_PATH = "/home/sptcnl/models/BitNet-b1.58-2B/ggml-model-i2_s.gguf"
BITNET_BINARY = "/home/sptcnl/BitNet/run_inference"
LLM_AVAILABLE = (
    os.path.exists(BITNET_MODEL_PATH) and 
    os.path.exists(BITNET_BINARY) and 
    os.access(BITNET_BINARY, os.X_OK)
)

print(f"🔍 BitNet 상태: 모델={os.path.exists(BITNET_MODEL_PATH)}, 바이너리={os.path.exists(BITNET_BINARY)}")
if LLM_AVAILABLE:
    print("✅ BitNet b1.58-2B I2_S 로드 완료! (ARM 최적화, ~800MB, 3-5 t/s)")
else:
    print("⚠️ BitNet Fallback 모드 (규칙 기반 응답)")

# GPIO 서보 설정
GPIO.setmode(GPIO.BCM)
servo_pin = 12
GPIO.setup(servo_pin, GPIO.OUT) 
servo = GPIO.PWM(servo_pin, 50)
servo.start(0)
servo_min_duty = 3
servo_max_duty = 12

class RobotHardware:
    def __init__(self):
        self.cascade_path = "/home/sptcnl/haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        self.face_detected = False
        self.running = False
        self.tail_running = False
        self.tail_thread = None
        
    def start_camera(self):
        """fswebcam 카메라 테스트"""
        test_img = self.capture_face_image()
        if test_img:
            print("📷 fswebcam USB 카메라 연결 성공!")
            os.unlink(test_img)
        else:
            print("❌ fswebcam 카메라 연결 실패! (sudo apt install fswebcam)")
    
    def capture_face_image(self):
        """fswebcam 단일 이미지 캡처"""
        temp_file = f"/tmp/webcam_face_{int(time.time())}.jpg"
        cmd = [
            "fswebcam", "--resolution", "640x480",
            "--no-banner", "--save", temp_file
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=3)
            return temp_file if os.path.exists(temp_file) else None
        except:
            return None
    
    def set_servo_degree(self, degree):
        degree = max(0, min(180, degree))
        duty = servo_min_duty + (degree * (servo_max_duty - servo_min_duty) / 180.0)
        servo.ChangeDutyCycle(duty)
        time.sleep(0.015)
    
    def tail_wag_loop(self):
        """꼬리 흔들기 루프 (60-120도 왕복)"""
        global servo
        while self.tail_running:
            # 좌우 흔들기
            for deg in range(60, 120, 5):
                if not self.tail_running: break
                self.set_servo_degree(deg)
            for deg in range(120, 60, -5):
                if not self.tail_running: break
                self.set_servo_degree(deg)
    
    def start_tail_wag(self):
        if not self.tail_running:
            self.tail_running = True
            self.tail_thread = threading.Thread(target=self.tail_wag_loop, daemon=True)
            self.tail_thread.start()
            print("🐕 꼬리 흔들기 시작! (얼굴 감지)")
    
    def stop_tail(self):
        self.tail_running = False
        if self.tail_thread and self.tail_thread.is_alive():
            self.tail_thread.join(timeout=0.2)
        self.set_servo_degree(90)  # 중앙 정지
        print("🛑 꼬리 정지!")
    
    def detect_face(self):
        """fswebcam + OpenCV 얼굴 인식 (0.5초 주기)"""
        img_path = self.capture_face_image()
        if not img_path:
            return False, 0
        
        try:
            frame = cv2.imread(img_path)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
            face_detected = len(faces) > 0
            
            # 꼬리 제어 로직
            if face_detected and not self.tail_running:
                self.start_tail_wag()
            elif not face_detected and self.tail_running:
                self.stop_tail()
            
            os.unlink(img_path)
            return face_detected, len(faces)
        except:
            if os.path.exists(img_path):
                os.unlink(img_path)
            return False, 0
    
    def cleanup(self):
        """종료 정리"""
        self.stop_tail()
        cv2.destroyAllWindows()
        servo.ChangeDutyCycle(0)
        servo.stop()
        GPIO.cleanup()
        print("✅ 하드웨어 정리 완료!")

def bitnet_chat(prompt: str, max_tokens: int = 50) -> str:
    """BitNet 공식 바이너리 호출 (안정적)"""
    if not LLM_AVAILABLE:
        return "멍멍! 🐶"
    
    try:
        cmd = [
            BITNET_BINARY, '-m', BITNET_MODEL_PATH,
            '-p', prompt,
            '-n', str(max_tokens), '-t', '4',
            '-temp', '0.7', '-cnv'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        reply = result.stdout.strip()
        return reply[:80] if reply else "좋은 하루! 🐾"
    except Exception as e:
        print(f"🤖 BitNet 오류: {e}")
        return "생각중... 🐕"

def local_chat(user_text: str, emotion: str, face_detected: bool) -> str:
    """로봇 대화 로직 (BitNet 우선 + Fallback)"""
    if not user_text.strip():
        return "woof woof 🐶"
    
    context = f"[{emotion}, face:{'O' if face_detected else 'X'}, {time.strftime('%H:%M')}]"
    
    if LLM_AVAILABLE:
        prompt = f"{context} 주인: {user_text}\n친구 로봇 개:"
        reply = bitnet_chat(prompt)
        gc.collect()  # 메모리 정리
        return reply
    
    # Fallback 응답 (BitNet 실패시)
    if face_detected:
        return "🐶 얼굴 봤어! 같이 놀자~ 😊"
    elif any(g in user_text.lower() for g in ["안녕", "hi", "hello"]):
        return "🐕 안녕하세요 주인님! 오늘도 화이팅! 💕"
    elif any(g in user_text for g in ["사랑", "좋아", "귀여워"]):
        return "🥰 저도 주인님 사랑해요! 🐾"
    else:
        responses = {
            "happy": "멋져요! 같이 뛰놀자! 🏃‍♂️",
            "sad": "괜찮아요... 같이 산책 갈까요? 🥺",
            "angry": "진정하세요... 숨 쉬세요~ 😌",
            "neutral": "네? 더 말씀해주세요! 🐶"
        }
        return responses.get(emotion, f"'{user_text}' 들었어요! 😄")

def hardware_monitoring_loop(robot):
    """얼굴 감지 백그라운드 스레드 (0.5초 주기)"""
    count = 0
    while robot.running:
        face_detected, face_count = robot.detect_face()
        robot.face_detected = face_detected
        
        count += 1
        status = f"[📸 {count:4d}] 얼굴:{face_count} 꼬리:{'흔들림!' if robot.tail_running else '정지'}"
        print(status, end='\r', flush=True)
        time.sleep(0.5)  # fswebcam 속도 고려

def main_loop():
    """메인 루프 - 얼굴감지 + 음성대화"""
    print("=" * 60)
    print("🚀 BitNet b1.58 반려로봇 v2.0 시작!")
    print("📋 확인사항: fswebcam / USB카메라 / haarcascade.xml")
    print("💾 메모리 모니터링: htop (MEM < 1.5GB 유지)")
    print("=" * 60)
    
    robot = RobotHardware()
    robot.running = True
    robot.start_camera()
    
    # 얼굴 감지 백그라운드 시작
    monitor_thread = threading.Thread(target=hardware_monitoring_loop, args=(robot,), daemon=True)
    monitor_thread.start()
    
    print("🚀 로봇 활성화 완료! (Ctrl+C 종료)")
    
    try:
        while True:
            print("\n" + "=" * 50 + "\n=== 새 대화 ===")
            
            status = f"[📸 얼굴]: {'O' if robot.face_detected else 'X'} [🐕 꼬리]: {'흔들림!' if robot.tail_running else '정지'}"
            print(status)
            
            # 1. 감정 분석
            emotion = get_current_emotion()
            print(f"[😊 감정]: {emotion}")
            
            # 2. 음성 입력 (10초)
            print("🎤 말해주세요... (10초 대기)")
            text = stt_from_mic(seconds=10)
            print(f"[💭 음성->텍스트]: '{text}'")
            
            # 3. BitNet 대화 생성
            reply = local_chat(text, emotion, robot.face_detected)
            print(f"[🤖 BitNet]: {reply}")
            
            # 4. TTS 출력
            tts_play(reply)
            
            print("-" * 50)
            time.sleep(1)  # 간격 조절
            
    except KeyboardInterrupt:
        print("\n\n👋 로봇 종료 신호 수신...")
    finally:
        robot.running = False
        time.sleep(2)  # 정리 대기
        robot.cleanup()
        print("✨ 프로그램 완전 종료!")

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n👋 안전 종료!")
    except Exception as e:
        print(f"❌ 치명적 오류: {e}")
    finally:
        try:
            GPIO.cleanup()
            servo.stop()
        except:
            pass