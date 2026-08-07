from fastapi import APIRouter, HTTPException, status, Query, Depends, UploadFile, File
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import csv
import io
from app.utils.security import verify_token_and_role
from app.utils.validation import ALLOWED_CATEGORIES, ALLOWED_DIFFICULTY, reject_malicious

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

# --- In-Memory Mock Datasets ---
MOCK_LESSON_DB = {}

def seed_alphabet_lessons():
    """
    Seeds the mock dataset with alphabet and sample lessons for testing.
    """
    mod_id = "mod_alphabet_101"
    
    # Seed A through Z alphabet lessons
    for char_code in range(ord('A'), ord('Z') + 1):
        letter = chr(char_code)
        les_id = f"les_alphabet_{letter.lower()}"
        MOCK_LESSON_DB[les_id] = {
            "lesson_id": les_id,
            "module_id": mod_id,
            "title": f"The Letter {letter}",
            "content_description": f"Master signing the alphabet letter '{letter}'.",
            "expected_gesture": letter,
            "category": "Alphabet",
            "difficulty": "Easy"
        }

    # Seed extra common word lessons
    extra_words = [
        {"id": "les_word_hello", "title": "Word Hello", "gesture": "HELLO", "cat": "Words", "diff": "Easy"},
        {"id": "les_word_thankyou", "title": "Word Thank You", "gesture": "THANK_YOU", "cat": "Words", "diff": "Medium"},
        {"id": "les_word_yes", "title": "Word Yes", "gesture": "YES", "cat": "Words", "diff": "Easy"},
        {"id": "les_word_no", "title": "Word No", "gesture": "NO", "cat": "Words", "diff": "Easy"},
        {"id": "les_word_please", "title": "Word Please", "gesture": "PLEASE", "cat": "Words", "diff": "Medium"}
    ]
    
    for word in extra_words:
        MOCK_LESSON_DB[word["id"]] = {
            "lesson_id": word["id"],
            "module_id": word["id"],
            "title": word["title"],
            "content_description": f"Learn how to sign {word['title']}.",
            "expected_gesture": word["gesture"],
            "category": word["cat"],
            "difficulty": word["diff"]
        }

# Initialize mock data on startup
seed_alphabet_lessons()

# --- GET ALL LESSONS ---

@router.get("", status_code=status.HTTP_200_OK)
def get_all_lessons(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (default 10)"),
    search: Optional[str] = Query(None, description="Search term for lesson title")
):
    """
    SRS Requirement: Fetch lessons with built-in Search-by-name and Pagination (10 per page).
    """
    lessons_list = list(MOCK_LESSON_DB.values())
    
    if search:
        search_lower = search.lower()
        lessons_list = [
            les for les in lessons_list 
            if search_lower in les["title"].lower()
        ]
        
    total_count = len(lessons_list)
    paginated_lessons = lessons_list[skip : skip + limit]
    
    return {
        "skip": skip,
        "limit": limit,
        "total": total_count,
        "data": [LessonResponse(**les) for les in paginated_lessons]
    }

# --- STATIC SPECIFIC ROUTES (MUST BE BEFORE /{lesson_id} ROUTE) ---

@router.get("/advanced", status_code=status.HTTP_200_OK)
def get_advanced_lessons():
    """
    Milestone 2 & 3 Requirement: Fetches extended multi-tier advanced lessons catalog.
    """
    advanced_lessons = [
        les for les in MOCK_LESSON_DB.values()
        if les.get("difficulty") in ["Medium", "Hard"] or les.get("category") == "Words"
    ]
    return {
        "count": len(advanced_lessons),
        "advanced_lessons": advanced_lessons
    }

@router.post("/bulk-upload-csv", status_code=status.HTTP_201_CREATED)
def bulk_upload_lessons_csv(payload: CSVBulkUploadPayload):
    """
    Milestone 3 Requirement: Bulk upload lessons via CSV string payload.
    CSV header format: module_id,title,content_description,expected_gesture,category,difficulty
    """
    if not payload or not payload.csv_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="CSV content string payload must be provided."
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
            
        new_id = f"les_csv_{len(MOCK_LESSON_DB) + 1}_{row_num}"
        new_lesson = {
            "lesson_id": new_id,
            "module_id": module_id or "mod_alphabet_101",
            "title": title,
            "content_description": row.get("content_description", f"Bulk uploaded lesson {title}"),
            "expected_gesture": expected_gesture,
            "category": row.get("category", "General"),
            "difficulty": row.get("difficulty", "Medium")
        }
        MOCK_LESSON_DB[new_id] = new_lesson
        created_lessons.append(new_lesson)
        
    return {
        "message": f"Successfully parsed and created {len(created_lessons)} lessons.",
        "created_count": len(created_lessons),
        "created_lessons": created_lessons,
        "errors": errors
    }

# --- DYNAMIC PARAMETER ROUTES ---

@router.get("/{lesson_id}", response_model=LessonResponse, status_code=status.HTTP_200_OK)
def get_lesson_by_id(lesson_id: str):
    """
    SRS Requirement: Fetch an individual lesson details by ID.
    """
    if lesson_id not in MOCK_LESSON_DB:
        raise HTTPException(status_code=404, detail="The requested lesson could not be found.")
    
    return LessonResponse(**MOCK_LESSON_DB[lesson_id])

@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    lesson_input: LessonCreate,
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"]))
):
    """
    Day 6 Checkpoint: Create a custom lesson (Restricted to Instructors and Admins).
    """
    new_id = f"les_custom_{len(MOCK_LESSON_DB) + 1}"
    
    new_lesson = {
        "lesson_id": new_id,
        "module_id": lesson_input.module_id,
        "title": lesson_input.title,
        "content_description": lesson_input.content_description,
        "expected_gesture": lesson_input.expected_gesture,
        "category": lesson_input.category,
        "difficulty": lesson_input.difficulty
    }
    
    MOCK_LESSON_DB[new_id] = new_lesson
    return LessonResponse(**new_lesson)

@router.put("/{lesson_id}", response_model=LessonResponse, status_code=status.HTTP_200_OK)
def update_lesson(
    lesson_id: str,
    lesson_update: LessonCreate,
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"]))
):
    """
    Day 6 Checkpoint: Edit an existing lesson by ID (Restricted to Instructors and Admins).
    """
    if lesson_id not in MOCK_LESSON_DB:
        raise HTTPException(status_code=404, detail="The specified lesson to update could not be found.")
        
    updated_data = {
        "lesson_id": lesson_id,
        "module_id": lesson_update.module_id,
        "title": lesson_update.title,
        "content_description": lesson_update.content_description,
        "expected_gesture": lesson_update.expected_gesture,
        "category": lesson_update.category,
        "difficulty": lesson_update.difficulty
    }
    
    MOCK_LESSON_DB[lesson_id] = updated_data
    return LessonResponse(**updated_data)

@router.delete("/{lesson_id}", status_code=status.HTTP_200_OK)
def delete_lesson(
    lesson_id: str,
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"]))
):
    """
    Day 6 Checkpoint: Delete a lesson by ID (Restricted to Instructors and Admins).
    """
    if lesson_id not in MOCK_LESSON_DB:
        raise HTTPException(status_code=404, detail="The specified lesson to delete could not be found.")
        
    del MOCK_LESSON_DB[lesson_id]
    return {"message": f"Lesson {lesson_id} deleted successfully."}