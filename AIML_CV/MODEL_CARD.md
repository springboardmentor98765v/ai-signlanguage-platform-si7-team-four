# Sign Language Letter Recognition — Model Card

**Owner:** Intern 3 (AI/ML & Computer Vision) · **Milestone:** 2

## Overview
Predicts a static ASL handshape (A–Z) from a single
webcam frame. Powers the practice/assessment flow of the AI Sign Language
Platform.

## Model
Best of four candidates compared (KNN, RandomForest, SVM, XGBoost) by
held-out test accuracy: currently **RandomForestClassifier(n_estimators=200)**
in a `StandardScaler` pipeline (RandomForest and XGBoost tied on test
accuracy at 0.9945 in the latest run; RandomForest won on CV score).
*Note: this selection is made automatically by comparing test accuracy
after oversampling, which has a train/test leakage caveat (see Accuracy
below) — the "best" pick has shifted between runs (XGBoost, then
RandomForest) and shouldn't be read as a precise ranking between
algorithms.*

Input: 78 engineered features per detected hand — 63 landmark coordinates
(normalized to wrist position and wrist-to-middle-finger-base scale),
7 fingertip distances, 5 finger-bend angles, 3 palm-orientation values.

## Training Data
- ~12,147 images from the Kaggle ASL Alphabet dataset, features extracted
  via MediaPipe.
- 884 real webcam captures from the team, across multiple contributors
  (relabeled once after an M/N/P/T mix-up was found in the original
  collection).
- Webcam samples oversampled ~7× during training so real-world capture
  patterns aren't drowned out by the larger Kaggle set.
- `del`, `space`, `nothing` should be excluded — **`del` (381 rows) is
  still present in the current training run**, meaning the deployed model
  can predict a "delete gesture" class that isn't wanted. Needs
  `drop_del_rows.py` (or a fresh extraction with the corrected exclusion
  filter) before the final handoff.
- **`J` has zero webcam samples.** It's a motion-based sign; a static frame
  can only approximate it. Its performance relies entirely on Kaggle data
  and was not covered by real-world (Day 8) testing.

## Accuracy
Held-out split of the training distribution: **~99%** — treat this as an
upper bound, not a real-world estimate (oversampled webcam rows can appear
on both sides of that split).

Real webcam accuracy (Day 8 testing — 8 letters × 8 samples per condition,
small sample, directional). This is after retraining on the relabeled
M/N/P/T webcam data with oversampling — a genuine improvement, since this
metric is measured with fresh camera captures and isn't subject to the
leakage caveat above:

| Condition | Accuracy | Avg. confidence | Avg. prediction time |
|---|---|---|---|
| Bright light | 88% | 0.77 | 68ms |
| Cluttered background | 88% | 0.76 | 75ms |
| Dim light | 100% | 0.68 | 66ms |
| Tilted hand | 88% | 0.68 | 73ms |

Average real-world accuracy: ~91% (up from ~78% before the relabel/retrain).
Hand-detection rate: 100% across all tested conditions.
Prediction speed: 65–75ms end to end, well under the ~1–2s target.

## Known Limitations
- Confidence scores run moderate (0.5–0.8) even when correct, and aren't
  well-calibrated — don't treat them as a true probability of correctness.
- **`del` (381 samples) is still in the current training data** — see
  Training Data above. The deployed model can currently predict a delete
  gesture that isn't intended to be part of the letter set.
- `J` is unverified in real-world conditions (see Training Data).
- **`O` is still being consistently misclassified as `J`**, now confirmed
  across two separate training runs (bright light and cluttered background
  fail every time; dim light and tilted hand technically pass but with very
  low confidence, ~0.3, suggesting a lucky guess rather than real
  recognition). The M/N/P/T relabel fix didn't touch O. Points to the same
  kind of webcam data/labeling issue as M/N/P/T had — **still open,
  deliberately deferred, needs the same data check applied to O's webcam
  captures.**
- **`N` fails specifically under tilted-hand conditions**, misread as `M`,
  in two separate test runs now — looks like genuine angle-sensitivity
  (N and M are a classically confusable ASL pair) rather than a labeling
  issue. A few tilted-angle webcam samples for N would likely help.
- Day 8 per-condition numbers use 8 samples/letter; the per-letter
  breakdown used only 1 sample per letter per condition, so any single
  letter's accuracy there is either 0% or 100% and shouldn't be read as
  precise — it's useful for spotting patterns (like O→J or N→M), not as a
  calibrated number.
- The "best model" selection in `train_model.py` compares algorithms using
  a metric affected by train/test leakage from oversampling (see Model
  above) — the current XGBoost pick shouldn't be assumed definitively
  better than RandomForest for real-world use; both have performed well in
  live testing across different training runs.

## API
- `POST /predict` — multipart file upload (`file`), optional `target_sign`
  form field.
  - Without `target_sign`: returns `predicted_sign`, `confidence`,
    `hand_detected`.
  - With `target_sign` (practice mode): also returns `correct` and
    `possible_issue` — a plain-language hint (e.g. *"Your thumb bend looks
    off for 'N'"*), or `null` if there's no meaningful issue.
- `GET /health` — liveness check.
- Run with `uvicorn main:app --reload` from `api/`; interactive docs at
  `http://127.0.0.1:8000/docs`.

## Files to Hand Off
- `ml/sign_model.joblib` — trained pipeline + label encoder + per-letter
  feature centroids (used for hint generation).
- `ml/confusion_matrix.png` — latest per-letter confusion matrix.
- `models/hand_landmarker.task` — MediaPipe hand landmark model.
- `requirements.txt` — full dependency list.

## Before Production Deploy
`api/main.py` currently allows CORS from `*` (marked `TODO` in the file).
Restrict to the actual frontend origin before the real demo/deploy.
