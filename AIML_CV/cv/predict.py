import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "sign_model.joblib")

_saved = joblib.load(MODEL_PATH)
_pipeline = _saved["pipeline"]
_label_encoder = _saved["label_encoder"]
# new labels 
_centroids = _saved.get("interpretable_centroids")
_interp_names = _saved.get("interpretable_feature_names")

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
    """
    hand: raw MediaPipe hand landmarks (21 points) for one detected hand
    extractor: a FeatureExtractor instance

    Returns (predicted_sign: str, confidence: float)
    """
    features = extractor.extract(hand)

    predicted_encoded = _pipeline.predict([features])[0]
    predicted_sign = _label_encoder.inverse_transform([predicted_encoded])[0]

    probabilities = _pipeline.predict_proba([features])[0]
    confidence = float(max(probabilities))

    return predicted_sign, confidence
