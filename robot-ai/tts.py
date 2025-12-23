# tts.py
import subprocess
import uuid
import os

PIPER_BIN = "/home/sptcnl/piper/piper"
PIPER_MODEL = "/home/sptcnl/piper/ko_KR-sunhi-medium.onnx"

def tts_play(text: str):
    if not text:
        return

    wav_file = f"/tmp/tts_{uuid.uuid4().hex}.wav"

    try:
        # 텍스트 → 음성
        p = subprocess.Popen(
            [
                PIPER_BIN,
                "--model", PIPER_MODEL,
                "--output_file", wav_file
            ],
            stdin=subprocess.PIPE
        )
        p.stdin.write(text.encode("utf-8"))
        p.stdin.close()
        p.wait()

        # 재생
        subprocess.run(["aplay", wav_file], check=False)

    except Exception as e:
        print("⚠️ TTS 실패:", e)

    finally:
        if os.path.exists(wav_file):
            os.remove(wav_file)