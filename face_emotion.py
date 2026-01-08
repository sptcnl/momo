# face_emotion.py (USB 카메라 버전)
import cv2
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

# USB 카메라 초기화 (전역)
cap = cv2.VideoCapture(0)  # 0: 기본 USB 카메라, 다른 포트면 1, 2 등으로 변경
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # 해상도 설정
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

def get_current_emotion():
    try:
        ret, frame = cap.read()
        if not ret:
            return "error: 카메라 읽기 실패"
            
        # BGR -> RGB 변환 (OpenCV 기본 형식)
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
    print("USB 카메라 표정 감지 테스트...")
    try:
        for i in range(5):
            emotion = get_current_emotion()
            print(f"[{i+1}/5] Emotion: {emotion}")
    finally:
        cap.release()
        print("카메라 해제 완료")