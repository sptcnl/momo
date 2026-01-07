import cv2
from face_emotion import get_current_emotion
from stt_whispercpp import stt_from_mic
from tts_piper import tts_play
import time
import threading
import RPi.GPIO as GPIO

try:
    from transformers import pipeline
    chat_pipeline = pipeline("text-generation", model="gpt2", device=-1, torch_dtype="float32")
    LLM_AVAILABLE = True
except:
    LLM_AVAILABLE = False
    print("⚠️ LLM 로드 실패")

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
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.face_detected = False
        self.running = False
        self.tail_running = False
        self.tail_thread = None
        
    def start_camera(self):
        ret, test_frame = self.cap.read()
        if ret:
            print("📷 USB 카메라 연결 성공!")
        else:
            print("❌ USB 카메라 연결 실패! 꽂혀있는지 확인하세요")
    
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
        ret, frame = self.cap.read()
        if not ret:
            return False, 0
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
        face_detected = len(faces) > 0
        
        if face_detected and not self.tail_running:
            self.start_tail_wag()
        elif not face_detected and self.tail_running:
            self.stop_tail()
        
        return face_detected, len(faces)
    
    def cleanup(self):
        self.stop_tail()
        if self.cap:
            self.cap.release()
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
            prompt = f"[{context}] User: {user_text}\nRobot (friendly companion robot):"
            response = chat_pipeline(prompt, max_new_tokens=40, do_sample=True)
            reply = response[0]['generated_text'].split("Robot:")[-1].strip()
            return reply[:100]
        except:
            pass
    
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
        time.sleep(0.1)

def main_loop():
    robot = RobotHardware()
    robot.running = True
    robot.start_camera()
    
    monitor_thread = threading.Thread(target=hardware_monitoring_loop, args=(robot,), daemon=True)
    monitor_thread.start()
    
    print("🚀 반려로봇 시작! (얼굴감지 + 꼬리흔들기 + 음성대화)")
    print("Ctrl+C로 종료")
    
    try:
        while True:
            print("\n=== 새 대화 ===")
            
            print(f"[📸 얼굴]: {'O' if robot.face_detected else 'X'} [🐕 꼬리]: {'흔들림' if robot.tail_running else '정지'}")
            
            emotion = get_current_emotion()
            print(f"[😊 감정]: {emotion}")
            
            print("🎤 말해줘... (10초)")
            text = stt_from_mic(seconds=10)
            print(f"[💭 STT]: '{text}'")
            
            reply = local_chat(text, emotion, robot.face_detected)
            print(f"[🤖 로봇]: {reply}")
            
            tts_play(reply)
            print("-" * 50)
            
    except KeyboardInterrupt:
        print("\n👋 로봇 종료 중...")
    finally:
        robot.running = False
        time.sleep(0.5)
        robot.cleanup()

if __name__ == "__main__":
    main_loop()