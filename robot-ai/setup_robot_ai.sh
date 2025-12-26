#!/bin/bash
set -e

echo "🧠 Robot-AI 설치 시작"

BASE_DIR=$HOME/robot/robot-ai
VENV_DIR=$BASE_DIR/.venv

mkdir -p $BASE_DIR
cd $BASE_DIR

### 1. 시스템 패키지
echo "📦 시스템 패키지 설치..."
sudo apt update
sudo apt install -y \
  git cmake build-essential \
  python3 python3-venv python3-pip \
  ffmpeg sox \
  libatlas-base-dev \
  portaudio19-dev \
  alsa-utils \
  curl wget

### 2. Python 가상환경
echo "🐍 Python 가상환경 생성..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install --upgrade pip wheel setuptools

### 3. whisper.cpp
echo "🗣️ whisper.cpp 설치..."
if [ ! -d whisper.cpp ]; then
  git clone https://github.com/ggerganov/whisper.cpp.git
fi

cd whisper.cpp
make -j$(nproc)

cd models
if [ ! -f ggml-small.ko.bin ]; then
  bash download-ggml-model.sh small.ko
fi
cd $BASE_DIR

### 4. Piper TTS
echo "🔊 Piper TTS 설치..."
if [ ! -d piper ]; then
  git clone https://github.com/rhasspy/piper.git
fi

cd piper
pip install -r requirements.txt
pip install .

mkdir -p models/ko
cd models/ko
if [ ! -f ko_KR-kss-medium.onnx ]; then
  wget https://github.com/rhasspy/piper/releases/download/v1.0.0/ko_KR-kss-medium.onnx
  wget https://github.com/rhasspy/piper/releases/download/v1.0.0/ko_KR-kss-medium.onnx.json
fi

cd $BASE_DIR

### 5. Python 라이브러리
echo "📚 Python 라이브러리 설치..."
pip install \
  numpy \
  sounddevice \
  soundfile \
  torch \
  torchaudio \
  transformers \
  requests

echo "✅ Robot-AI 설치 완료!"
echo "👉 source .venv/bin/activate"