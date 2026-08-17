# Model Card — Sign Language Recognition
**Milestone 3 update — Day 10**

## Overview
Two-part recognition system:
- **Static model**: A–Z RandomForest classifier (feature selection +
  StandardScaler + RandomForestClassifier), trained on merged Kaggle +
  real webcam data. Handles all letters except J and Z.
- **Dynamic model**: DTW (Dynamic Time Warping) template-matching
  system for motion-based signs — J, Z, and word signs (hello, no,
  please, thank_you, yes). Not a trained classifier; matches a live
  landmark trajectory against stored reference templates.

---

## Static model

### Training data
- Kaggle ASL Alphabet (image-per-class, all 26 letters + `del`)
- Real webcam samples, all 26 letters covered (Milestone 3 closed the
  gap from Milestone 2's 15+ letters)
- Webcam data oversampled (~3x, target ~35% effective share) to avoid
  being drowned out by Kaggle's larger volume — oversampling applied
  **only to the training split**, after the train/test split, to avoid
  data leakage (see "Known fixes applied")

### Accuracy
- Held-out test accuracy (leakage-free split): **0.9901** (RandomForest,
  best of KNN/RF/SVM/XGBoost comparison)
- Cross-validation accuracy (train set): 0.9934 ± 0.0009
- Held exactly at 0.9901 after Day 8 optimization — zero measured cost

### Real-world robustness testing
Tested across 4 conditions, 2 testers, ~11 reps per letter per
condition per tester (~1,167 total logged predictions):

| Condition | Hand detection rate | Accuracy | Avg confidence | Avg prediction time |
|---|---|---|---|---|
| bright_light | 100% | 94% | 0.90 | 48.3ms |
| cluttered_bg | 100% | 97% | 0.90 | 46.7ms |
| dim_light | 100% | 98% | 0.88 | 45.7ms |
| tilted_hand | 100% | 96% | 0.87 | 47.0ms |

| Tester | Samples | Accuracy |
|---|---|---|
| person1 | 647 | 96% |
| person2 | 520 | 97% |

Accuracy is consistent across both testers — no evidence of overfitting
to one person's hand shape or skin tone.

### Known limitations

**R — severe, confirmed failure (highest priority, deferred to Milestone 4).**
R fails in every condition, consistently misclassified as U:
bright_light 27% (7/11→U), cluttered_bg 50% (6/12→U), dim_light 55%
(5/11→U), tilted_hand 36% (7/11→U). Consistent direction across every
condition and both testers rules out noise.

*Root cause (diagnosed):* current `dist_`/`angle_` features don't
separate R (crossed index/middle fingers) from U (parallel index/middle
fingers) — differences as small as 1–5° / 0.05 units, far less than
other letter pairs show.

*Fix designed but not implemented:* a finger-crossing feature
(`feat_finger_crossing` — sign of `(index_mcp.x - middle_mcp.x) *
(index_tip.x - middle_tip.x)`, negative when fingers have crossed) was
designed and prototyped. **Deliberately deferred to Milestone 4** per
team decision — the model achieves ~99% overall accuracy, and the team
chose not to risk destabilizing a working model to fix two letters
mid-milestone. Diagnostic script (`r_and_u_test.py`) and the designed
fix are ready to implement directly when Milestone 4 begins.

**Q → N — newly observed, needs investigation.** Q dropped to 82%
(bright_light) and 83% (cluttered_bg), misses concentrated on N (3 of 4
total misses), while dim_light/tilted_hand stayed at 100%. Same
repeated, same-direction signature as R — flagged for follow-up
alongside the R/U fix in Milestone 4.

**J and Z — routed to the dynamic matcher, not a static-model concern.**
J showed 64–91% static accuracy (mostly confused with I), consistent
with real ASL J being a motion sign that a static pose can't reliably
represent. Both J and Z are served by the dynamic matcher in the live
product; static accuracy figures are retained here only as supporting
evidence for that routing decision.

**Fragile-confidence watch list.** Correct but low-confidence
predictions: Q (0.62–0.83), T (0.72–0.79), U (0.80–0.86), X (0.70–0.84),
P (0.80–0.91), H (0.84–0.96). Worth a confidence-threshold pass in
Milestone 4.

**Other single-miss letters — evaluated, not a real issue.**
B/tilted (→W), C/tilted (→O), I/bright (→Y), N/bright (→M), K/dim (→V),
T/tilted (→X), U/bright (→V) — isolated, no repeated pattern. No action
needed.

### Optimization (Day 8)
Selected config: **58 features** (20 lowest-importance features dropped
from the original 78, ranked via `feature_importances_`), **100 trees**
(down from 200). Chosen from a 6-config sweep — pure feature trimming
at 200 trees consistently underperformed baseline on both speed and
accuracy; tree-count reduction was the config that actually delivered
the win.

| | Before | After |
|---|---|---|
| Test accuracy | 0.9901 | 0.9901 (unchanged) |
| Avg prediction latency (benchmark) | 9.77ms | 10.56ms |
| Model file size | 5587 KB | 2648 KB (−53%) |
| Feature count | 78 | 58 |
| Trees | 200 | 100 |

Confirmed accuracy did not drop after optimization.

*Alternative considered:* a more aggressive config (58 features, 50
trees) reached 1335 KB (−76%) and ~4.75ms latency at a small accuracy
cost (0.9887, −0.14 points). Not selected, but documented for Milestone
4 in case deployment constraints call for a smaller footprint.

---

## Dynamic model

### Approach
DTW template-matching for J, Z, hello, no, please, thank_you, yes.
Reference templates built from 20 downloaded videos per word sign
(`video_to_landmarks.py`) plus live webcam bursts for J/Z
(`dynamic_data_collector.py`), processed via `extract_dynamic_features.py`
(resampling + trajectory features) and `train_dynamic_templates.py`
(medoid template selection + threshold calibration). Live matching via
`predict_dynamic()`, exposed through the `/predict_dynamic` API
endpoint.

**Confidence scoring:** derived from DTW distance via exponential decay:
`confidence = exp(-ln(2) * distance/threshold)` — 1.0 at a perfect
match, 0.5 exactly at the threshold boundary, halving for each
additional threshold's worth of distance.

### Real-world robustness testing
Tested across the same 4 conditions and 2 testers, 24 reps per sign
(168 total):

| Condition | Accuracy | Match rate | Avg confidence | Avg matching time |
|---|---|---|---|---|
| bright_light | 93% | 100% | 0.83 | 59.8ms |
| cluttered_bg | 98% | 100% | 0.83 | 59.7ms |
| dim_light | 95% | 100% | 0.83 | 58.6ms |
| tilted_hand | 95% | 100% | 0.82 | 60.3ms |

| Tester | Accuracy |
|---|---|
| person1 | 94% |
| person2 | 96% |

| Sign | Accuracy | Avg distance | Avg confidence |
|---|---|---|---|
| J | 100% | 0.84 | 0.80 |
| Z | 88% | 1.22 | 0.62 |
| hello | 79% | 1.29 | 0.82 |
| no | 100% | 1.24 | 0.89 |
| please | 100% | 1.20 | 0.92 |
| thank_you | 100% | 1.15 | 0.89 |
| yes | 100% | 0.86 | 0.84 |

### Known limitations

**hello / thank_you / Z confusion cluster.** All 5 of `hello`'s misses
landed on `thank_you`. `Z`'s 3 misses split between `hello` (2) and
`thank_you` (1). Consistent, repeated, same-direction pattern — a real
confusion cluster, likely reflecting genuine trajectory similarity
between these signs' motions, not noise.

**Match rate is 100% even on wrong predictions.** Every tested attempt
found *some* match within threshold, including the incorrect ones
above. `calibrate_threshold()` only validates a sign's distance to its
own held-out samples — it doesn't check that other signs' distances
stay safely outside the threshold, so thresholds are currently tuned
for within-class tolerance only, not cross-class rejection.
*Recommended follow-up (Milestone 4):* recalibrate using cross-class
distances as a lower bound, particularly for the hello/thank_you/Z
cluster.

---

## Known fixes already applied
- **Train/test leakage fix:** webcam oversampling previously happened
  before the train/test split, allowing near-duplicate rows into both
  splits and inflating test accuracy (was ~0.9944, leakage-inflated).
  Fixed by splitting on raw data first, oversampling only the training
  portion.
- **Centroid computation fix:** centroids (used by `predict.py`'s hint
  system) computed from raw, non-oversampled, non-test training samples
  only, for the same reason.
- **Hint-scaler decoupling fix:** Day 8 optimization trimmed the
  classifier's feature set, which broke `predict.py`'s hint generation
  (it reused the classifier pipeline's internal scaler, now fit on
  fewer features than the live feature vector). Fixed with a dedicated
  hint scaler, always fit on the full feature set, fully decoupled from
  classifier trimming.

## API
- `POST /predict` — multipart file upload (`file`), optional `target_sign`
  form field.
  - Without `target_sign`: returns `predicted_sign`, `confidence`,
    `hand_detected`.
  - With `target_sign` (practice mode): also returns `correct` and
    `possible_issue` — a plain-language hint (e.g. *"Your thumb bend looks
    off for 'N'"*), or `null` if there's no meaningful issue.
- `POST /predict_dynamic` — multipart file upload (`files`, a **list** of
  frames captured over a recording burst — NOT a single image), for J,
  Z, and word signs (hello, no, please, thank_you, yes).
  - Returns `predicted_sign`, `matched`, `confidence`, `distance`,
    `hand_detected_frames`, `total_frames`.
  - `predicted_sign` is `null` whenever `matched` is `false` — either no
    template matched within threshold, or too few frames had a
    detectable hand (< 5 frames or < 50% detection rate); check
    `hand_detected_frames` vs. `total_frames` to distinguish a bad burst
    from a genuine no-match.
  - `confidence` is derived from DTW distance (not a classifier
    probability like `/predict`'s) — 1.0 at a perfect match, 0.5 at the
    threshold boundary, decaying exponentially beyond that.
- `GET /health` — liveness check.
- Run with `uvicorn main:app --reload --port 8001` from `api/` (port
  8001 to match `docker-compose.yml`); interactive docs at
  `http://127.0.0.1:8001/docs`.

## Files to Hand Off
- `ml/sign_model.joblib` — static model: trained pipeline (58 features,
  100 trees, post-Day 8 optimization) + label encoder + per-letter
  feature centroids + dedicated hint scaler (used for hint generation).
- `ml/dynamic_templates.joblib` — dynamic model: reference DTW
  trajectory templates + calibrated per-sign thresholds for J, Z, hello,
  no, please, thank_you, yes.
- `ml/confusion_matrix.png` — latest per-letter static confusion matrix
  (leakage-free split).
- `models/hand_landmarker.task` — MediaPipe hand landmark model.
- `requirements.txt` — full dependency list.
- `MODEL_CARD.md` — this document.

## Before Production Deploy
- `api/main.py` currently allows CORS from `*` (marked `TODO` in the
  file). Restrict to the actual frontend origin before the real
  demo/deploy.
- Dynamic model thresholds are calibrated for within-class tolerance
  only, not cross-class rejection (see "Known limitations" above) — the
  hello/thank_you/Z confusion cluster is a live risk in a demo if those
  three signs come up back-to-back. Worth a quick recalibration pass or,
  at minimum, briefing the demo presenter on it before Milestone 4's fix
  lands.
- `MIN_DETECTION_RATE` (0.5) and the 5-frame minimum in
  `/predict_dynamic` were chosen as reasonable defaults, not tuned
  against real frontend recording behavior — worth revisiting once
  Intern 1's actual capture flow (burst duration, frame rate) is
  finalized, in case it sends fewer/more frames than assumed here.
- Run in production without `--reload`: `uvicorn main:app --host 0.0.0.0
  --port 8001`, matching what's already hardcoded in `main.py`'s
  `if __name__ == "__main__"` block.

## Distribution
Final optimized static model (`sign_model.joblib`, 58 features / 100
trees), `dynamic_templates.joblib`, and this model card shared with
Intern 4 (business logic/feedback) and Intern 5 (DevOps/deployment) per
SRS requirement.