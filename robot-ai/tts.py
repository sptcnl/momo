#!/usr/bin/env python3
# tts_piper.py - Raspberry Pi 최적화 버전
import sounddevice as sd
import soundfile as sf
import os
import subprocess
import sys
import wave
from piper import PiperVoice
import subprocess

def tts_play(text: str):
    try:
        # 1. 음성 모델 로드
        voice = PiperVoice.load("en_US-amy-medium.onnx")

        with wave.open("test.wav", "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        subprocess.run(["aplay", "test.wav"])
        return True
    except Exception as e:
        print(f'error: {e}')

if __name__ == "__main__":
    print("🤖 반려로봇 TTS 테스트")
    print("-" * 40)
    
    success = tts_play("Hello world")
    
    if success:
        print("\n✅ TTS 완벽 작동! 로봇에 통합 가능")
    else:
        print("\n🔧 설치 확인:")
        print("1. pip install piper-tts")
        print("2. echo '테스트' | piper --model ko_KR --output_file /tmp/test.wav")