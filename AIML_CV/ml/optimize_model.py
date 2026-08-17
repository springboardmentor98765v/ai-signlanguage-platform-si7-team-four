"""
Day 8 optimization sweep.

Trains your current baseline config exactly as-is, then several candidate
"lighter" configs, and prints a comparison table of accuracy, average
prediction latency, and saved file size for each. Nothing here overwrites
your existing sign_model.joblib — it only writes candidate files to
ml/optimization_candidates/ so you can compare before choosing one.

Uses the same leakage-safe split-then-oversample logic as your fixed
train_model.py: split on raw data first, oversample webcam data only
within the training split.

Usage:
    python optimize_model.py
"""

import os
import time
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import accuracy_score
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_RAW_DIR = os.path.join(BASE_DIR, "..", "dataset", "raw")
ML_DIR = os.path.join(BASE_DIR, "..", "ml")
CANDIDATES_DIR = os.path.join(ML_DIR, "optimization_candidates")

WEBCAM_CSV = os.path.join(DATASET_RAW_DIR, "dataset.csv")
KAGGLE_CSV = os.path.join(DATASET_RAW_DIR, "kaggle_features.csv")

WEBCAM_TARGET_SHARE = 0.35

# How many of the LEAST important features to drop, per candidate config.
# 0 = baseline (no trimming). Tune these based on how many features you
# actually have (78 currently) — don't drop more than you have.
FEATURE_TRIM_CANDIDATES = [0, 20, 30, 40]

# Tree count candidates to try (on top of the best feature-trim result)
N_ESTIMATORS_CANDIDATES = [200, 100, 50]

N_TIMING_RUNS = 200  # how many single-sample predictions to average for latency


class ColumnSelector(BaseEstimator, TransformerMixin):
    """
    Selects a fixed set of feature columns by POSITION (not name), so this
    works whether the pipeline is fed a pandas DataFrame or a plain
    list/array at inference time — both are indexed the same way, as long
    as the caller always builds the feature vector in the same fixed order
    (which extractor.get_feature_names() / extractor.extract() guarantee).
    """
    def __init__(self, keep_indices):
        self.keep_indices = keep_indices

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if hasattr(X, "iloc"):  # pandas DataFrame
            return X.iloc[:, self.keep_indices].values
        X = np.asarray(X)
        return X[:, self.keep_indices]


def load_split_data():
    """Same leakage-safe loading as train_model.py: split raw data first,
    oversample webcam data only within the training split."""
    sources = {WEBCAM_CSV: "webcam", KAGGLE_CSV: "kaggle"}
    frames = []
    for path, source in sources.items():
        frame = pd.read_csv(path)
        frame["label"] = frame["label"].astype(str).str.strip()
        frame["_source"] = source
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True).dropna()

    X_raw = df.drop(columns=["label", "_source"])
    feature_names = list(X_raw.columns)
    encoder = LabelEncoder()
    y_raw = encoder.fit_transform(df["label"])

    X_train_raw, X_test, y_train_raw, y_test = train_test_split(
        X_raw, y_raw, test_size=0.2, stratify=y_raw, random_state=42
    )

    train_df = X_train_raw.copy()
    train_df["label"] = encoder.inverse_transform(y_train_raw)
    train_df["_source"] = df.loc[X_train_raw.index, "_source"].values

    webcam_df = train_df[train_df["_source"] == "webcam"]
    kaggle_df = train_df[train_df["_source"] == "kaggle"]
    if len(webcam_df) > 0 and len(kaggle_df) > 0:
        factor = (WEBCAM_TARGET_SHARE * len(kaggle_df)) / \
                 ((1 - WEBCAM_TARGET_SHARE) * len(webcam_df))
        factor = max(1, round(factor))
        webcam_oversampled = pd.concat([webcam_df] * factor, ignore_index=True)
        train_df = pd.concat([webcam_oversampled, kaggle_df], ignore_index=True)

    X_train = train_df.drop(columns=["label", "_source"])
    y_train = encoder.transform(train_df["label"])

    return X_train, X_test, y_train, y_test, feature_names, encoder, X_train_raw, y_train_raw


def measure_latency(pipeline, X_test, n_runs=N_TIMING_RUNS):
    """Average single-sample prediction time in milliseconds — pure model
    inference only, not camera/detection overhead."""
    sample = X_test.iloc[[0]]
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        pipeline.predict(sample)
        times.append((time.perf_counter() - start) * 1000)
    return float(np.mean(times))


def build_pipeline(keep_indices, n_estimators):
    return Pipeline([
        ("select", ColumnSelector(keep_indices)),
        ("scale", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=n_estimators, random_state=42)),
    ])


