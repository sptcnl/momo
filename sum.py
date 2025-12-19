import cv2
from gpiozero import DistanceSensor
import RPi.GPIO as GPIO
from face_emotion import get_current_emotion  # 기존 emotion 모듈 사용
from stt_whispercpp import stt_from_mic
from tts_piper import tts_play
import random, re, time
import threading

# 경량 LLM
try:
    from transformers import pipeline
    chat_pipeline = pipeline("text-generation", model="gpt2", device=-1, torch_dtype="float32")
    LLM_AVAILABLE = True
except:
    LLM_AVAILABLE = False
    print("⚠️ LLM 로드 실패")

# 하드웨어 설정
class RobotHardware:
    def __init__(self):
        # Face detection - USB 카메라로 변경
        self.cascade_path = "/home/sptcnl/haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        self.cap = cv2.VideoCapture(0)  # USB 카메라 (0번 포트)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Distance sensor
        self.distance_sensor = DistanceSensor(echo=21, trigger=4)
        
        # Motor control
        self.left_in3, self.left_in4, self.left_ena = 24, 23, 25
        self.right_in3, self.right_in4, self.right_enb = 18, 17, 27
        
        GPIO.setmode(GPIO.BCM)
        for pin in [self.left_in3, self.left_in4, self.left_ena, 
                   self.right_in3, self.right_in4, self.right_enb]:
            GPIO.setup(pin, GPIO.OUT)
        
        self.left_pwm = GPIO.PWM(self.left_ena, 1000)
        self.right_pwm = GPIO.PWM(self.right_enb, 1000)
        self.left_pwm.start(0)
        self.right_pwm.start(0)
        self.stop()
        
        # 상태 변수
        self.is_moving = False
        self.current_speed = 50
        self.current_distance = 0
        self.face_detected = False
        self.running = False
        
    def start_camera(self):
        """USB 카메라 시작 확인"""
        ret, test_frame = self.cap.read()
        if ret:
            print("📷 USB 카메라 연결 성공!")
        else:
            print("❌ USB 카메라 연결 실패! 꽂혀있는지 확인하세요")
    
    def detect_face(self):
        """얼굴 감지 및 거리 측정 - USB 카메라"""
        ret, frame = self.cap.read()
        if not ret:
            return False, 0, 0
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
        distance = self.distance_sensor.distance * 100
        
        # 얼굴이 감지되면 전진
        if len(faces) > 0:
            if not self.is_moving:
                self.forward()
                self.set_speed(min(self.current_speed, 40))  # 안전 속도
                self.is_moving = True
            return True, distance, len(faces)
        else:
            if self.is_moving:
                self.stop()
                self.is_moving = False
            return False, distance, 0
    
    # 모터 제어 함수들 (변경 없음)
    def forward(self):
        GPIO.output(self.left_in3, GPIO.HIGH); GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.HIGH); GPIO.output(self.right_in4, GPIO.LOW)
    
    def backward(self):
        GPIO.output(self.left_in3, GPIO.LOW); GPIO.output(self.left_in4, GPIO.HIGH)
        GPIO.output(self.right_in3, GPIO.LOW); GPIO.output(self.right_in4, GPIO.HIGH)
    
    def left_turn(self):
        GPIO.output(self.left_in3, GPIO.LOW); GPIO.output(self.left_in4, GPIO.HIGH)
        GPIO.output(self.right_in3, GPIO.HIGH); GPIO.output(self.right_in4, GPIO.LOW)
    
    def right_turn(self):
        GPIO.output(self.left_in3, GPIO.HIGH); GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.LOW); GPIO.output(self.right_in4, GPIO.HIGH)
    
    def stop(self):
        GPIO.output(self.left_in3, GPIO.LOW); GPIO.output(self.left_in4, GPIO.LOW)
        GPIO.output(self.right_in3, GPIO.LOW); GPIO.output(self.right_in4, GPIO.LOW)
        self.left_pwm.ChangeDutyCycle(0)
        self.right_pwm.ChangeDutyCycle(0)
    
    def set_speed(self, speed):
        self.current_speed = speed
        self.left_pwm.ChangeDutyCycle(speed)
        self.right_pwm.ChangeDutyCycle(speed)
    
    def cleanup(self):
        self.stop()
        if self.cap:
            self.cap.release()
        self.left_pwm.stop()
        self.right_pwm.stop()
        cv2.destroyAllWindows()
        GPIO.cleanup()

def local_chat(user_text: str, emotion: str, face_detected: bool, distance: float) -> str:
    if not user_text:
        return "woof woof"
    
    context = f"emotion:{emotion}, face:{'near' if face_detected and distance<100 else 'far'}, distance:{distance:.1f}cm"
    
    if LLM_AVAILABLE:
        try:
            prompt = f"[{context}] User: {user_text}\nRobot (friendly companion robot):"
            response = chat_pipeline(prompt, max_new_tokens=40, do_sample=True)
            reply = response[0]['generated_text'].split("Robot:")[-1].strip()
            return reply[:100]
        except:
            pass
    
    # 상황별 더미 응답
    if face_detected and distance < 50:
        return "🐶 가까이 왔어! 같이 놀자!"
    elif "안녕" in user_text or "hi" in user_text:
        return "🐕 안녕하세요 주인님! 😊"
    else:
        responses = {"happy": "멋져요! 🐾", "sad": "괜찮아요.. 🥺", "neutral": "네? 🐶"}
        return responses.get(emotion, f"{user_text} 들었어요!")

def hardware_monitoring_loop(robot):
    """백그라운드에서 하드웨어 모니터링"""
    count = 0
    while robot.running:
        face_detected, distance, face_count = robot.detect_face()
        robot.current_distance = distance
        robot.face_detected = face_detected
        
        count += 1
        print(f"[📏 {count:4d}] 거리:{distance:5.1f}cm 얼굴:{face_count}", end='\r')
        time.sleep(0.1)

def main_loop():
    robot = RobotHardware()
    robot.running = True
    robot.start_camera()
    
    # 하드웨어 모니터링 스레드 시작
    monitor_thread = threading.Thread(target=hardware_monitoring_loop, args=(robot,), daemon=True)
    monitor_thread.start()
    
    print("🚀 반려로봇 시작! (자동 추종 + 음성대화)")
    print("Ctrl+C로 종료")
    
    try:
        while True:
            print("\n=== 새 대화 ===")
            
            # 1) 하드웨어 상태 확인
            print(f"[📸 얼굴]: {'O' if robot.face_detected else 'X'}, [📏 거리]: {robot.current_distance:.1f}cm")
            
            # 2) 표정 감지 (기존 모듈 사용)
            emotion = get_current_emotion()
            print(f"[😊 감정]: {emotion}")
            
            # 3) 음성 입력
            print("🎤 말해줘... (10초)")
            text = stt_from_mic(seconds=10)
            print(f"[💭 STT]: '{text}'")
            
            # 4) LLM 응답 생성 (하드웨어 상태 포함)
            reply = local_chat(text, emotion, robot.face_detected, robot.current_distance)
            print(f"[🤖 로봇]: {reply}")
            
            # 5) TTS 출력
            tts_play(reply)
            print("-" * 50)
            
    except KeyboardInterrupt:
        print("\n👋 로봇 종료 중...")
    finally:
        robot.running = False
        robot.cleanup()
        print("✅ 모든 하드웨어 정리 완료!")

if __name__ == "__main__":
    main_loop()