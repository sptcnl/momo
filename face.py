import cv2
from picamera2 import Picamera2

cascade_path = "/home/sptcnl/haarcascade_frontalface_default.xml"
face = cv2.CascadeClassifier(cascade_path)

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

while True:
    frame = picam2.capture_array()          # RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face.detectMultiScale(gray, 1.2, 5)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow("Face detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:         # ESC
        break

picam2.stop()
cv2.destroyAllWindows()