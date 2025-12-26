#!/bin/bash
set -e

echo "🤖 Robot-Core 설치 시작"

BASE_DIR=$HOME/robot-core
VENV_DIR=$BASE_DIR/.venv

mkdir -p $BASE_DIR
cd $BASE_DIR

### 1. 시스템 패키지
echo "📦 시스템 패키지 설치..."
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  git \
  libopencv-dev python3-opencv \
  portaudio19-dev \
  alsa-utils sox \
  i2c-tools \
  python3-rpi.gpio \
  python3-gpiozero \
  curl wget

### 2. Python 가상환경
echo "🐍 Python 가상환경 생성..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install --upgrade pip wheel setuptools

### 3. Python 라이브러리
echo "📚 Python 라이브러리 설치..."
pip install \
  numpy \
  opencv-python \
  sounddevice \
  soundfile \
  gpiozero \
  RPi.GPIO \
  requests \

echo "✅ Robot-Core 설치 완료!"
echo "👉 source .venv/bin/activate"