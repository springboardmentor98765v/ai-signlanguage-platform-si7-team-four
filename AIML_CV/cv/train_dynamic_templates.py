import os
import numpy as np
import pandas as pd
import joblib

PROCESSED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "dataset", "processed_dynamic")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "ml", "dynamic_templates.joblib")

TEMPLATES_PER_SIGN = 4  # how many reference examples to keep per sign


def dtw_distance(seq_a, seq_b):
    n, m = len(seq_a), len(seq_b)
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0.0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            step_cost = np.linalg.norm(seq_a[i - 1] - seq_b[j - 1])
            cost[i, j] = step_cost + min(
                cost[i - 1, j],      # insertion
                cost[i, j - 1],      # deletion
                cost[i - 1, j - 1],  # match
            )

    return cost[n, m]


def load_sequences_for_label(index_df, label):
    rows = index_df[index_df["label"] == label]
    sequences = []
    for _, row in rows.iterrows():
        data = np.load(row["processed_file"])
        # relative_path (T, 3) is the core motion signal used for matching
        sequences.append(data["relative_path"])
    return sequences


def pick_templates(sequences, k=TEMPLATES_PER_SIGN):
    n = len(sequences)
    if n <= k:
        return list(range(n))  # not enough samples to be picky

    avg_dist = np.zeros(n)
    for i in range(n):
        dists = [dtw_distance(sequences[i], sequences[j]) for j in range(n) if j != i]
        avg_dist[i] = np.mean(dists)

    best_indices = np.argsort(avg_dist)[:k]
    return list(best_indices)


def calibrate_threshold(sequences, template_indices):
    templates = [sequences[i] for i in template_indices]
    non_template_indices = [i for i in range(len(sequences)) if i not in template_indices]

    if not non_template_indices:
        return None  # not enough held-out samples to calibrate

    nearest_distances = []
    for i in non_template_indices:
        dists = [dtw_distance(sequences[i], t) for t in templates]
        nearest_distances.append(min(dists))

    # threshold = worst-case held-out distance, with 20% headroom
    return max(nearest_distances) * 1.2


def main():
    index_df = pd.read_csv(os.path.join(PROCESSED_DIR, "index.csv"))
    labels = sorted(index_df["label"].unique())

    templates_by_sign = {}
    thresholds_by_sign = {}

    for label in labels:
        sequences = load_sequences_for_label(index_df, label)
        print(f"{label}: {len(sequences)} samples")

        if len(sequences) < 3:
            print(f"  WARNING: fewer than 3 samples for {label} — "
                  f"collect more before relying on this sign.")

        template_indices = pick_templates(sequences)
        templates_by_sign[label] = [sequences[i] for i in template_indices]

        threshold = calibrate_threshold(sequences, template_indices)
        thresholds_by_sign[label] = threshold
        print(f"  templates: {len(template_indices)}, threshold: {threshold}")

    joblib.dump({
        "templates_by_sign": templates_by_sign,
        "thresholds_by_sign": thresholds_by_sign,
    }, OUT_PATH)
    print(f"\nSaved dynamic templates to {OUT_PATH}")


if __name__ == "__main__":
    main()
