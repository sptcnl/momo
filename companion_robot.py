from face_emotion import get_current_emotion
from stt_whispercpp import stt_from_mic
from tts_piper import tts_play
import random, re

# 경량 LLM (첫 실행시 자동 다운로드 ~1GB)
try:
    from transformers import pipeline
    chat_pipeline = pipeline(
        "text-generation",
        model="gpt2",
        device=-1,  # CPU
        torch_dtype="float32"
    )
    LLM_AVAILABLE = True
except:
    LLM_AVAILABLE = False
    print("⚠️ LLM 로드 실패. 더미 응답 사용")

def local_chat(user_text: str, emotion: str) -> str:
    if not user_text:
        return "woof woof"
    
    if LLM_AVAILABLE:
        try:
            prompt = f"The user seems {emotion}. The user said: {user_text}\nRobot (friendly tone):"
            response = chat_pipeline(prompt, max_new_tokens=30, do_sample=True)
            reply = response[0]['generated_text'].split("Robot:")[-1].strip()
            return reply[:80]
        except:
            pass
    
    # 더미 응답 (LLM 실패시)
    responses = {
        "happy": "arf arf!",
        "sad": "ruff!",
        "neutral": f"arf!",
        "error": "woof!"
    }
    return responses.get(emotion, f"{user_text} 들었어!")

def main_loop():
    print("🚀 반려로봇 시작! Ctrl+C로 종료")
    while True:
        print("\n=== 새 대화 ===")
        
        # 1) 표정 감지
        emotion = get_current_emotion()
        print(f"[📸 표정]: {emotion}")
        
        # 2) 음성 입력
        print("🎤 말해줘... (3초)")
        text = stt_from_mic(seconds=10)
        print(f"[💭 STT]: '{text}'")
        
        # 3) LLM 응답
        reply = local_chat(text, emotion)
        print(f"[🤖 로봇]: {reply}")
        
        # 4) TTS 출력
        tts_play(reply)
        print("-" * 40)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n👋 로봇 종료!")