from collections import deque, Counter

import cv2
import traceback

from camera import Camera
from hand_detector import HandDetector
from feature_extractor import FeatureExtractor
from predict import predict

CONFIDENCE_THRESHOLD = 0.6   # ignore predictions below this
SMOOTHING_WINDOW = 10        # frames to look back over for stability
STABLE_FRACTION = 0.7        # fraction of the window that must agree

recent_predictions = deque(maxlen=SMOOTHING_WINDOW)
stable_label = None

try:
    camera = Camera()
    detector = HandDetector()
    extractor = FeatureExtractor()

    while True:
        frame = camera.get_frame()

        if frame is None:
            print("Failed to get frame")
            break

        results = detector.detect_hands(frame)
        frame = detector.draw_landmarks(frame, results)

        if results.hand_landmarks:
            hand = results.hand_landmarks[0]

            sign, confidence = predict(hand, extractor)

            if confidence >= CONFIDENCE_THRESHOLD:
                recent_predictions.append(sign)
            else:
                recent_predictions.append(None)   # counts as "no confident sign"

            # only commit to a "stable" label once the same sign has
            # dominated the recent window — this is what smooths out
            # single-frame flicker instead of flashing every prediction
            if len(recent_predictions) == SMOOTHING_WINDOW:
                most_common, count = Counter(recent_predictions).most_common(1)[0]

                if most_common is not None and count / SMOOTHING_WINDOW >= STABLE_FRACTION:
                    if most_common != stable_label:
                        stable_label = most_common
                        print(f"Stable sign detected: {stable_label}")
                else:
                    stable_label = None

            overlay = f"Sign: {sign}  ({confidence:.2f})"
            cv2.putText(frame, overlay, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if stable_label:
                cv2.putText(frame, f"Stable: {stable_label}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)
        else:
            recent_predictions.append(None)

        cv2.imshow("Hand Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()

except Exception:
    traceback.print_exc()
finally:
    try:
        camera.release()
    except Exception:
        pass