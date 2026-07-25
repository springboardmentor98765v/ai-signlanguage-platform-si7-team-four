from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, List
from pydantic import BaseModel
from app.utils.security import verify_token_and_role

router = APIRouter(prefix="/lessons", tags=["Lessons Service"])

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
    module_id: str
    title: str
    content_description: Optional[str] = None
    expected_gesture: str
    category: Optional[str] = "Alphabet"
    difficulty: Optional[str] = "Easy"

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
            "module_id": mod_id,
            "title": word["title"],
            "content_description": f"Learn how to sign {word['title']}.",
            "expected_gesture": word["gesture"],
            "category": word["cat"],
            "difficulty": word["diff"]
        }

# Initialize mock data on startup
seed_alphabet_lessons()

# --- SRS ENDPOINT: Get All Lessons with Search & Pagination ---

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
    
    # 1. Search-by-name filter (case-insensitive substring match)
    if search:
        search_lower = search.lower()
        lessons_list = [
            les for les in lessons_list 
            if search_lower in les["title"].lower()
        ]
        
    # 2. Total count after search filtering
    total_count = len(lessons_list)
    
    # 3. Pagination slicing (e.g., 10 items per page)
    paginated_lessons = lessons_list[skip : skip + limit]
    
    return {
        "skip": skip,
        "limit": limit,
        "total": total_count,
        "data": [LessonResponse(**les) for les in paginated_lessons]
    }

# --- SRS ENDPOINT: Get Single Lesson by ID ---

@router.get("/{lesson_id}", response_model=LessonResponse, status_code=status.HTTP_200_OK)
def get_lesson_by_id(lesson_id: str):
    """
    SRS Requirement: Fetch an individual lesson details by ID.
    """
    if lesson_id not in MOCK_LESSON_DB:
        raise HTTPException(status_code=404, detail="The requested lesson could not be found.")
    
    return LessonResponse(**MOCK_LESSON_DB[lesson_id])

# --- DAY 6: CREATE LESSON (Instructor/Admin Only) ---

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

# --- DAY 6: EDIT/UPDATE LESSON (Instructor/Admin Only) ---

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

# --- DAY 6: DELETE LESSON (Instructor/Admin Only) ---

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