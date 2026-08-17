"""
Robustness/performance test for the DYNAMIC sign matcher (J, Z, and the
word signs), mirroring robustness_test.py's structure for the static
model. Records a short burst per sign and checks whether predict_dynamic()
correctly identifies it, across conditions and testers.

Usage:
    Edit CONDITION and TESTER below, then:
    python dynamic_robustness_test.py
    python dynamic_robustness_test.py summarize

Controls:
    SPACE = record a burst for the current sign and predict
    N     = skip to next sign
    Q     = quit
"""
"""
Four conditions = "bright_light", "dim_light", "cluttered_bg", "tilted_hand"
"""

import csv
import os
import time
import numpy as np
from datetime import datetime
from collections import Counter
from camera import Camera
from hand_detector import HandDetector
from dynamic_data_collector import record_burst
from predict_dynamic import predict_dynamic

# --- change these every run ---
CONDITION = "dim_light"
TESTER = "person2"

TEST_LABELS = ["J", "Z", "hello", "no", "please", "thank_you", "yes"]

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "dataset", "raw", "dynamic_robustness_log.csv")


def run_session():
    import cv2
    camera = Camera()
    detector = HandDetector()

    file_exists = os.path.exists(LOG_PATH)
    log_file = open(LOG_PATH, "a", newline="")
    writer = csv.writer(log_file)
    if not file_exists:
        writer.writerow(["timestamp", "condition", "tester", "target_label",
                          "predicted_label", "correct", "matched", "distance",
                          "confidence", "match_ms"])

    print(f"Condition: {CONDITION}  Tester: {TESTER}")
    print("SPACE = record burst & predict, N = skip sign, Q = quit\n")

    try:
        for label in TEST_LABELS:
            print(f"--- Sign {label}: press SPACE to record ---")
            done = False

            while not done:
                frame = camera.get_frame()
                if frame is None:
                    break

                results = detector.detect_hands(frame)
                display = frame.copy()
                if results.hand_landmarks:
                    detector.draw_landmarks(display, results)
                cv2.putText(display,
                            f"Condition:{CONDITION} Tester:{TESTER} Target:{label}  "
                            f"SPACE=record  N=skip  Q=quit",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
                cv2.imshow("Dynamic robustness test", display)
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    raise KeyboardInterrupt
                if key == ord('n'):
                    break

                if key == ord(' '):
                    frames = record_burst(camera, detector, label)
                    valid_frames = [f for f in frames if f is not None]
                    detection_rate = len(valid_frames) / max(1, len(frames))

                    if detection_rate < 0.7:
                        print(f"  Poor hand detection ({detection_rate:.0%}) during "
                              f"burst — try again")
                        continue

                    sequence = np.stack(valid_frames)

                    start = time.perf_counter()
                    predicted, distance, matched, confidence = predict_dynamic(sequence)
                    match_ms = (time.perf_counter() - start) * 1000

                    correct = (predicted == label)
                    writer.writerow([
                        datetime.now().isoformat(), CONDITION, TESTER, label,
                        predicted, correct, matched,
                        round(distance, 2) if distance is not None else None,
                        round(confidence, 4) if confidence is not None else None,
                        round(match_ms, 1)
                    ])
                    log_file.flush()
                    print(f"  Predicted: {predicted}  matched={matched}  "
                          f"distance={distance}  confidence={confidence}  "
                          f"{'correct' if correct else 'WRONG'}  ({match_ms:.1f}ms)")
                    done = True

    except KeyboardInterrupt:
        print("\nStopped early.")
    finally:
        log_file.close()
        camera.release()
        cv2.destroyAllWindows()

    print(f"\nLogged to {LOG_PATH}")


def summarize():
    import pandas as pd
    df = pd.read_csv(LOG_PATH)

    print("=== Per-condition summary (dynamic signs) ===")
    for condition, group in df.groupby("condition"):
        acc = group["correct"].astype(bool).mean()
        match_rate = group["matched"].astype(bool).mean()
        avg_conf = group["confidence"].mean()
        avg_ms = group["match_ms"].mean()
        print(f"\n{condition}  (n={len(group)})")
        print(f"  accuracy: {acc:.0%}")
        print(f"  match rate (found a sign within threshold): {match_rate:.0%}")
        print(f"  avg confidence: {avg_conf:.2f}")
        print(f"  avg matching time: {avg_ms:.1f}ms")

    print("\n=== Per-tester summary ===")
    for tester, group in df.groupby("tester"):
        acc = group["correct"].astype(bool).mean()
        print(f"\n{tester}  (n={len(group)})")
        print(f"  accuracy: {acc:.0%}")

    print("\n=== Per-sign summary ===")
    for label, group in df.groupby("target_label"):
        acc = group["correct"].astype(bool).mean()
        avg_dist = group["distance"].mean()
        avg_conf = group["confidence"].mean()
        print(f"\n{label}  (n={len(group)})")
        print(f"  accuracy: {acc:.0%}, avg distance: {avg_dist:.2f}, avg confidence: {avg_conf:.2f}")

        wrong = group[group["correct"] == False]
        if len(wrong):
            mistakes = Counter(wrong["predicted_label"].fillna("NOT_RECOGNIZED"))
            print(f"    Common mistakes: {mistakes.most_common(3)}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summarize":
        summarize()
    else:
        run_session()
