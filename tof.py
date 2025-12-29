import time
import board
import busio
from adafruit_vl53l1x import VL53L1X

# I2C 버스 열기
i2c = busio.I2C(board.SCL, board.SDA)

# 센서 생성
sensor = VL53L1X(i2c, address=0x29)

# 연속 측정 시작
sensor.start_ranging()

try:
    while True:
        if sensor.distance:
            distance_cm = sensor.distance
            print(f"거리: {distance_cm} cm ({distance_cm/10:.1f} m)")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n중단됨")
finally:
    sensor.stop_ranging()
