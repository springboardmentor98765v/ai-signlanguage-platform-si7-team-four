import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "sign_model.joblib")

_saved = joblib.load(MODEL_PATH)
_pipeline = _saved["pipeline"]
_label_encoder = _saved["label_encoder"]


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
