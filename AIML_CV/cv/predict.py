import os
import joblib
import sys

ML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml"))
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "sign_model.joblib")

_saved = joblib.load(MODEL_PATH)
_pipeline = _saved["pipeline"]
_label_encoder = _saved["label_encoder"]
# new labels 
_centroids = _saved.get("interpretable_centroids")
_interp_names = _saved.get("interpretable_feature_names")

_hint_scaler = _saved.get("hint_scaler")
if _hint_scaler is None:
    _hint_scaler = _pipeline.named_steps["scale"]

#Deviation threshold to manage the noisy large standard deviation posing as jitters
DEVIATION_THRESHOLD = 1.0 

# Hardcoded features for feedback generations 
# Can be enhanced or made more personalized using NLP but following the SRS it is not mentioned
FEATURE_HINTS = {
    "dist_thumb_index": "thumb-to-index finger distance",
    "dist_thumb_middle": "thumb-to-middle finger distance",
    "dist_thumb_ring": "thumb-to-ring finger distance",
    "dist_thumb_pinky": "thumb-to-pinky finger distance",
    "dist_index_middle": "index-to-middle finger spacing",
    "dist_middle_ring": "middle-to-ring finger spacing",
    "dist_ring_pinky": "ring-to-pinky finger spacing",
    "angle_index": "index finger bend",
    "angle_middle": "middle finger bend",
    "angle_ring": "ring finger bend",
    "angle_pinky": "pinky finger bend",
    "angle_thumb": "thumb bend",
}

def predict(hand, extractor):
    features = extractor.extract(hand)

    predicted_encoded = _pipeline.predict([features])[0]
    predicted_sign = _label_encoder.inverse_transform([predicted_encoded])[0]

    probabilities = _pipeline.predict_proba([features])[0]
    confidence = float(max(probabilities))

    return predicted_sign, confidence

# Function to identify the issue
def get_possible_issue(hand, extractor, target_label):
    if not _centroids or target_label not in _centroids:
        return None

    features = extractor.extract(hand)
    scaled = _hint_scaler.transform([features])[0]

    feature_names = extractor.get_feature_names()
    name_to_idx = {name: i for i, name in enumerate(feature_names)}
    target_centroid = _centroids[target_label]

    deviations = []
    for name in _interp_names:
        idx = name_to_idx[name]
        diff = abs(scaled[idx] - target_centroid[name])
        deviations.append((name, diff))

    top_feature, top_deviation = max(deviations, key=lambda x: x[1])

    if top_deviation < DEVIATION_THRESHOLD:
        return None

    label = FEATURE_HINTS.get(top_feature, top_feature)
    return f"Your {label} looks off for '{target_label}'"

# Function to feed Intern 4's Feedback Engine

def predict_with_feedback(hand, extractor, target_label=None):
    predicted_sign, confidence = predict(hand, extractor)

    if target_label is None:
        return predicted_sign, confidence, None, None

    correct = predicted_sign == target_label
    possible_issue = None if correct else get_possible_issue(hand, extractor, target_label)

    return predicted_sign, confidence, correct, possible_issue