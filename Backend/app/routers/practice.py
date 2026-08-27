from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import practice_service
from app.models import models
from app.services import notification_service as notifications
from app.schemas.practice import (
    PracticeSessionResponse,
    PracticeEndResponse,
    PracticeSubmitResponse,
    PracticeDynamicSubmitResponse,
    PracticeImageSubmissionRequest,
    PracticeDynamicSubmissionRequest,
)
import uuid
import logging
from datetime import datetime, timedelta as _timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/practice", tags=["Practice Service"])


@router.post(
    "/start",
    response_model=PracticeSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a Practice Session",
    description=(
        "Starts a new practice session for a user/lesson pair via the practice "
        "service and returns the created session record with status 'in_progress'."
    ),
)
def start_practice(
    user_id: str,
    lesson_id: str,
    db: Session = Depends(get_db),
):
    """
    Starts a new practice session via the practice service.
    """
    session = practice_service.start_session(db, user_id, lesson_id)
    return session


@router.post(
    "/end",
    response_model=PracticeEndResponse,
    status_code=status.HTTP_200_OK,
    summary="End a Practice Session",
    description=(
        "Ends an existing practice session, recording end time and duration. "
        "Returns 404 if the session does not exist."
    ),
)
def end_practice(
    session_id: str,
    db: Session = Depends(get_db),
):
    """
    Ends an existing practice session via the practice service.
    """
    session = practice_service.end_session(db, session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.post(
    "/submit",
    response_model=PracticeSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a Practice Frame for AI Feedback",
    description=(
        "Accepts a raw base64-encoded image from the frontend, decodes it, and "
        "forwards it as multipart/form-data to the Python AI service "
        "(`ai-service:8001/predict`). The AI service extracts hand landmarks with "
        "MediaPipe, generates features, and runs the trained model; the resulting "
        "prediction is relayed back to the client. Requires a valid UUID "
        "session_id (or user_id + lesson_id to auto-start one); 400 if the image "
        "data is malformed, 404 if the session does not exist."
    ),
)

def submit_practice_frame(
    payload: PracticeImageSubmissionRequest,
    db: Session = Depends(get_db)
) -> PracticeSubmitResponse:
    """
    Relay a raw hand image to the AI service for prediction.

    Flow enforced here (landmark extraction happens ONLY in the AI service):
        Browser -> raw image (base64) -> /submit -> decode -> multipart ->
        ai-service:8001/predict -> MediaPipe landmarks -> features -> model ->
        prediction -> relayed back.
    """
    session_id = payload.session_id

    if session_id:
        # Validate the provided session belongs to a real practice record.
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="session_id must be a valid UUID format.")
        session = db.query(models.PracticeSession).filter(models.PracticeSession.id == str(session_uuid)).first()
        if not session:
            raise HTTPException(status_code=404, detail="Active practice session context missing")
    else:
        # The frontend may omit session_id; auto-start an in-progress session.
        if not payload.user_id or not payload.lesson_id:
            raise HTTPException(
                status_code=400,
                detail="Either session_id or both user_id and lesson_id are required.",
            )
        session_id = practice_service.start_session(db, payload.user_id, payload.lesson_id)["session_id"]

    # Decode base64 image data (expects a data URL prefix)
    import base64, re
    match = re.match(r"data:image/.+;base64,(.*)", payload.image_data)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid image_data format; must be base64 data URL.")
    try:
        image_bytes = base64.b64decode(match.group(1))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to decode base64 image.")

    # Forward the RAW image to the AI service (landmark extraction is done there).
    import httpx, os
    ai_url = os.getenv("AI_SERVICE_URL", "http://ai-service:8001").rstrip("/")
    files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
    data = {}
    if payload.target_letter:
        data["target_sign"] = payload.target_letter
    try:
        ai_resp = httpx.post(f"{ai_url}/predict", files=files, data=data, timeout=10.0)
    except Exception as exc:
        logger.warning("AI service request failed: %s", exc)
        raise HTTPException(status_code=502, detail="AI service is unreachable. Please try again shortly.")
    if ai_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="AI service returned an unexpected error.")

    try:
        ai = ai_resp.json()
        if not isinstance(ai, dict):
            raise ValueError("AI response is not a JSON object")
        predicted_sign = ai.get("predicted_sign")
        confidence = float(ai.get("confidence") or 0.0)
        hand_detected = bool(ai.get("hand_detected", False))
        correct = ai.get("correct")
        possible_issue = ai.get("possible_issue")
    except (ValueError, TypeError) as exc:
        logger.warning("AI service returned malformed prediction: %s", exc)
        raise HTTPException(status_code=502, detail="AI service returned a malformed prediction response.")

    # ------------------------------------------------------------------
    # Persist this practice attempt so dashboards/leaderboards are live.
    # (Intern 4 Section C: every successful prediction is recorded.)
    # ------------------------------------------------------------------
    overall_accuracy = None
    updated_streak = None
    try:
        session = db.query(models.PracticeSession).filter(models.PracticeSession.id == session_id).first()

        if hand_detected and payload.target_letter and predicted_sign:
            eff_conf = max(0.0, min(float(confidence), 1.0))
            is_correct = str(predicted_sign).strip().lower() == str(payload.target_letter).strip().lower()
            if is_correct:
                overall_accuracy = round(eff_conf * 100.0, 1)
            else:
                overall_accuracy = round(max(0.0, 100.0 - eff_conf * 100.0), 1)

            db.add(models.Assessment(
                session_id=session_id,
                predicted_sign=str(predicted_sign)[:5],
                expected_sign=str(payload.target_letter)[:5],
                confidence=eff_conf,
                hand_shape_score=overall_accuracy,
                finger_position_score=overall_accuracy,
                timing_score=overall_accuracy,
                overall_accuracy=overall_accuracy,
                is_correct=bool(is_correct),
                suggestions=possible_issue,
            ))

            if session is not None and session.user_id:
                today = datetime.utcnow().date()
                streak_row = db.query(models.Streak).filter(models.Streak.user_id == session.user_id).first()
                if streak_row is None:
                    streak_row = models.Streak(
                        user_id=session.user_id,
                        current_streak_count=1,
                        longest_streak_count=1,
                        last_practice_date=datetime.utcnow(),
                    )
                    db.add(streak_row)
                else:
                    last_date = streak_row.last_practice_date
                    if last_date is None or last_date.date() != today:
                        gap_days = (today - last_date.date()).days if last_date else 1
                        streak_row.current_streak_count = 1 if gap_days > 1 else (streak_row.current_streak_count or 0) + 1
                        streak_row.longest_streak_count = max(
                            streak_row.longest_streak_count or 0,
                            streak_row.current_streak_count or 0,
                        )
                        streak_row.last_practice_date = datetime.utcnow()
                db.flush()
                updated_streak = streak_row.current_streak_count

                # Refresh the learner's aggregate analytics row.
                _refresh_analytics_summary(db, session.user_id)

                # Auto-mark lesson as completed when score >= 80%.
                if overall_accuracy is not None and overall_accuracy >= 80.0 and session.lesson_id:
                    from app.models.models import LessonCompletion
                    existing_completion = (
                        db.query(LessonCompletion)
                        .filter(
                            LessonCompletion.user_id == session.user_id,
                            LessonCompletion.lesson_id == str(session.lesson_id),
                        )
                        .first()
                    )
                    if existing_completion:
                        if overall_accuracy > existing_completion.best_score:
                            existing_completion.best_score = overall_accuracy
                    else:
                        db.add(LessonCompletion(
                            user_id=session.user_id,
                            lesson_id=str(session.lesson_id),
                            best_score=overall_accuracy,
                        ))

            notifications.create_notification(
                db,
                user_id=session.user_id if session is not None else (payload.user_id or "unknown"),
                title="Practice attempt recorded",
                message=(
                    f"Signed '{payload.target_letter}' — score {overall_accuracy:.1f}%."
                    if overall_accuracy is not None
                    else "Practice attempt recorded."
                ),
                event_type="info",
            )
            db.commit()

        # Best-effort recommendation refresh after the attempt is safely
        # persisted, so the learner dashboard reflects it immediately.
        if session is not None and session.user_id:
            try:
                from app.services.recommendation_service import sync_user_recommendations

                sync_user_recommendations(db, session.user_id)
            except Exception as exc:
                logger.warning("Could not refresh recommendations: %s", exc)
                db.rollback()

        if session is not None:
            practice_service.increment_attempt(db, session_id)
    except Exception as exc:
        logger.warning("Could not persist practice attempt: %s", exc)
        db.rollback()

    return PracticeSubmitResponse(
        status="success",
        session_id=session_id,
        predicted_sign=predicted_sign,
        confidence=confidence,
        hand_detected=hand_detected,
        correct=correct,
        possible_issue=possible_issue,
        overall_accuracy=overall_accuracy,
        updated_streak=updated_streak,
    )