def evaluate_config(name, keep_indices, n_estimators, X_train, y_train, X_test, y_test):
    pipeline = build_pipeline(keep_indices, n_estimators)
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    acc = accuracy_score(y_test, preds)
    latency_ms = measure_latency(pipeline, X_test)

    os.makedirs(CANDIDATES_DIR, exist_ok=True)
    out_path = os.path.join(CANDIDATES_DIR, f"{name}.joblib")
    joblib.dump({"pipeline": pipeline, "keep_indices": keep_indices}, out_path, compress=3)
    size_kb = os.path.getsize(out_path) / 1024

    print(f"{name:25s}  n_features={len(keep_indices):3d}  "
          f"n_estimators={n_estimators:4d}  acc={acc:.4f}  "
          f"latency={latency_ms:6.2f}ms  size={size_kb:8.1f}KB")

    return {
        "name": name, "n_features": len(keep_indices), "n_estimators": n_estimators,
        "accuracy": acc, "latency_ms": latency_ms, "size_kb": size_kb,
    }


def main():
    print("Loading and splitting data (leakage-safe)...")
    X_train, X_test, y_train, y_test, feature_names, encoder, X_train_raw, y_train_raw = load_split_data()
    print(f"Total features available: {len(feature_names)}\n")

    results = []

    # --- Step 1: baseline, full features, current n_estimators (200) ---
    all_indices = list(range(len(feature_names)))
    baseline = evaluate_config("baseline_full", all_indices, 200,
                                X_train, y_train, X_test, y_test)
    results.append(baseline)

    # --- Step 2: get feature importances from the baseline model to rank features ---
    baseline_pipeline = build_pipeline(all_indices, 200)
    baseline_pipeline.fit(X_train, y_train)
    importances = baseline_pipeline.named_steps["clf"].feature_importances_
    ranked = sorted(zip(feature_names, all_indices, importances),
                     key=lambda x: x[2], reverse=True)

    print("\nTop 15 most important features:")
    for fname, _, imp in ranked[:15]:
        print(f"  {fname:25s} {imp:.4f}")
    print("\nBottom 10 least important features:")
    for fname, _, imp in ranked[-10:]:
        print(f"  {fname:25s} {imp:.4f}")
    print()

    # --- Step 3: trimmed-feature candidates, same n_estimators (200) ---
    for drop_n in FEATURE_TRIM_CANDIDATES:
        if drop_n == 0:
            continue  # already have baseline_full
        keep = [idx for _, idx, _ in ranked[:len(ranked) - drop_n]]
        keep = sorted(keep)  # keep original column order
        name = f"trim_drop{drop_n}"
        result = evaluate_config(name, keep, 200, X_train, y_train, X_test, y_test)
        results.append(result)

    # --- Step 4: pick the best trimmed config so far by accuracy, then
    #             sweep n_estimators on top of it ---
    trimmed_results = [r for r in results if r["name"] != "baseline_full"]
    best_trim = max(trimmed_results, key=lambda r: r["accuracy"]) if trimmed_results else baseline
    best_drop_n = int(best_trim["name"].replace("trim_drop", "")) if "trim_drop" in best_trim["name"] else 0
    best_keep = sorted([idx for _, idx, _ in ranked[:len(ranked) - best_drop_n]])

    print(f"\nUsing best trimmed feature set ({best_trim['name']}) to sweep n_estimators:")
    for n_est in N_ESTIMATORS_CANDIDATES:
        if n_est == 200:
            continue  # already covered
        name = f"{best_trim['name']}_trees{n_est}"
        result = evaluate_config(name, best_keep, n_est, X_train, y_train, X_test, y_test)
        results.append(result)

    # --- Summary ---
    print("\n=== Full comparison (sorted by accuracy) ===")
    results_sorted = sorted(results, key=lambda r: r["accuracy"], reverse=True)
    for r in results_sorted:
        print(f"{r['name']:25s}  acc={r['accuracy']:.4f}  "
              f"latency={r['latency_ms']:6.2f}ms  size={r['size_kb']:8.1f}KB  "
              f"features={r['n_features']}  trees={r['n_estimators']}")

    summary_path = os.path.join(CANDIDATES_DIR, "sweep_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to {summary_path}")
    print("\nEach candidate model + its kept feature indices are saved individually "
          f"in {CANDIDATES_DIR}/<name>.joblib — inspect the table above, pick the "
          "config with the best speed/size for an acceptable accuracy drop, "
          "then run finalize_model.py with that name.")


if __name__ == "__main__":
    main()
