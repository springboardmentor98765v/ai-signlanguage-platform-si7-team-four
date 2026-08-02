"""
Four conditions = "bright_light", "dim_light", "cluttered_bg", "tilted_hand"
"""

import csv
import os
import time
from datetime import datetime
from collections import Counter
from camera import Camera
from hand_detector import HandDetector
from feature_extractor import FeatureExtractor
from predict import predict_with_feedback
import string

# --- change this every run ---
CONDITION = "bright_light"

# Test all 26 uppercase alphabet letters

TEST_LABELS = list(string.ascii_uppercase)

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "dataset", "raw", "robustness_log.csv")


def run_session():
    camera = Camera()
    detector = HandDetector()
    extractor = FeatureExtractor()

    file_exists = os.path.exists(LOG_PATH)
    log_file = open(LOG_PATH, "a", newline="")
    writer = csv.writer(log_file)
    if not file_exists:
        writer.writerow(["timestamp", "condition", "target_label", "predicted_label",
                          "correct", "confidence", "hand_detected", "predict_ms"])

    print(f"Condition: {CONDITION}")
    print("SPACE = capture, N = skip letter, Q = quit\n")

    import cv2  # local import keeps this file's top-level deps minimal

    try:
        for label in TEST_LABELS:
            print(f"--- Show letter {label}, press SPACE ---")
            captured = False

            while not captured:
                frame = camera.get_frame() 
                if frame is None:
                    break

                results = detector.detect_hands(frame)

                display = frame.copy()

                if results.hand_landmarks:
                    detector.draw_landmarks(display, results)

                cv2.putText(display, f"Condition: {CONDITION}  Target: {label}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display, "SPACE=capture  N=skip  Q=quit",
                            (10, display.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (255, 255, 255), 1)
                cv2.imshow("Day 8 robustness test", display)
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    raise KeyboardInterrupt
                if key == ord('n'):
                    break

                if key == ord(' '):
                    start = time.perf_counter()
                    results = detector.detect_hands(frame)

                    if not results.hand_landmarks:
                        writer.writerow([datetime.now().isoformat(), CONDITION, label,
                                          None, False, 0.0, False, None])
                        log_file.flush()
                        print("  No hand detected — logged as a miss")
                        captured = True
                        continue

                    hand = results.hand_landmarks[0]
                    predicted, confidence, correct, _ = predict_with_feedback(
                        hand, extractor, target_label=label
                    )
                    elapsed_ms = (time.perf_counter() - start) * 1000

                    writer.writerow([datetime.now().isoformat(), CONDITION, label,
                                      predicted, correct, round(confidence, 4),
                                      True, round(elapsed_ms, 1)])
                    log_file.flush()
                    print(f"  Predicted {predicted} (conf {confidence:.2f}, "
                          f"{'correct' if correct else 'WRONG'}, {elapsed_ms:.1f}ms)")
                    captured = True

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

    print("=== Per-condition summary ===")
    for condition, group in df.groupby("condition"):
        detected = group["hand_detected"].astype(bool)
        detect_rate = detected.mean()
        subset = group[detected]
        accuracy = subset["correct"].astype(bool).mean() if len(subset) else float("nan")
        avg_conf = subset["confidence"].mean() if len(subset) else float("nan")
        avg_ms = subset["predict_ms"].mean() if len(subset) else float("nan")

        print(f"\n{condition}  (n={len(group)})")
        print(f"  hand detection rate: {detect_rate:.0%}")
        print(f"  accuracy (when hand detected): {accuracy:.0%}")
        print(f"  avg confidence: {avg_conf:.2f}")
        print(f"  avg prediction time: {avg_ms:.1f}ms")
    
    print("\n=== Per-letter robustness summary ===")
    for label, group in df.groupby("target_label"):
        print(f"\nLetter {label}")
        for condition, cond_group in group.groupby("condition"):
            detected = cond_group[
                cond_group["hand_detected"] == True
            ]
            if len(detected) == 0:
                continue
            accuracy = detected["correct"].astype(bool).mean()
            avg_conf = detected["confidence"].mean()
            print(
                f"  {condition}: "
                f"accuracy={accuracy:.0%}, "
                f"confidence={avg_conf:.2f}, "
                f"samples={len(detected)}"
            )
            # Show what wrong predictions this letter becomes
            wrong = detected[detected["correct"] == False]

            if len(wrong):
                mistakes = Counter(wrong["predicted_label"])
                print(
                f"    Common mistakes: {mistakes.most_common(3)}"
            )

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summarize":
        summarize()
    else:
        run_session()
