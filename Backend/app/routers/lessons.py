"""
Real database-backed Lesson CRUD service.

All lesson management reads and writes the `lessons` table (the same catalog
served by /api/courses/modules), so instructor-created lessons are persisted,
survive restarts, and are immediately visible to learners.

RBAC: create/update/delete/bulk-upload require an Instructor or Admin token.
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import csv
import io
import uuid as _uuid

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Lesson, Module
from app.utils.security import verify_token_and_role
from app.utils.validation import (
    ALLOWED_CATEGORIES,
    ALLOWED_DIFFICULTY,
    reject_malicious,
)

router = APIRouter(prefix="/api/lessons", tags=["Lessons Service"])

# --- Pydantic Schemas for Validation ---
class LessonResponse(BaseModel):
    lesson_id: str
    module_id: str
    title: str
    content_description: Optional[str] = None
    expected_gesture: str
    category: Optional[str] = "Alphabet"
    difficulty: Optional[str] = "Easy"


class LessonCreate(BaseModel):
    module_id: str = Field(..., min_length=1, max_length=36)
    title: str = Field(..., min_length=1, max_length=150)
    content_description: Optional[str] = Field(None, max_length=2000)
    expected_gesture: str = Field(..., min_length=1, max_length=5)
    category: Optional[str] = "Alphabet"
    difficulty: Optional[str] = "Easy"

    @field_validator("module_id", "title", "content_description", "expected_gesture")
    @classmethod
    def _reject_malicious_text(cls, value):
        if value is None:
            return value
        return reject_malicious(value)

    @field_validator("category")
    @classmethod
    def _validate_category(cls, value):
        if value and value.lower() not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"category must be one of: {sorted(ALLOWED_CATEGORIES)} (got '{value}')."
            )
        return value

    @field_validator("difficulty")
    @classmethod
    def _validate_difficulty(cls, value):
        if value and value.lower() not in ALLOWED_DIFFICULTY:
            raise ValueError(
                f"difficulty must be one of: {sorted(ALLOWED_DIFFICULTY)} (got '{value}')."
            )
        return value


class CSVBulkUploadPayload(BaseModel):
    csv_content: str = Field(..., max_length=1_000_000)

    @field_validator("csv_content")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)


def _canonical_uuid(value: str | None, fallback: str | None = None) -> str:
    """Coerce arbitrary ids into a valid UUID string (deterministic for lookups)."""
    raw = value or fallback
    if not raw:
        return str(_uuid.uuid4())
    try:
        return str(_uuid.UUID(str(raw)))
    except (ValueError, AttributeError):
        return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, str(raw)))


def _resolve_module_id(db: Session, module_id: str) -> str:
    """Return a real module id, falling back to the alphabet module if the
    requested module does not exist (keeps the FK valid on both SQLite/Postgres)."""
    requested = _canonical_uuid(module_id)
    if db.query(Module).filter(Module.id == requested).first() is not None:
        return requested
    alphabet = (
        db.query(Module)
        .filter(Module.module_name == "American Sign Language: Alphabets")
        .first()
    )
    if alphabet is not None:
        return str(alphabet.id)
    return requested


def _lesson_to_response(lesson: Lesson) -> LessonResponse:
    return LessonResponse(
        lesson_id=str(lesson.id),
        module_id=str(lesson.module_id),
        title=lesson.title,
        content_description=lesson.description or "",
        expected_gesture=lesson.expected_gesture or "",
        category=(lesson.category or "alphabet").capitalize(),
        difficulty=(lesson.difficulty or "easy").capitalize(),
    )


# --- GET ALL LESSONS ---

@router.get("", status_code=status.HTTP_200_OK, summary="List Lessons (paginated)", description="SRS Requirement: Fetch lessons with built-in search-by-name and pagination.")
def get_all_lessons(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Lesson)
    if search:
        query = query.filter(Lesson.title.ilike(f"%{search}%"))
    total_count = query.count()
    lessons = query.order_by(Lesson.id.asc()).offset(skip).limit(limit).all()
    return {
        "skip": skip,
        "limit": limit,
        "total": total_count,
        "data": [_lesson_to_response(lesson) for lesson in lessons],
    }


# --- STATIC SPECIFIC ROUTES (MUST BE BEFORE /{lesson_id} ROUTE) ---

@router.get("/advanced", status_code=status.HTTP_200_OK, summary="List Advanced Lessons")
def get_advanced_lessons(db: Session = Depends(get_db)):
    advanced_lessons = (
        db.query(Lesson)
        .filter((Lesson.category == "words") | (Lesson.difficulty.in_(["medium", "hard"])))
        .limit(100)
        .all()
    )
    return {
        "count": len(advanced_lessons),
        "advanced_lessons": [_lesson_to_response(lesson) for lesson in advanced_lessons],
    }


@router.post("/bulk-upload-csv", status_code=status.HTTP_201_CREATED, summary="Bulk Upload Lessons via CSV String")
def bulk_upload_lessons_csv(
    payload: CSVBulkUploadPayload,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"])),
):
    if not payload or not payload.csv_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV content string payload must be provided.",
        )

    f = io.StringIO(payload.csv_content.strip())
    reader = csv.DictReader(f)

    created_lessons = []
    errors = []
    row_num = 1

    for row in reader:
        row_num += 1
        module_id = row.get("module_id", "").strip()
        title = row.get("title", "").strip()
        expected_gesture = row.get("expected_gesture", "").strip()

        if not title or not expected_gesture:
            errors.append(f"Row {row_num}: missing required title or expected_gesture.")
            continue

        category = row.get("category", "general").strip().lower()
        difficulty = row.get("difficulty", "medium").strip().lower()
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"Row {row_num}: invalid category '{category}'.")
            continue
        if difficulty not in ALLOWED_DIFFICULTY:
            errors.append(f"Row {row_num}: invalid difficulty '{difficulty}'.")
            continue

        lesson = Lesson(
            slug=f"lesson-{_uuid.uuid4().hex[:12]}",
            module_id=_resolve_module_id(db, module_id),
            title=title,
            description=row.get("content_description", f"Bulk uploaded lesson {title}"),
            expected_gesture=expected_gesture,
            category=category,
            difficulty=difficulty,
        )
        db.add(lesson)
        created_lessons.append(_lesson_to_response(lesson))

    db.commit()
    return {
        "message": f"Successfully created {len(created_lessons)} lessons.",
        "created_count": len(created_lessons),
        "created_lessons": [lesson.model_dump() for lesson in created_lessons],
        "errors": errors,
    }


# --- DYNAMIC PARAMETER ROUTES ---

@router.get("/{lesson_id}", response_model=LessonResponse, status_code=status.HTTP_200_OK)
def get_lesson_by_id(lesson_id: str, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == _canonical_uuid(lesson_id)).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="The requested lesson could not be found.")
    return _lesson_to_response(lesson)


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED, summary="Create a Custom Lesson")
def create_lesson(
    lesson_input: LessonCreate,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"])),
):
    lesson = Lesson(
        slug=f"lesson-{_uuid.uuid4().hex[:12]}",
        module_id=_resolve_module_id(db, lesson_input.module_id),
        title=lesson_input.title,
        description=lesson_input.content_description,
        expected_gesture=lesson_input.expected_gesture,
        category=(lesson_input.category or "alphabet").lower(),
        difficulty=(lesson_input.difficulty or "easy").lower(),
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return _lesson_to_response(lesson)


@router.put("/{lesson_id}", response_model=LessonResponse, status_code=status.HTTP_200_OK)
def update_lesson(
    lesson_id: str,
    lesson_update: LessonCreate,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"])),
):
    lesson = db.query(Lesson).filter(Lesson.id == _canonical_uuid(lesson_id)).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="The specified lesson to update could not be found.")

    lesson.module_id = _resolve_module_id(db, lesson_update.module_id)
    lesson.title = lesson_update.title
    lesson.description = lesson_update.content_description
    lesson.expected_gesture = lesson_update.expected_gesture
    lesson.category = (lesson_update.category or "alphabet").lower()
    lesson.difficulty = (lesson_update.difficulty or "easy").lower()
    db.commit()
    db.refresh(lesson)
    return _lesson_to_response(lesson)


@router.delete("/{lesson_id}", status_code=status.HTTP_200_OK)
def delete_lesson(
    lesson_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"])),
):
    lesson = db.query(Lesson).filter(Lesson.id == _canonical_uuid(lesson_id)).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="The specified lesson to delete could not be found.")
    db.delete(lesson)
    db.commit()
    return {"message": f"Lesson {lesson_id} deleted successfully."}