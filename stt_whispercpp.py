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
WHISPER_MODEL = "/home/sptcnl/momo/whisper.cpp/models/ggml-base.bin"

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
    print(f"[녹음 시작] {seconds}초 동안 말하세요...")
    frames = []
    
    print("📡 PyAudio 입력 장치 확인 중...")
    print(f"기본 입력 장치: {p.get_default_input_device_info()}")
    
    try:
        for i in range(int(RATE / CHUNK * seconds)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            if i % 10 == 0:  # 10번마다 진행 상황
                print(f"📝 {i*CHUNK/RATE:.1f}초 녹음됨")
    except Exception as e:
        print(f"❌ 녹음 중 오류: {e}")
        return None
    
    print(f"📊 총 {len(frames)} 프레임 수집됨 ({len(b''.join(frames))} bytes)")
    
    if not frames:
        print("⚠️ 녹음 데이터 없음!")
        return None
    
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        print(f"💾 임시파일 생성: {tmp.name}")
        
        with wave.open(tmp.name, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
        
        print(f"✅ WAV 파일 생성 완료: {tmp.name} ({os.path.getsize(tmp.name)} bytes)")
        return tmp.name
        
    except Exception as e:
        print(f"❌ WAV 저장 실패: {e}")
        if 'tmp' in locals():
            os.unlink(tmp.name)
        return None

def run_whisper(wav_path):
    output_txt = wav_path.replace(".wav", ".txt")
    
    cmd = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", wav_path,
        "-l", "ko",  # --language → -l (최신 표준)
        "-otxt",     # 텍스트 파일 출력
        "-pp"        # 후처리 활성화 (더 정확)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    # .txt 파일 대신 stdout 확인 (더 안정적)
    if result.stdout.strip():
        text = result.stdout.strip()
    elif os.path.exists(output_txt):
        with open(output_txt, "r", encoding="utf-8") as f:
            text = f.read().strip()
        os.unlink(output_txt)
    else:
        text = f"실패: {result.stderr}"  # 디버깅용
    
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