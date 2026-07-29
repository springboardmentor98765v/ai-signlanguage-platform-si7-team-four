from pydantic import BaseModel
from typing import Optional, List

class LessonCreate(BaseModel):
    title: str
    content_description: str
    expected_gesture: str

class LessonResponse(BaseModel):
    lesson_id: str
    module_id: str
    title: str
    content_description: str
    expected_gesture: str

    class Config:
        from_attributes = True

class ModuleCreate(BaseModel):
    title: str
    description: str
    course_id: str  

class ModuleResponse(BaseModel):
    module_id: Optional[str] = None
    course_id: str
    title: str
    description: str
    lessons: List[LessonResponse] = []

    class Config:
        from_attributes = True