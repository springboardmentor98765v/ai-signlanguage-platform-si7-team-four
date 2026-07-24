#IMPORT libraries 
import os
import sys
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CV_DIR = os.path.join(BASE_DIR, "..", "cv")
sys.path.append(CV_DIR)

from hand_detector import HandDetector          # noqa: E402
from feature_extractor import FeatureExtractor  # noqa: E402
from predict import predict_with_feedback     # noqa: E402


app = FastAPI(title="Sign Language AI Prediction Service")

# TODO: replace "*" with the actual frontend origin before the real demo/deploy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# loaded once at startup, reused across every request —
# creating a new HandDetector per request would be slow and wasteful
detector = HandDetector()
extractor = FeatureExtractor()


class PredictionResponse(BaseModel):
    predicted_sign: Optional[str]
    confidence: float
    hand_detected: bool
    # new labels for giving feedback over issue
    correct: Optional[bool] = None
    possible_issue: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(file: UploadFile = File(...),target_sign: Optional[str] = None):
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        # unreadable file — not the same as "no hand found"
        return PredictionResponse(
            predicted_sign=None, confidence=0.0, hand_detected=False
        )

    results = detector.detect_hands(frame)

    if not results.hand_landmarks:
        return PredictionResponse(
            predicted_sign=None, confidence=0.0, hand_detected=False
        )

    hand = results.hand_landmarks[0]
    sign, confidence, correct, possible_issue = predict_with_feedback(
        hand, extractor, target_label=target_sign
    )

    return PredictionResponse(
        predicted_sign=sign, confidence=confidence, hand_detected=True,
        correct=correct, possible_issue=possible_issue
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)