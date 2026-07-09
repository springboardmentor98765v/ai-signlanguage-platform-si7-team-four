import cv2
from camera import Camera
camera = Camera()

while True:
    frame = camera.get_frame()

    if frame is None:
        print("Could not read frame")
        break
    cv2.imshow("Camera Test", frame)
    if cv2.waitKey(1) == 27:
        break

camera.release()