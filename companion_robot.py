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

# BitNet을 위한 llama-cpp-python 사용 (CPU 전용)
try:
    from llama_cpp import Llama
    BITNET_MODEL_PATH = "/home/sptcnl/models/bitnet_b1_58-3B.Q4_K_M.gguf"
    chat_model = Llama(
        model_path=BITNET_MODEL_PATH,
        n_ctx=512,
        n_threads=4,
        n_gpu_layers=0,
        verbose=False
    )
    LLM_AVAILABLE = True
    print("✅ BitNet 3B 로드 성공! (~1GB 메모리)")
except Exception as e:
    LLM_AVAILABLE = False
    print(f"⚠️ BitNet 로드 실패: {e}")

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
        # self.cap 제거 - fswebcam 사용
        self.face_detected = False
        self.running = False
        self.tail_running = False
        self.tail_thread = None
        
    def start_camera(self):
        """fswebcam으로 카메라 테스트"""
        test_img = self.capture_face_image()
        if test_img:
            print("📷 fswebcam USB 카메라 연결 성공!")
            os.unlink(test_img)  # 테스트 이미지 삭제
        else:
            print("❌ fswebcam 카메라 연결 실패! USB 연결 확인하세요")
    
    def capture_face_image(self):
        """fswebcam으로 단일 이미지 캡처"""
        temp_file = f"/tmp/webcam_face_{int(time.time())}.jpg"
        cmd = [
            "fswebcam",
            "--resolution", "640x480",
            "--no-banner",
            "--save", temp_file
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=3)
            if os.path.exists(temp_file):
                return temp_file
        except:
            pass
        return None
    
    def set_servo_degree(self, degree):
        if degree > 180: degree = 180
        elif degree < 0: degree = 0
        duty = servo_min_duty + (degree * (servo_max_duty - servo_min_duty) / 180.0)
        servo.ChangeDutyCycle(duty)
        time.sleep(0.015)
    
    def tail_wag_loop(self):
        global servo
        while self.tail_running:
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
            print("🐕 꼬리 흔들기 시작!")
    
    def stop_tail(self):
        self.tail_running = False
        if self.tail_thread and self.tail_thread.is_alive():
            self.tail_thread.join(timeout=0.1)
        self.set_servo_degree(90)
        print("🛑 꼬리 정지!")
    
    def detect_face(self):
        """fswebcam + OpenCV 얼굴 인식"""
        img_path = self.capture_face_image()
        if not img_path:
            return False, 0
        
        try:
            frame = cv2.imread(img_path)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
            face_detected = len(faces) > 0
            
            if face_detected and not self.tail_running:
                self.start_tail_wag()
            elif not face_detected and self.tail_running:
                self.stop_tail()
            
            os.unlink(img_path)  # 캡처 이미지 삭제
            return face_detected, len(faces)
            
        except Exception as e:
            if img_path and os.path.exists(img_path):
                os.unlink(img_path)
            return False, 0
    
    def cleanup(self):
        self.stop_tail()
        cv2.destroyAllWindows()
        servo.ChangeDutyCycle(0)
        servo.stop()
        GPIO.cleanup()
        print("✅ 모든 정리 완료!")

def local_chat(user_text: str, emotion: str, face_detected: bool) -> str:
    if not user_text:
        return "woof woof"
    
    context = f"emotion:{emotion}, face:{'detected' if face_detected else 'not_detected'}"
    
    if LLM_AVAILABLE:
        try:
            prompt = f"[{context}] User: {user_text}\nFriendly robot dog:"
            response = chat_model(
                prompt, 
                max_tokens=50,
                temperature=0.7,
                top_p=0.9,
                stop=["User:", "\n\n"],
                echo=False
            )
            reply = response['choices'][0]['text'].strip()
            gc.collect()
            return reply[:80]
        except Exception as e:
            print(f"LLM 오류: {e}")
            gc.collect()
    
    if face_detected:
        return "🐶 얼굴 봤어! 같이 놀자!"
    elif "안녕" in user_text or "hi" in user_text:
        return "🐕 안녕하세요 주인님! 😊"
    else:
        responses = {"happy": "멋져요! 🐾", "sad": "괜찮아요.. 🥺", "neutral": "네? 🐶"}
        return responses.get(emotion, f"{user_text} 들었어요!")

def hardware_monitoring_loop(robot):
    count = 0
    while robot.running:
        face_detected, face_count = robot.detect_face()
        robot.face_detected = face_detected
        
        count += 1
        print(f"[📸 {count:4d}] 얼굴:{face_count} 꼬리:{'흔들림' if robot.tail_running else '정지'}", end='\r')
        time.sleep(0.5)  # fswebcam은 느리므로 간격 늘림

def main_loop():
    print("🚀 fswebcam 반려로봇 시작 전 필수 확인!")
    print("1. sudo apt install fswebcam")
    print("2. USB 카메라 연결")
    print("3. haarcascade_frontalface_default.xml 파일 존재 확인")
    
    robot = RobotHardware()
    robot.running = True
    robot.start_camera()
    
    monitor_thread = threading.Thread(target=hardware_monitoring_loop, args=(robot,), daemon=True)
    monitor_thread.start()
    
    print("🚀 BitNet 반려로봇 시작! (fswebcam 얼굴감지 + 꼬리흔들기 + 음성대화)")
    print("💾 메모리: htop으로 MEM/SWP 모니터링 권장")
    print("Ctrl+C로 종료")
    
    try:
        while True:
            print("\n=== 새 대화 ===")
            
            print(f"[📸 얼굴]: {'O' if robot.face_detected else 'X'} [🐕 꼬리]: {'흔들림' if robot.tail_running else '정지'}")
            
            emotion = get_current_emotion()  # fswebcam 기반
            print(f"[😊 감정]: {emotion}")
            
            print("🎤 말해줘... (10초)")
            text = stt_from_mic(seconds=10)
            print(f"[💭 STT]: '{text}'")
            
            reply = local_chat(text, emotion, robot.face_detected)
            print(f"[🤖 BitNet]: {reply}")
            
            tts_play(reply)
            print("-" * 50)
            
    except KeyboardInterrupt:
        print("\n👋 로봇 종료 중...")
    finally:
        robot.running = False
        time.sleep(1.0)  # fswebcam 정리 대기
        robot.cleanup()
        if LLM_AVAILABLE:
            chat_model.free()
            gc.collect()

if __name__ == "__main__":
    main_loop()