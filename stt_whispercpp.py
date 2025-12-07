# stt_whispercpp.py - whisper.cpp + 실시간 마이크 (라즈베리 최적!)
import subprocess
import tempfile
import pyaudio
import wave
import time
import os

# whisper.cpp 경로 (빌드 완료 가정)
WHISPER_BIN = "/home/sptcnl/whisper.cpp/build/main"
WHISPER_MODEL = "/home/sptcnl/whisper.cpp/models/ggml-tiny.bin"  # tiny 다운로드 필요

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 4

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                input=True, frames_per_buffer=CHUNK)

def record_audio(seconds=RECORD_SECONDS):
    """마이크 녹음 → 임시 wav"""
    print(f"[{seconds}초] 🎤 말해줘! (whisper.cpp 대기...)")
    frames = []
    
    for _ in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    
    # 임시 wav 파일
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wf = wave.open(tmp.name, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    return tmp.name

def stt_from_mic(seconds=RECORD_SECONDS):
    """whisper.cpp로 오프라인 한국어 인식"""
    try:
        wav_path = record_audio(seconds)
        
        print("   🔄 whisper.cpp 인식 중...")
        
        # whisper.cpp 실행 (한국어)
        cmd = [
            WHISPER_BIN, "-m", WHISPER_MODEL,
            "-f", wav_path, "--language", "ko",
            "-osrt"  # 텍스트 출력
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # 임시 파일 삭제
        os.unlink(wav_path)
        
        # 결과 파싱 (첫 줄 텍스트)
        output = result.stdout.strip()
        if output:
            return output.split('\n')[0].strip()
        return ""
        
    except subprocess.TimeoutExpired:
        print("   ⏰ 인식 타임아웃")
        return ""
    except Exception as e:
        print(f"   ❌ 에러: {e}")
        return ""

if __name__ == "__main__":
    print("🎤 whisper.cpp STT 테스트!")
    while True:
        text = stt_from_mic(4)
        print(f"[실제 STT]: '{text}'")
        time.sleep(1)