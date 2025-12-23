# stt.py
import subprocess
import uuid
import os

WHISPER_BIN = "/home/pi/whisper.cpp/main"
WHISPER_MODEL = "/home/pi/whisper.cpp/models/ggml-base.bin"

def stt_from_mic(seconds: int = 5) -> str:
    wav_file = f"/tmp/rec_{uuid.uuid4().hex}.wav"

    try:
        # 녹음 (arecord)
        subprocess.run([
            "arecord",
            "-d", str(seconds),
            "-f", "cd",
            "-t", "wav",
            wav_file
        ], check=True)

        # whisper.cpp 실행
        result = subprocess.run(
            [
                WHISPER_BIN,
                "-m", WHISPER_MODEL,
                "-f", wav_file,
                "-l", "ko"
            ],
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()
        return output.split("]")[-1].strip()

    except Exception as e:
        print("⚠️ STT 실패:", e)
        return ""

    finally:
        if os.path.exists(wav_file):
            os.remove(wav_file)