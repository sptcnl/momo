# stt_whispercpp.py (2025 최신 안정화 버전)
import subprocess
import tempfile
import pyaudio
import wave
import time
import os
import shutil

# whisper.cpp 최신 실행 파일 경로
WHISPER_BIN = "/home/sptcnl/momo/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL = "/home/sptcnl/momo/whisper.cpp/models/ggml-tiny.bin"

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 4

# PyAudio 초기화 (에러 방지)
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                input=True, frames_per_buffer=CHUNK)


def check_environment():
    """whisper.cpp 실행 파일과 모델 파일 확인"""
    if not os.path.exists(WHISPER_BIN):
        raise FileNotFoundError(f"❌ whisper-cli 실행파일 없음: {WHISPER_BIN}")

    if not os.path.exists(WHISPER_MODEL):
        raise FileNotFoundError(f"❌ tiny 모델 없음: {WHISPER_MODEL}")


def record_audio(seconds=RECORD_SECONDS):
    """마이크 녹음 → 임시 WAV 파일 생성"""
    print(f"[녹음 시작] {seconds}초 동안 말하세요...")
    frames = []

    for _ in range(int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))

    return tmp.name


def run_whisper(wav_path):
    """
    whisper.cpp(whisper-cli)를 실행해 텍스트 반환
    최신 옵션 기준:
      -otxt : 텍스트 파일 출력
      -of   : output 파일 prefix
    """

    output_txt = wav_path.replace(".wav", ".txt")

    cmd = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", wav_path,
        "--language", "ko",
        "-otxt",
        "-of", wav_path  # 출력 prefix
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30
    )

    # whisper.cpp는 stdout이 거의 비어있음 → txt 파일에서 직접 읽는 방식이 가장 안정적
    if os.path.exists(output_txt):
        with open(output_txt, "r", encoding="utf-8") as f:
            text = f.read().strip()
        os.unlink(output_txt)
    else:
        text = ""

    return text


def stt_from_mic(seconds=RECORD_SECONDS):
    """전체 파이프라인: 녹음 → whisper.cpp → 텍스트 리턴"""
    try:
        wav = record_audio(seconds)
        print("🔄 whisper.cpp 인식 중…")

        text = run_whisper(wav)

        os.unlink(wav)
        return text

    except subprocess.TimeoutExpired:
        return "⏰ 인식 타임아웃"
    except Exception as e:
        return f"❌ 오류 발생: {e}"


if __name__ == "__main__":
    try:
        check_environment()
        print("🎤 whisper.cpp 한국어 STT (라즈베리파이 최적화) 시작!")

        while True:
            text = stt_from_mic(4)
            print(f"[결과]: {text}")
            time.sleep(1)

    except Exception as e:
        print(f"프로그램 초기화 실패: {e}")