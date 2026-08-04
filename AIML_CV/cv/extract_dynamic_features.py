
import os
import numpy as np
import pandas as pd
from feature_extractor import FeatureExtractor

RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "dataset", "raw_dynamic")
PROCESSED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "dataset", "processed_dynamic")

RESAMPLE_STEPS = 20  # every sequence gets normalized to this many frames


def resample_sequence(seq, target_len=RESAMPLE_STEPS):
    """Linearly interpolate a (T, 21, 3) sequence to (target_len, 21, 3)."""
    t_orig = np.linspace(0, 1, num=seq.shape[0])
    t_new = np.linspace(0, 1, num=target_len)

    resampled = np.zeros((target_len, seq.shape[1], seq.shape[2]), dtype=np.float32)
    for landmark_idx in range(seq.shape[1]):
        for axis in range(seq.shape[2]):
            resampled[:, landmark_idx, axis] = np.interp(
                t_new, t_orig, seq[:, landmark_idx, axis]
            )
    return resampled


def trajectory_features(seq):
    wrist = seq[:, 0, :]
    index_tip = seq[:, 8, :]

    # Path of the index fingertip relative to the wrist (removes camera
    # position/hand-location dependence, keeps the SHAPE of the motion)
    relative_path = index_tip - wrist  # (T, 3)

    start_to_end = relative_path[-1] - relative_path[0]
    total_path_length = np.sum(
        np.linalg.norm(np.diff(relative_path, axis=0), axis=1)
    )

    return {
        "relative_path": relative_path,       # (T, 3) — full normalized trajectory
        "start_to_end_delta": start_to_end,    # (3,)   — net displacement
        "path_length": total_path_length,      # scalar — how much motion occurred
    }


def per_frame_features(seq, extractor):
    frame_feats = []
    for frame_landmarks in seq:
        # Adapt this call to match your FeatureExtractor's actual signature —
        # assumes it accepts an (21, 3) array or a landmarks-like object.
        feats = extractor.extract(frame_landmarks)
        frame_feats.append(feats)
    return np.array(frame_feats, dtype=np.float32)  # (T, 78)


def main():
    extractor = FeatureExtractor()
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    index_rows = []

    for label in sorted(os.listdir(RAW_DIR)):
        label_dir = os.path.join(RAW_DIR, label)
        if not os.path.isdir(label_dir):
            continue

        out_label_dir = os.path.join(PROCESSED_DIR, label)
        os.makedirs(out_label_dir, exist_ok=True)

        for fname in sorted(os.listdir(label_dir)):
            if not fname.endswith(".npy"):
                continue

            raw_seq = np.load(os.path.join(label_dir, fname))  # (T, 21, 3)
            resampled = resample_sequence(raw_seq)

            traj = trajectory_features(resampled)
            frame_feats = per_frame_features(resampled, extractor)

            out_path = os.path.join(out_label_dir, fname.replace(".npy", "_processed.npz"))
            np.savez(
                out_path,
                relative_path=traj["relative_path"],
                start_to_end_delta=traj["start_to_end_delta"],
                path_length=traj["path_length"],
                per_frame_features=frame_feats,
            )

            index_rows.append({"label": label, "raw_file": fname, "processed_file": out_path})
            print(f"Processed {label}/{fname} -> {out_path}")

    index_df = pd.DataFrame(index_rows)
    index_csv = os.path.join(PROCESSED_DIR, "index.csv")
    index_df.to_csv(index_csv, index=False)
    print(f"\nSaved index of {len(index_df)} processed samples to {index_csv}")


if __name__ == "__main__":
    main()
