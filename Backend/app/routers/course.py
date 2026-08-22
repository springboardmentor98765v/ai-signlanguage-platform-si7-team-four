from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import uuid as _uuid

from app.schemas.course import ModuleResponse, ModuleCreate, LessonResponse
from app.utils.security import verify_token_and_role
from app.db.database import SessionLocal, get_db
from app.models import models

# Router initialized
router = APIRouter(prefix="/api/courses", tags=["Course Service"])

ALPHABET_MODULE_NAME = "American Sign Language: Alphabets"
ALPHABET_MODULE_DESCRIPTION = (
    "Learn and practice hand gestures for the foundational letters A through Z."
)


def _lesson_to_response(lesson: models.Lesson) -> LessonResponse:
    return LessonResponse(
        lesson_id=lesson.id,
        module_id=lesson.module_id or "",
        title=lesson.title,
        content_description=lesson.description or "",
        expected_gesture=lesson.expected_gesture or "",
    )


def _module_to_response(mod: models.Module, lessons: List[models.Lesson]) -> ModuleResponse:
    return ModuleResponse(
        module_id=mod.id,
        course_id=mod.course_id,
        title=mod.module_name,
        description=mod.description or "",
        lessons=[_lesson_to_response(lesson) for lesson in lessons],
    )


def _seed_alphabet_course(db: Session) -> None:
    """
    Idempotently seed the static Alphabet Course (module + 26 lessons) into the
    real database so course data survives restarts. Primary keys are generated
    UUIDs (native PostgreSQL UUID columns) and idempotency is keyed by the
    module name / lesson slug, matching Database_Devops/seed_lessons.py.
    """
    existing = db.query(models.Module).filter(
        models.Module.module_name == ALPHABET_MODULE_NAME
    ).first()
    if existing is not None:
        return

    letters = [chr(c) for c in range(ord("A"), ord("Z") + 1)]

    if db.query(models.Course).filter(models.Course.title == ALPHABET_MODULE_NAME).first() is None:
        db.add(models.Course(
            title=ALPHABET_MODULE_NAME,
            description=ALPHABET_MODULE_DESCRIPTION,
            level="Beginner",
        ))
        db.flush()

    course = db.query(models.Course).filter(
        models.Course.title == ALPHABET_MODULE_NAME
    ).one()

    mod = models.Module(
        course_id=course.id,
        module_name=ALPHABET_MODULE_NAME,
        description=ALPHABET_MODULE_DESCRIPTION,
    )
    db.add(mod)
    db.flush()

    for letter in letters:
        db.add(models.Lesson(
            slug=f"alphabet-{letter.lower()}",
            module_id=mod.id,
            title=f"The Letter {letter}",
            description=f"Imitate the visual posture prompt to master signing the alphabet letter '{letter}'.",
            expected_gesture=letter,
            category="alphabet",
            difficulty="easy",
        ))

    db.commit()


WORDS_MODULE_NAME = "American Sign Language: Common Words"
WORDS_MODULE_DESCRIPTION = (
    "Common ASL word signs, each a distinct hand gesture learners practice "
    "alongside the alphabet."
)
COMMON_WORD_SIGNS = [
    ("hello", "Hello", "Wave with an open palm or use the standard HELLO greeting sign."),
    ("thank", "Thank You", "Touch the fingertips of the flat hand to the chin and move it outward."),
    ("help", "Help", "Place the flat hand on the other fist and lift upward."),
    ("love", "Love", "Cross the arms over the chest with fists closed."),
    ("sorry", "Sorry", "Make a fist and rub it in a circular motion over the chest."),
    ("again", "Again", "Bend the dominant hand at the wrist palm-down, moving it in an arc."),
]


def _seed_words_course(db: Session) -> None:
    """Idempotently seed the Common Words course (module + word sign lessons)."""
    existing = db.query(models.Module).filter(
        models.Module.module_name == WORDS_MODULE_NAME
    ).first()
    if existing is not None:
        return

    if db.query(models.Course).filter(models.Course.title == WORDS_MODULE_NAME).first() is None:
        db.add(models.Course(
            title=WORDS_MODULE_NAME,
            description=WORDS_MODULE_DESCRIPTION,
            level="Beginner",
        ))
        db.flush()

    course = db.query(models.Course).filter(
        models.Course.title == WORDS_MODULE_NAME
    ).one()

    mod = models.Module(
        course_id=course.id,
        module_name=WORDS_MODULE_NAME,
        description=WORDS_MODULE_DESCRIPTION,
    )
    db.add(mod)
    db.flush()

    for gesture, title, description in COMMON_WORD_SIGNS:
        db.add(models.Lesson(
            slug=f"word-{gesture}",
            module_id=mod.id,
            title=title,
            description=description,
            expected_gesture=gesture,
            category="words",
            difficulty="medium",
        ))

    db.commit()


