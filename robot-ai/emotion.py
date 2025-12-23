# emotion.py
import random

try:
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    import torch
    from PIL import Image

    MODEL_NAME = "HardlyHumans/Facial-expression-detection"
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
    model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
    EMOTION_AVAILABLE = True
except Exception as e:
    print("⚠️ Emotion 모델 로드 실패:", e)
    EMOTION_AVAILABLE = False

EMOTIONS = ["happy", "sad", "neutral", "angry", "surprise"]

def get_current_emotion(image_path: str = None) -> str:
    """
    image_path: 얼굴 이미지 파일 경로 (없으면 랜덤/중립 fallback)
    """
    if not EMOTION_AVAILABLE or image_path is None:
        return random.choice(EMOTIONS)

    try:
        img = Image.open(image_path).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        pred = outputs.logits.argmax(-1).item()
        return model.config.id2label[pred].lower()
    except Exception as e:
        print("⚠️ Emotion 추론 실패:", e)
        return "neutral"