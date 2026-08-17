"""
Converts downloaded sign-language VIDEO FILES into landmark sequences,
in the exact same format dynamic_data_collector.py produces from live
webcam bursts: a (T, 21, 3) numpy array saved as .npy per sample.

Once this runs, extract_dynamic_features.py and train_dynamic_templates.py
will treat webcam-recorded and video-extracted samples identically — they
just read every .npy file under dataset/raw_dynamic/<LABEL>/.

This script is Colab-safe: no cv2.imshow / waitKey / live camera access,
since those don't work in a headless Colab environment. Run this on
Colab; keep dynamic_data_collector.py (live capture) running locally.

Expected input layout:
    dataset/raw_dynamic_videos/
        hello/       *.mp4 (or .mov / .avi)
        no/          *.mp4
        please/      *.mp4
        thank_you/   *.mp4
        yes/         *.mp4

Usage:
    python video_to_landmarks.py
"""

import os
import cv2
import numpy as np
from hand_detector import HandDetector

VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "dataset", "raw_dynamic_videos")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "dataset", "raw_dynamic")

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")

# If a video runs longer than this, sample down to keep sequence length
# reasonable (extract_dynamic_features.py resamples anyway, but capping
# here avoids processing e.g. a 10-second clip frame-by-frame for nothing)
MAX_FRAMES_PER_VIDEO = 60


def landmarks_to_array(hand_landmarks):
    return np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks], dtype=np.float32)


def extract_sequence_from_video(video_path, detector):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  Could not open {video_path}")
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # evenly sample frame indices if the video is longer than our cap
    if total_frames > MAX_FRAMES_PER_VIDEO:
        sample_indices = set(
            np.linspace(0, total_frames - 1, MAX_FRAMES_PER_VIDEO).astype(int)
        )
    else:
        sample_indices = None  # use every frame

    frames = []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if sample_indices is None or frame_idx in sample_indices:
            results = detector.detect_hands(frame)
            if results.hand_landmarks:
                frames.append(landmarks_to_array(results.hand_landmarks[0]))
            # frames with no detected hand are simply skipped, not padded —
            # keeps the sequence representing real, detected motion only

        frame_idx += 1

    cap.release()

    if len(frames) < 5:
        print(f"  Only {len(frames)} frames with a detected hand — skipping "
              f"(video likely has poor hand visibility)")
        return None

    return np.stack(frames)  # (T, 21, 3)


def main():
    detector = HandDetector()

    if not os.path.isdir(VIDEO_DIR):
        raise RuntimeError(f"Expected video folder not found: {VIDEO_DIR}")

    for label in sorted(os.listdir(VIDEO_DIR)):
        label_video_dir = os.path.join(VIDEO_DIR, label)
        if not os.path.isdir(label_video_dir):
            continue

        out_label_dir = os.path.join(OUT_DIR, label)
        os.makedirs(out_label_dir, exist_ok=True)

        video_files = [f for f in sorted(os.listdir(label_video_dir))
                       if f.lower().endswith(VIDEO_EXTENSIONS)]
        print(f"--- {label}: {len(video_files)} videos ---")

        for fname in video_files:
            video_path = os.path.join(label_video_dir, fname)
            sequence = extract_sequence_from_video(video_path, detector)

            if sequence is None:
                continue

            out_name = os.path.splitext(fname)[0] + ".npy"
            out_path = os.path.join(out_label_dir, out_name)
            np.save(out_path, sequence)
            print(f"  {fname}: {sequence.shape[0]} frames -> {out_path}")

    print("\nDone. Now run extract_dynamic_features.py — it will pick up "
          "both these video-derived sequences and any webcam-recorded ones "
          "under the same dataset/raw_dynamic/<LABEL>/ folders.")


if __name__ == "__main__":
    main()
