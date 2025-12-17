from gpiozero import DistanceSensor
from time import sleep

# 초음파 거리 센서를 초기화
distanceSensor = DistanceSensor(echo=17, trigger=4)

count = 0  # 측정 횟수를 저장할 변수 count를 0으로 초기화

# 무한 루프를 실행합니다. 
# 사용자가 강제로 중지하기 전까지 계속 반복됩니다.
while 1 :
    count += 1  # 측정 횟수를 1 증가시킵니다.
    
    # 현재 측정 횟수(count)와 센서로 측정된 거리를 센티미터(cm) 단위로 출력합니다.
    # 측정된 거리는 소수점 세 자리까지 표시됩니다.
    print(f"[{count:6d}] {distanceSensor.distance * 100:.3f} cm")
    
    sleep(0.1)  # 0.1초 동안 대기합니다. 즉, 초당 약 10번의 측정을 수행하게 됩니다.
pass