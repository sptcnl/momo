import time
import board
import busio
import vl53l1x

# I2C 버스 열기 (라즈베리파이 기본 I2C-1)
i2c = busio.I2C(board.SCL, board.SDA)

# 센서 객체 생성
sensor = vl53l1x.VL53L1X(i2c, address=0x29)

# 거리 측정 시작
sensor.start_ranging()

try:
    while True:
        distance_mm = sensor.distance  # 단위: mm
        print(f"Distance: {distance_mm} mm")
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    sensor.stop_ranging()
