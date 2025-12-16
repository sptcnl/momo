# stt_whispercpp.py (2025 최신 안정화 버전)
import tempfile
import pyaudio
import wave
import time
import os

from faster_whisper import WhisperModel

# Whisper 모델 설정
WHISPER_MODEL_NAME = "base"  # "base.en", "small", "small.en" 등으로 교체 가능
DEVICE = "cpu"               # GPU 사용 시 "cuda"
COMPUTE_TYPE = "int8"        # Pi면 "int8" 또는 "int8_float16" 추천

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 4

# PyAudio 초기화
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                input=True, frames_per_buffer=CHUNK)

# faster-whisper 모델 로드 (한 번만)
print("📦 faster-whisper 모델 로딩 중...")
model = WhisperModel(
    WHISPER_MODEL_NAME,
    device=DEVICE,
    compute_type=COMPUTE_TYPE,
)

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

def run_whisper_faster(wav_path):
    """
    faster-whisper로 WAV 파일을 바로 읽어 텍스트 추출
    """
    # language="en" / "ko" 로 고정하고 싶으면 지정, 자동감지는 language=None
    segments, info = model.transcribe(
        wav_path,
        beam_size=5,
        vad_filter=True,       # 침묵 부분 자동 제거
        language=None,         # "en" 또는 "ko"로 고정 가능
        condition_on_previous_text=False,
    )

    print(f"🧠 detected language: {info.language}, prob={info.language_probability:.2f}")

    texts = []
    for seg in segments:
        # seg.text에 한 문장 단위 텍스트가 들어옵니다.
        print(f"[{seg.start:.2f}~{seg.end:.2f}] {seg.text}")
        texts.append(seg.text)

    full_text = " ".join(texts).strip()
    return full_text if full_text else "(인식된 텍스트 없음)"

def stt_from_mic(seconds=RECORD_SECONDS):
    """전체 파이프라인: 녹음 → faster-whisper → 텍스트 리턴"""
    try:
        wav = record_audio(seconds)
        if not wav:
            return "❌ 녹음 실패"

        print("🔄 faster-whisper 인식 중…")
        text = run_whisper_faster(wav)

        os.unlink(wav)
        return text

    except Exception as e:
        return f"❌ 오류 발생: {e}"

if __name__ == "__main__":
    try:
        print("🎤 faster-whisper STT (라즈베리파이 최적화) 시작!")

        while True:
            text = stt_from_mic(4)
            print(f"[결과]: {text}")
            time.sleep(1)

    except Exception as e:
        print(f"프로그램 초기화 실패: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()