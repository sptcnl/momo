from hardware import RobotHardware
from ai_client import ask_ai
import time

robot = RobotHardware()
robot.running = True

try:
    while True:
        face, dist, _ = robot.detect_face()

        print("🎤 말해줘")
        text = input("> ")  # 테스트용 (STT는 ai쪽)

        ai_res = ask_ai(text, face, dist)

        print("😊 감정:", ai_res["emotion"])
        print("🤖 말:", ai_res["reply"])

        time.sleep(1)

except KeyboardInterrupt:
    robot.cleanup()