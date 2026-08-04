from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.course import ModuleResponse, ModuleCreate, LessonResponse, LessonCreate
from app.utils.security import verify_token_and_role
from typing import List

# Router initialized
router = APIRouter(prefix="/api/courses", tags=["Course Service"])

# In-memory curriculum datasets
MOCK_MODULE_DB = {}
MOCK_LESSON_DB = {}

def seed_alphabet_course():
    """
    Day 5 Core Requirement: Seeds the platform with the full static Alphabet Course.
    """
    mod_id = "mod_alphabet_101"
    MOCK_MODULE_DB[mod_id] = {
        "module_id": mod_id,
        "title": "American Sign Language: Alphabets",
        "description": "Learn and practice hand gestures for the foundational letters A through Z."
    }
    
    for char_code in range(ord('A'), ord('Z') + 1):
        letter = chr(char_code)
        les_id = f"les_alphabet_{letter.lower()}"
        
        MOCK_LESSON_DB[les_id] = {
            "lesson_id": les_id,
            "module_id": mod_id,
            "title": f"The Letter {letter}",
            "content_description": f"Imitate the visual posture prompt to master signing the alphabet letter '{letter}'.",
            "expected_gesture": letter
        }

seed_alphabet_course()

# --- CRUD READ ENDPOINTS ---

@router.get("/modules", response_model=List[ModuleResponse], status_code=status.HTTP_200_OK, tags=["Course Service"])
def get_all_modules():
    result = []
    for mod_id, mod_data in MOCK_MODULE_DB.items():
        module_lessons = [
            LessonResponse(**les) for les in MOCK_LESSON_DB.values() 
            if les["module_id"] == mod_id
        ]
        # --- Inside get_all_modules ---
        # Merge together to build standard validation layout
        compiled_module = ModuleResponse(
            module_id=mod_data["module_id"],
            title=mod_data["title"],
            description=mod_data["description"],
            course_id=mod_data.get("course_id", "default_course_id"), # ADD THIS LINE
            lessons=module_lessons
        )
        result.append(compiled_module)
    return result

@router.get("/modules/{module_id}/lessons", response_model=List[LessonResponse], status_code=status.HTTP_200_OK, tags=["Course Service"])
def get_lessons_by_module(module_id: str):
    if module_id not in MOCK_MODULE_DB:
        raise HTTPException(status_code=404, detail="Requested course module sequence not found.")
        
    module_lessons = [
        LessonResponse(**les) for les in MOCK_LESSON_DB.values() 
        if les["module_id"] == module_id
    ]
    return module_lessons

# --- CRUD CREATE ENDPOINTS (PROTECTED BY RBAC) ---

@router.post("/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED, tags=["Course Service"])
def create_custom_module(
    module_input: ModuleCreate, 
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"]))
):
    """
    Create Endpoint: Allows Instructors or Admins to expand curriculum.
    """
    # Generating a custom ID
    new_id = f"mod_custom_{len(MOCK_MODULE_DB) + 101}"
    
    # Storing data using the keys from your schema: module_input.title and module_input.description
    MOCK_MODULE_DB[new_id] = {
        "course_id": new_id,
        "title": module_input.title,
        "description": module_input.description
    }
    
    # Returning the response
    return ModuleResponse(
        course_id=new_id, 
        title=module_input.title, 
        description=module_input.description, 
        lessons=[]
    )