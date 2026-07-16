import os
import cv2
import mediapipe as mp

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "models", "hand_landmarker.task"
)


class HandDetector:

    def __init__(self):

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=MODEL_PATH
            ),
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(
            options
        )


    def detect_hands(self, frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        results = self.detector.detect(image)

        return results


    def draw_landmarks(self, frame, results):

        if results.hand_landmarks:

            h, w, _ = frame.shape

            for hand_landmarks in results.hand_landmarks:

                for landmark in hand_landmarks:

                    x = int(landmark.x * w)
                    y = int(landmark.y * h)

                    cv2.circle(
                        frame,
                        (x, y),
                        5,
                        (0, 255, 0),
                        -1
                    )

        return frame

    def close(self):
        self.detector.close()