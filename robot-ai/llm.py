from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

# 모델 로드 (8bit 양자화 적용)
model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    quantization_config={"load_in_8bit": True},  # bitsandbytes 자동 적용
    device_map="auto"
)

chat_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)

def local_chat(user_text, emotion=None, face_detected=False, distance=None):
    if not user_text:
        return "woof woof"

    # 간결한 컨텍스트로 변경
    context_parts = []
    if emotion:
        context_parts.append(f"emotion={emotion}")
    if face_detected:
        context_parts.append(f"face_detected")
    if distance is not None:
        context_parts.append(f"distance={distance:.1f}m")

    context = ", ".join(context_parts)
    prompt = f"[{context}] User: {user_text}\nRobot:"
    
    res = chat_pipeline(
        prompt,
        max_new_tokens=30,    # 짧게 생성
        temperature=0.8,      # 약간의 랜덤성 추가
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    return res[0]["generated_text"].split("Robot:")[-1].strip()