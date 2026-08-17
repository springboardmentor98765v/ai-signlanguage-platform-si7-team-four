
import os
import time
import numpy as np
from datetime import datetime
from camera import Camera
from hand_detector import HandDetector

# --- change this per collection session ---
DYNAMIC_LABELS = ["J", "Z", "hello", "no", "please", "thank_you", "yes"]

# How long to record per burst, and at what rate
CAPTURE_DURATION_SEC = 3
TARGET_FPS = 20  # frames captured per burst (approx)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "dataset", "raw_dynamic")


def landmarks_to_array(hand_landmarks):
    """Flatten a single frame's 21 landmarks into a (21, 3) array."""
    return np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks], dtype=np.float32)


def record_burst(camera, detector, display_label):
    import cv2
    frames = []
    start = time.perf_counter()
    frame_interval = 1.0 / TARGET_FPS
    next_capture = start

    while (time.perf_counter() - start) < CAPTURE_DURATION_SEC:
        frame = camera.get_frame()
        if frame is None:
            continue

        now = time.perf_counter()
        results = detector.detect_hands(frame)

        display = frame.copy()
        if results.hand_landmarks:
            detector.draw_landmarks(display, results)
        remaining = CAPTURE_DURATION_SEC - (now - start)
        cv2.putText(display, f"RECORDING {display_label}  {remaining:.1f}s left",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Dynamic sign collector", display)
        cv2.waitKey(1)

        if now >= next_capture:
            if results.hand_landmarks:
                frames.append(landmarks_to_array(results.hand_landmarks[0]))
            else:
                frames.append(None)  # mark missed detection, filtered later
            next_capture += frame_interval

    return frames


def run_session():
    import cv2
    camera = Camera()
    detector = HandDetector()

    os.makedirs(OUT_DIR, exist_ok=True)
    print("SPACE = record burst, N = next letter, Q = quit\n")

    try:
        for label in DYNAMIC_LABELS:
            label_dir = os.path.join(OUT_DIR, label)
            os.makedirs(label_dir, exist_ok=True)
            existing = len([f for f in os.listdir(label_dir) if f.endswith(".npy")])
            print(f"--- Sign {label} (existing samples: {existing}) ---")
            print("Press SPACE to start a recording burst, N for next sign")

            while True:
                frame = camera.get_frame()
                if frame is None:
                    break
                results = detector.detect_hands(frame)
                display = frame.copy()
                if results.hand_landmarks:
                    detector.draw_landmarks(display, results)
                cv2.putText(display,
                            f"Sign: {label}",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2)

                cv2.putText(display,
                            f"Samples: {existing}",
                            (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 0),
                            2)

                cv2.putText(display,
                            "SPACE=Record  N=Next  Q=Quit",
                            (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 255),
                            2)
                cv2.imshow("Dynamic sign collector", display)
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
                        print(f"  Skipped — hand only detected in "
                              f"{detection_rate:.0%} of frames. Try again.")
                        continue

                    sequence = np.stack(valid_frames)  # (T, 21, 3)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    out_path = os.path.join(label_dir, f"{label}_{ts}.npy")
                    np.save(out_path, sequence)

                    existing += 1

                    print(f"  Saved burst #{existing} ({sequence.shape[0]} frames)")
                    print(f"  Total samples for {label}: {existing}")

    except KeyboardInterrupt:
        print("\nStopped early.")
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run_session()
