"""
Live prediction for dynamic signs (J, Z, hello, no, please, thank_you,
yes). Takes a raw landmark sequence captured from the webcam and matches
it against the stored DTW templates.
"""

import os
import math
import joblib
import numpy as np
from extract_dynamic_features import resample_sequence, trajectory_features, RESAMPLE_STEPS
from train_dynamic_templates import dtw_distance

ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml")
TEMPLATES_PATH = os.path.join(ML_DIR, "dynamic_templates.joblib")

_saved = joblib.load(TEMPLATES_PATH)
_templates_by_sign = _saved["templates_by_sign"]
_thresholds_by_sign = _saved["thresholds_by_sign"]


def compute_confidence(distance, threshold):
    """
    Exponential decay confidence from DTW distance, scaled against the
    sign's calibrated threshold. confidence = exp(-ln(2) * distance/threshold)
      - distance=0            -> confidence=1.0  (perfect match)
      - distance=threshold    -> confidence=0.5  (right at the match boundary)
      - distance=2*threshold  -> confidence=0.25 (halves every extra threshold)
    Returns None if threshold is unavailable (sign wasn't calibrated —
    e.g. too few samples during training).
    """
    if threshold is None or threshold <= 0:
        return None
    ratio = distance / threshold
    return math.exp(-math.log(2) * ratio)


def predict_dynamic(raw_sequence):
    """
    raw_sequence: array-like of per-frame (21, 3) landmark arrays,
    captured live over a ~1.5-2s burst (variable length).

    Returns (predicted_sign, distance, matched, confidence):
      - predicted_sign: the closest-matching sign's label, or None if
        nothing matched within its calibrated threshold (i.e. "not
        recognized" rather than a forced guess — meaningful for a
        template-matching approach with no probability output)
      - distance: the DTW distance to the closest template found
      - matched: whether that distance was within threshold
      - confidence: exponential-decay confidence derived from distance
        and threshold (see compute_confidence) — reported even when
        matched=False, so a "close but not quite" attempt is
        distinguishable from a completely wrong one
    """
    raw_sequence = np.asarray(raw_sequence)
    resampled = resample_sequence(raw_sequence, target_len=RESAMPLE_STEPS)
    live_path = trajectory_features(resampled)["relative_path"]  # (T, 3)

    best_sign = None
    best_distance = float("inf")
    best_threshold = None

    for sign, templates in _templates_by_sign.items():
        threshold = _thresholds_by_sign.get(sign)
        for template in templates:
            dist = dtw_distance(live_path, template)
            if dist < best_distance:
                best_distance = dist
                best_sign = sign
                best_threshold = threshold

    if best_sign is None:
        return None, None, False, None

    matched = best_threshold is not None and best_distance <= best_threshold
    confidence = compute_confidence(best_distance, best_threshold)

    return (best_sign if matched else None), best_distance, matched, confidence
