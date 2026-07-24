from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/v1/dictionary", tags=["Sign Dictionary & Vocabulary"])

class DictionarySignResponse(BaseModel):
    id: int
    sign_name: str
    category: str
    difficulty_level: str
    description: str
    video_url: Optional[str] = None

    class Config:
        from_attributes = True

# Mock database of sign language dictionary entries
SIGN_DICTIONARY_DB = [
    {
        "id": 1,
        "sign_name": "Hello",
        "category": "Greetings",
        "difficulty_level": "Beginner",
        "description": "Raise your hand with fingers extended and touch your forehead, then move it slightly outward.",
        "video_url": "https://example.com/videos/hello.mp4"
    },
    {
        "id": 2,
        "sign_name": "Thank You",
        "category": "Common Phrases",
        "difficulty_level": "Beginner",
        "description": "Touch your fingertips to your chin and move your hand forward and down toward the person.",
        "video_url": "https://example.com/videos/thank_you.mp4"
    },
    {
        "id": 3,
        "sign_name": "Help",
        "category": "Emergency & Support",
        "difficulty_level": "Intermediate",
        "description": "Place one flat hand on top of the other fist and lift both upwards together.",
        "video_url": "https://example.com/videos/help.mp4"
    }
]

# 1. Search or List Dictionary Signs Endpoint
@router.get("/signs", response_model=List[DictionarySignResponse])
def get_dictionary_signs(search: Optional[str] = Query(None, description="Search term for sign name or category")):
    """
    Retrieves all available signs or filters them by name/category query parameters.
    """
    if search:
        filtered = [
            sign for sign in SIGN_DICTIONARY_DB 
            if search.lower() in sign["sign_name"].lower() or search.lower() in sign["category"].lower()
        ]
        return filtered
    return SIGN_DICTIONARY_DB

# 2. Get Specific Sign Details by ID Endpoint
@router.get("/signs/{sign_id}", response_model=DictionarySignResponse)
def get_sign_by_id(sign_id: int):
    """
    Retrieves detailed instructions and metadata for a specific sign ID.
    """
    for sign in SIGN_DICTIONARY_DB:
        if sign["id"] == sign_id:
            return sign
            
    raise HTTPException(status_code=404, detail="Sign entry not found in the dictionary.")