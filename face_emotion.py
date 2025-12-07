# face_emotion.py (완전 버전)
import cv2
from picamera2 import Picamera2
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import numpy as np
import torch

DEVICE = "cpu"

# 표정 감지 모델 (첫 실행시 자동 다운로드)
MODEL_NAME = "HardlyHumans/Facial-expression-detection"

processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForImageClassification.from_pretrained(MODEL_NAME).to(DEVICE)
id2label = model.config.id2label

# 카메라 초기화 (전역)
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (320, 240)})  # 가볍게
picam2.configure(config)
picam2.start()

def get_current_emotion():
    try:
        frame = picam2.capture_array()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        
        inputs = processor(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            outputs = model(**inputs)
            pred_id = int(torch.argmax(outputs.logits, dim=-1))
            emotion = id2label[pred_id]
        return emotion
    except Exception as e:
        return f"error: {str(e)}"

if __name__ == "__main__":
    print("표정 감지 테스트...")
    for _ in range(5):
        emotion = get_current_emotion()
        print("Emotion:", emotion)
