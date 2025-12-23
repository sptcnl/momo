import socket, json
from emotion import get_current_emotion
from stt import stt_from_mic
from tts import tts_play
from llm import local_chat

HOST = "0.0.0.0"
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)

print("🤖 robot-ai 서버 시작")

while True:
    conn, addr = sock.accept()
    print("연결:", addr)

    data = conn.recv(4096).decode()
    req = json.loads(data)

    # AI 처리
    emotion = get_current_emotion()
    reply = local_chat(
        req.get("text", ""),
        emotion,
        req.get("face_detected", False),
        req.get("distance", 999)
    )

    res = {
        "emotion": emotion,
        "reply": reply
    }

    conn.send(json.dumps(res).encode())
    tts_play(reply)
    conn.close()