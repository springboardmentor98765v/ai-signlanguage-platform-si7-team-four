#IMPORT libraries 
import os
import sys
from typing import Optional,List

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CV_DIR = os.path.join(BASE_DIR, "..", "cv")
sys.path.append(CV_DIR)

from hand_detector import HandDetector          # noqa: E402
from feature_extractor import FeatureExtractor  # noqa: E402
from predict import predict_with_feedback     # noqa: E402
from predict_dynamic import predict_dynamic     # noqa: E402
from dynamic_data_collector import landmarks_to_array  # noqa: E402


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

class DynamicPredictionResponse(BaseModel):
    predicted_sign: Optional[str]
    matched: bool
    confidence: Optional[float]
    distance: Optional[float]
    hand_detected_frames: int
    total_frames: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(file: UploadFile = File(...),target_sign: Optional[str] = None):
    try:
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#Dynamic model prediction POST 
MIN_DETECTION_RATE = 0.5

@app.post("/predict_dynamic", response_model=DynamicPredictionResponse)
async def predict_dynamic_endpoint(files: List[UploadFile] = File(...)):
    frames_landmarks = []

    for f in files:
        contents = await f.read()
        np_arr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            continue

        results = detector.detect_hands(frame)
        if results.hand_landmarks:
            frames_landmarks.append(landmarks_to_array(results.hand_landmarks[0]))

    total_frames = len(files)
    detected_frames = len(frames_landmarks)
    detection_rate = detected_frames / total_frames if total_frames else 0.0

    if detected_frames < 5 or detection_rate < MIN_DETECTION_RATE:
        # Not enough usable frames to trust a prediction — distinct from
        # "matched=False", which means we tried and didn't find a match.
        return DynamicPredictionResponse(
            predicted_sign=None, matched=False, confidence=None, distance=None,
            hand_detected_frames=detected_frames, total_frames=total_frames
        )

    sequence = np.stack(frames_landmarks)
    predicted, distance, matched, confidence = predict_dynamic(sequence)

    return DynamicPredictionResponse(
        predicted_sign=predicted,
        matched=matched,
        confidence=round(confidence, 4) if confidence is not None else None,
        distance=round(distance, 4) if distance is not None else None,
        hand_detected_frames=detected_frames,
        total_frames=total_frames,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)