# -----------------------------------------------------------------------
# Dynamic (multi-frame) submission — for J, Z, and word signs
# -----------------------------------------------------------------------

@router.post(
    "/submit_dynamic",
    response_model=PracticeDynamicSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a Burst of Frames for Dynamic AI Feedback",
    description=(
        "Accepts a list of base64-encoded frames captured over a recording "
        "burst, decodes each one, and forwards the entire list as multipart "
        "files to the AI service at ``/predict_dynamic``. Used for dynamic "
        "signs (J, Z, hello, no, please, thank_you, yes) where a single "
        "image is insufficient."
    ),
)
def submit_practice_frame_dynamic(
    payload: PracticeDynamicSubmissionRequest,
    db: Session = Depends(get_db),
) -> PracticeDynamicSubmitResponse:
    """Relay a burst of hand images to the AI dynamic prediction service.

    Flow:
        Browser -> list of base64 images -> /submit_dynamic -> decode each ->
        multipart files -> ai-service:8001/predict_dynamic -> DTW matching ->
        prediction -> relayed back + persisted.
    """
    import base64, re, httpx, os

    # --- Resolve / validate session -------------------------------------------
    session_id = payload.session_id
    if session_id:
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="session_id must be a valid UUID format.")
        session = db.query(models.PracticeSession).filter(
            models.PracticeSession.id == str(session_uuid)
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Active practice session context missing")
    else:
        if not payload.user_id or not payload.lesson_id:
            raise HTTPException(
                status_code=400,
                detail="Either session_id or both user_id and lesson_id are required.",
            )
        session_id = practice_service.start_session(
            db, payload.user_id, payload.lesson_id
        )["session_id"]

    # --- Decode every frame --------------------------------------------------
    decoded_frames: list[tuple[str, bytes, str]] = []
    for idx, frame_data in enumerate(payload.frames):
        m = re.match(r"data:image/.+;base64,(.*)", frame_data)
        if not m:
            raise HTTPException(
                status_code=400,
                detail=f"Frame {idx}: invalid image_data format; must be base64 data URL.",
            )
        try:
            frame_bytes = base64.b64decode(m.group(1))
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Frame {idx}: failed to decode base64 image.",
            )
        decoded_frames.append((f"frame_{idx}.jpg", frame_bytes, "image/jpeg"))

    # --- Forward to AI service /predict_dynamic ------------------------------
    ai_url = os.getenv("AI_SERVICE_URL", "http://ai-service:8001").rstrip("/")
    files = [("files", (name, data, ct)) for name, data, ct in decoded_frames]
    data: dict = {}
    if payload.target_letter:
        data["target_sign"] = payload.target_letter

    try:
        ai_resp = httpx.post(f"{ai_url}/predict_dynamic", files=files, data=data, timeout=30.0)
    except Exception as exc:
        logger.warning("AI service (predict_dynamic) request failed: %s", exc)
        raise HTTPException(status_code=502, detail="AI service is unreachable. Please try again shortly.")
    if ai_resp.status_code != 200:
        logger.warning("AI service returned %d: %s", ai_resp.status_code, ai_resp.text[:300])
        raise HTTPException(status_code=502, detail="AI service returned an unexpected error.")

    try:
        ai = ai_resp.json()
        if not isinstance(ai, dict):
            raise ValueError("AI response is not a JSON object")
        matched = bool(ai.get("matched", False))
        predicted_sign = ai.get("predicted_sign")
        confidence = float(ai.get("confidence") or 0.0)
        distance = ai.get("distance")
        hand_detected_frames = int(ai.get("hand_detected_frames") or 0)
        total_frames = int(ai.get("total_frames") or len(decoded_frames))
        possible_issue = ai.get("possible_issue")
    except (ValueError, TypeError) as exc:
        logger.warning("AI service (predict_dynamic) returned malformed prediction: %s", exc)
        raise HTTPException(status_code=502, detail="AI service returned a malformed prediction response.")

    # --- Determine correctness using dynamic scoring -----------------------------------------------
    correct = None
    overall_accuracy = None

    if matched and predicted_sign and payload.target_letter:
        from app.services.assessment_service import assess_dynamic

        dynamic_result = assess_dynamic(
            predicted_sign=str(predicted_sign),
            expected_sign=str(payload.target_letter),
            confidence=confidence,
            distance=distance,
        )

        correct = dynamic_result["is_correct"]
        overall_accuracy = dynamic_result["overall_accuracy"]

    # --- Persist to Assessment (mirrors the static path) ---------------------
    updated_streak = None
    try:
        session = db.query(models.PracticeSession).filter(
            models.PracticeSession.id == session_id
        ).first()

        if matched and payload.target_letter and predicted_sign:
            db.add(models.Assessment(
                session_id=session_id,
                predicted_sign=str(predicted_sign)[:20],
                expected_sign=str(payload.target_letter)[:20],
                confidence=confidence,
                hand_shape_score=None,
                finger_position_score=None,
                timing_score=None,
                overall_accuracy=overall_accuracy,
                is_correct=correct,
                suggestions=possible_issue,
            ))

            if session is not None and session.user_id:
                today = datetime.utcnow().date()
                streak_row = db.query(models.Streak).filter(
                    models.Streak.user_id == session.user_id
                ).first()
                if streak_row is None:
                    streak_row = models.Streak(
                        user_id=session.user_id,
                        current_streak_count=1,
                        longest_streak_count=1,
                        last_practice_date=datetime.utcnow(),
                    )
                    db.add(streak_row)
                else:
                    last_date = streak_row.last_practice_date
                    if last_date is None or last_date.date() != today:
                        gap_days = (today - last_date.date()).days if last_date else 1
                        streak_row.current_streak_count = (
                            1 if gap_days > 1 else (streak_row.current_streak_count or 0) + 1
                        )
                        streak_row.longest_streak_count = max(
                            streak_row.longest_streak_count or 0,
                            streak_row.current_streak_count or 0,
                        )
                        streak_row.last_practice_date = datetime.utcnow()
                db.flush()
                updated_streak = streak_row.current_streak_count

                _refresh_analytics_summary(db, session.user_id)

                # Auto-mark lesson as completed when score >= 80%.
                if overall_accuracy is not None and overall_accuracy >= 80.0 and session.lesson_id:
                    from app.models.models import LessonCompletion
                    existing_completion = (
                        db.query(LessonCompletion)
                        .filter(
                            LessonCompletion.user_id == session.user_id,
                            LessonCompletion.lesson_id == str(session.lesson_id),
                        )
                        .first()
                    )
                    if existing_completion:
                        if overall_accuracy > existing_completion.best_score:
                            existing_completion.best_score = overall_accuracy
                    else:
                        db.add(LessonCompletion(
                            user_id=session.user_id,
                            lesson_id=str(session.lesson_id),
                            best_score=overall_accuracy,
                        ))

            notifications.create_notification(
                db,
                user_id=session.user_id if session is not None else (payload.user_id or "unknown"),
                title="Dynamic practice attempt recorded",
                message=(
                    f"Signed '{payload.target_letter}' — score {overall_accuracy:.1f}%."
                    if overall_accuracy is not None
                    else "Dynamic practice attempt recorded."
                ),
                event_type="info",
            )
            db.commit()

        if session is not None and session.user_id:
            try:
                from app.services.recommendation_service import sync_user_recommendations
                sync_user_recommendations(db, session.user_id)
            except Exception as exc:
                logger.warning("Could not refresh recommendations: %s", exc)
                db.rollback()

        if session is not None:
            practice_service.increment_attempt(db, session_id)
    except Exception as exc:
        logger.warning("Could not persist dynamic practice attempt: %s", exc)
        db.rollback()

    return PracticeDynamicSubmitResponse(
        status="success",
        session_id=session_id,
        matched=matched,
        predicted_sign=predicted_sign,
        confidence=confidence,
        distance=distance,
        hand_detected_frames=hand_detected_frames,
        total_frames=total_frames,
        correct=correct,
        possible_issue=possible_issue,
        overall_accuracy=overall_accuracy,
        updated_streak=updated_streak,
    )


def _refresh_analytics_summary(db, user_id: str) -> None:
    """Recompute a learner's AnalyticsSummary row from persisted records."""
    from sqlalchemy import func as _af

    sessions = (
        db.query(models.PracticeSession)
        .filter(models.PracticeSession.user_id == user_id, models.PracticeSession.status == "completed")
        .all()
    )
    completed_up_to = {s.id for s in sessions}
    acc_avg = None
    if completed_up_to:
        acc_avg = db.query(_af.avg(models.Assessment.overall_accuracy)).filter(
            models.Assessment.session_id.in_(completed_up_to)
        ).scalar()

    distinct_lessons = {s.lesson_id for s in sessions}
    practice_hours = round(sum((s.duration_seconds or 0.0) for s in sessions) / 3600.0, 2)

    summary = db.query(models.AnalyticsSummary).filter(models.AnalyticsSummary.user_id == user_id).first()
    if summary is None:
        summary = models.AnalyticsSummary(user_id=user_id)
        db.add(summary)
    summary.overall_accuracy_percentage = round(acc_avg or 0.0, 1)
    summary.lessons_completed = len(distinct_lessons)
    summary.practice_hours = practice_hours
    summary.improvement_rate_percentage = 0.0