# Seed the courses into the real database on startup (idempotent).
_seed_db = SessionLocal()
_seed_alphabet_course(_seed_db)
_seed_words_course(_seed_db)
_seed_db.close()


# --- CRUD READ ENDPOINTS ---

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List Courses",
    description="Returns the course catalog, each course with its total lesson count (DB-backed).",
)
def list_courses(db: Session = Depends(get_db)):
    courses = db.query(models.Course).order_by(models.Course.id.asc()).all()
    items = []
    for c in courses:
        lesson_count = (
            db.query(models.Lesson)
            .join(models.Module, models.Module.id == models.Lesson.module_id)
            .filter(models.Module.course_id == c.id)
            .count()
        )
        items.append({
            "course_id": c.id,
            "title": c.title,
            "description": c.description or "",
            "level": c.level or "Beginner",
            "category": "Alphabet",
            "total_lessons": lesson_count,
        })
    return {"courses": items}


@router.get(
    "/modules",
    response_model=List[ModuleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get All Course Modules",
    description="Returns every curriculum module, each with its nested lessons (DB-backed).",
)
def get_all_modules(db: Session = Depends(get_db)):
    result = []
    modules = db.query(models.Module).order_by(
        models.Module.created_at.asc(), models.Module.id.asc()
    ).all()
    for mod in modules:
        module_lessons = (
            db.query(models.Lesson)
            .filter(models.Lesson.module_id == mod.id)
            .order_by(models.Lesson.id.asc())
            .all()
        )
        result.append(_module_to_response(mod, module_lessons))
    return result


@router.get(
    "/modules/{module_id}/lessons",
    response_model=List[LessonResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Lessons for a Module",
    description="Returns the lessons belonging to a specific module. 404 if the module does not exist.",
)
def get_lessons_by_module(module_id: str, db: Session = Depends(get_db)):
    mod = db.query(models.Module).filter(models.Module.id == module_id).first()
    if mod is None:
        raise HTTPException(status_code=404, detail="Requested course module sequence not found.")

    module_lessons = (
        db.query(models.Lesson)
        .filter(models.Lesson.module_id == module_id)
        .order_by(models.Lesson.id.asc())
        .all()
    )
    return [_lesson_to_response(lesson) for lesson in module_lessons]


@router.get(
    "/{course_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Course Details",
    description="Returns a single course with its nested modules and lessons.",
)
def get_course_details(course_id: str, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    module_list = []
    mods = (
        db.query(models.Module)
        .filter(models.Module.course_id == course.id)
        .order_by(models.Module.id.asc())
        .all()
    )
    for mod in mods:
        lessons = (
            db.query(models.Lesson)
            .filter(models.Lesson.module_id == mod.id)
            .order_by(models.Lesson.id.asc())
            .all()
        )
        module_list.append({
            "module_id": mod.id,
            "module_name": mod.module_name,
            "lessons": [
                {
                    "lesson_id": l.id,
                    "title": l.title,
                    "description": l.description or "",
                    "expected_gesture": l.expected_gesture,
                    "difficulty": (l.difficulty or "Easy").capitalize(),
                }
                for l in lessons
            ],
        })

    return {
        "course_id": course.id,
        "title": course.title,
        "description": course.description or "",
        "level": course.level or "Beginner",
        "modules": module_list,
    }


# --- CRUD CREATE ENDPOINTS (PROTECTED BY RBAC) ---

@router.post(
    "/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Custom Course Module",
    description="RBAC: Instructor or Admin only. Persists a new curriculum module to the database.",
)
def create_custom_module(
    module_input: ModuleCreate,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"])),
):
    """
    Create Endpoint: Allows Instructors or Admins to expand curriculum.

    Persists to the `courses` + `modules` tables (real DB, survives restarts).
    A course row is upserted for the provided course_id so the module has a valid
    FK target on PostgreSQL as well as SQLite.
    """
    try:
        course_pk = str(_uuid.UUID(module_input.course_id))
    except (ValueError, AttributeError):
        course_pk = str(_uuid.uuid4())

    if db.query(models.Course).filter(models.Course.id == course_pk).first() is None:
        db.add(models.Course(
            id=course_pk,
            title=module_input.title,
            description=module_input.description,
            level="Beginner",
        ))
        db.flush()

    new_module = models.Module(
        id=course_pk,
        course_id=course_pk,
        module_name=module_input.title,
        description=module_input.description,
    )
    db.add(new_module)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A module already exists with this course ID.",
        )

    return ModuleResponse(
        module_id=new_module.id,
        course_id=new_module.course_id,
        title=new_module.module_name,
        description=new_module.description or "",
        lessons=[],
    )
