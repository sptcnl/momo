# face_emotion.py (fswebcam 버전)
import subprocess
import cv2
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import numpy as np
import torch
import time
import os

DEVICE = "cpu"

# 표정 감지 모델 (첫 실행시 자동 다운로드)
MODEL_NAME = "HardlyHumans/Facial-expression-detection"

processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForImageClassification.from_pretrained(MODEL_NAME).to(DEVICE)
id2label = model.config.id2label

def capture_with_fswebcam():
    """fswebcam으로 이미지 캡처"""
    temp_file = "/tmp/webcam_face.jpg"
    
    # fswebcam 명령어 실행 (저해상도, 빠른 캡처)
    cmd = [
        "fswebcam",
        "--resolution", "320x240",
        "--no-banner", 
        "--save", temp_file
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=3)
        if os.path.exists(temp_file):
            return temp_file
        return None
    except subprocess.TimeoutExpired:
        return None
    except subprocess.CalledProcessError:
        return None

def get_current_emotion():
    """fswebcam으로 캡처한 이미지에서 표정 감지"""
    try:
        img_path = capture_with_fswebcam()
        if not img_path:
            return "error: fswebcam 캡처 실패"
        
        # 이미지 로드
        img = Image.open(img_path).convert('RGB')
        
        # 모델 추론
        inputs = processor(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            outputs = model(**inputs)
            pred_id = int(torch.argmax(outputs.logits, dim=-1))
            emotion = id2label[pred_id]
        
        # 임시파일 삭제
        os.unlink(img_path)
        
        return emotion
        
    except Exception as e:
        return f"error: {str(e)}"

if __name__ == "__main__":
    print("fswebcam 표정 감지 테스트...")
    print("실행 전 fswebcam 설치 필요: sudo apt install fswebcam")
    
    try:
        for i in range(5):
            emotion = get_current_emotion()
            print(f"[{i+1}/5] Emotion: {emotion}")
            time.sleep(1)  # 1초 대기
    except KeyboardInterrupt:
        print("\n테스트 중단")