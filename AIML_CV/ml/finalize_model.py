"""
Takes the name of a winning candidate from optimize_model.py's sweep
(e.g. "trim_drop30_trees100") and rebuilds it as your actual
sign_model.joblib — including the interpretable centroids that
predict.py's hint system needs. This does NOT overwrite your current
sign_model.joblib automatically; it writes to sign_model_optimized.joblib
so you can compare side-by-side before replacing the live one.

Usage:
    python finalize_model.py trim_drop30_trees100
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
import joblib

from optimize_model import (
    ColumnSelector, load_split_data, DATASET_RAW_DIR, ML_DIR, CANDIDATES_DIR
)

MODEL_OUT = os.path.join(ML_DIR, "sign_model_optimized.joblib")


def main():
    if len(sys.argv) < 2:
        print("Usage: python finalize_model.py <candidate_name>")
        print(f"Check {CANDIDATES_DIR}/sweep_summary.json for available names.")
        sys.exit(1)

    candidate_name = sys.argv[1]
    candidate_path = os.path.join(CANDIDATES_DIR, f"{candidate_name}.joblib")
    if not os.path.exists(candidate_path):
        print(f"Candidate not found: {candidate_path}")
        sys.exit(1)

    candidate = joblib.load(candidate_path)
    keep_indices = candidate["keep_indices"]
    n_estimators = candidate["pipeline"].named_steps["clf"].n_estimators

    print(f"Rebuilding '{candidate_name}': {len(keep_indices)} features, "
          f"{n_estimators} trees")

    X_train, X_test, y_train, y_test, feature_names, encoder, X_train_raw, y_train_raw = load_split_data()

    pipeline = Pipeline([
        ("select", ColumnSelector(keep_indices)),
        ("scale", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=n_estimators, random_state=42)),
    ])
    pipeline.fit(X_train, y_train)

    # Centroids: computed from RAW (non-oversampled, non-test) training
    # samples only, same principle as the leakage-safe centroid fix.
    #
    # IMPORTANT: predict.py's get_possible_issue() compares SCALED live
    # features against these centroids, so centroids must be in the same
    # scaled space — but scaled using a scaler fit on the FULL feature
    # set, NOT the classifier pipeline's internal scaler (which may only
    # be fit on the trimmed subset if this config drops features). This
    # keeps hint generation fully decoupled from whatever trimming the
    # classifier itself uses.
    interpretable_prefixes = ("dist_", "angle_")
    interpretable_names = [c for c in feature_names if c.startswith(interpretable_prefixes)]
    interpretable_idx = [feature_names.index(c) for c in interpretable_names]

    hint_scaler = StandardScaler()
    hint_scaler.fit(X_train_raw)  # full feature set, always — independent
                                   # of keep_indices used by the classifier

    X_train_raw_scaled = hint_scaler.transform(X_train_raw)
    centroids = {}
    for class_idx, class_label in enumerate(encoder.classes_):
        rows = X_train_raw_scaled[y_train_raw == class_idx][:, interpretable_idx]
        centroids[class_label] = dict(zip(interpretable_names, rows.mean(axis=0)))

    joblib.dump({
        "pipeline": pipeline,
        "label_encoder": encoder,
        "interpretable_centroids": centroids,
        "interpretable_feature_names": interpretable_names,
        "feature_names": feature_names,   # full original order — needed so
        "kept_feature_indices": keep_indices,  # ColumnSelector stays valid
        "hint_scaler": hint_scaler,       # decoupled scaler for predict.py's
                                           # get_possible_issue() — always
                                           # fit on the full feature set
    }, MODEL_OUT, compress=3)

    size_kb = os.path.getsize(MODEL_OUT) / 1024
    print(f"Saved optimized model to {MODEL_OUT} ({size_kb:.1f} KB)")
    print("\nCompare this against your current ml/sign_model.joblib before "
          "replacing it. If satisfied, back up the old one and rename this "
          "file to sign_model.joblib.")


if __name__ == "__main__":
    main()
