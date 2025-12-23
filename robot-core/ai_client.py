import socket, json

AI_HOST = "robot-ai"
AI_PORT = 5000

def ask_ai(text, face_detected, distance):
    req = {
        "text": text,
        "face_detected": face_detected,
        "distance": distance
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((AI_HOST, AI_PORT))
    sock.send(json.dumps(req).encode())

    res = sock.recv(4096).decode()
    sock.close()

    return json.loads(res)