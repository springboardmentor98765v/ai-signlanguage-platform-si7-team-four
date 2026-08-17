import os
import time
import cv2
import numpy as np
import joblib

from camera import Camera
from hand_detector import HandDetector


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "dynamic_templates.joblib"
)

RESAMPLE_STEPS = 20


def resample_sequence(seq, target_len=20):

    t_orig = np.linspace(0, 1, len(seq))
    t_new = np.linspace(0, 1, target_len)

    out = np.zeros(
        (target_len, 21, 3),
        dtype=np.float32
    )

    for i in range(21):
        for j in range(3):
            out[:, i, j] = np.interp(
                t_new,
                t_orig,
                seq[:, i, j]
            )

    return out


def trajectory_features(seq):

    wrist = seq[:, 0, :]
    index_tip = seq[:, 8, :]

    return index_tip - wrist


def dtw_distance(a, b):

    n, m = len(a), len(b)

    cost = np.full(
        (n+1, m+1),
        np.inf
    )

    cost[0,0] = 0

    for i in range(1,n+1):
        for j in range(1,m+1):

            d = np.linalg.norm(
                a[i-1]-b[j-1]
            )

            cost[i,j] = d + min(
                cost[i-1,j],
                cost[i,j-1],
                cost[i-1,j-1]
            )

    return cost[n,m]


def predict_dynamic(sequence):

    model = joblib.load(TEMPLATE_PATH)

    templates = model["templates_by_sign"]
    thresholds = model["thresholds_by_sign"]

    sequence = resample_sequence(sequence)

    motion = trajectory_features(sequence)

    best_label = "unknown"
    best_distance = float("inf")


    for label, refs in templates.items():

        distances = []

        for ref in refs:

            dist = dtw_distance(
                motion,
                ref
            )

            distances.append(dist)


        distance = min(distances)

        if distance < best_distance:
            best_distance = distance
            best_label = label


    threshold = thresholds[best_label]


    if threshold and best_distance <= threshold:
        return best_label, best_distance

    return "unknown", best_distance



def main():

    camera = Camera()
    detector = HandDetector()

    frames = []

    state = "IDLE"  # IDLE, COUNTDOWN, RECORDING
    countdown_start = None
    recording_start = None
    
    last_prediction = None
    last_distance = None


    print("SPACE = record sign")
    print("Q = quit")


    while True:

        frame = camera.get_frame()

        if frame is None:
            continue


        results = detector.detect_hands(frame)

        display = frame.copy()


        if results.hand_landmarks:

            detector.draw_landmarks(
                display,
                results
            )


        # Handle state machine for countdown and recording
        current_time = time.time()

        if state == "COUNTDOWN":
            elapsed = current_time - countdown_start
            remaining_countdown = max(0, 3.0 - elapsed)

            cv2.putText(
                display,
                f"Get Ready: {math.ceil(remaining_countdown)}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )

            if elapsed >= 3.0:
                state = "RECORDING"
                recording_start = time.time()
                frames = []
                print("Recording started")

        elif state == "RECORDING":
            elapsed_rec = current_time - recording_start
            remaining_rec = max(0, 3.0 - elapsed_rec)

            cv2.putText(
                display,
                f"RECORDING... {remaining_rec:.1f}s left",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            if results.hand_landmarks:
                # Select the first detected hand from the list
                hand_landmarks = results.hand_landmarks[0]
                
                landmarks = np.array(
                    [
                        [lm.x, lm.y, lm.z]
                        for lm in hand_landmarks
                    ],
                    dtype=np.float32
                )
                frames.append(landmarks)

            if elapsed_rec >= 3.0:
                state = "IDLE"

                if len(frames) > 5:
                    seq = np.array(frames)
                    prediction, distance = predict_dynamic(seq)

                    last_prediction = prediction
                    last_distance = distance

                    print(
                        "Prediction:",
                        prediction,
                        "distance:",
                        round(distance, 3)
                    )
                else:
                    print("Not enough frames")
                    last_prediction = "Not enough frames"
                    last_distance = 0.0

                frames = []

        # Display the latest prediction result on screen if available
        if last_prediction is not None and state == "IDLE":
            text = f"Sign: {last_prediction} (Dist: {round(last_distance, 2)})"
            cv2.putText(
                display,
                text,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )


        cv2.imshow(
            "Dynamic Sign Test",
            display
        )


        key = cv2.waitKey(1) & 0xff


        if key == ord(' ') and state == "IDLE":
            state = "COUNTDOWN"
            countdown_start = time.time()
            print("Countdown started...")

        elif key == ord('q'):
            break


    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import math
    main()