from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

from app.utils.validation import reject_malicious


class LessonCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    content_description: str = Field(..., min_length=1, max_length=2000)
    expected_gesture: str = Field(..., min_length=1, max_length=5)

    @field_validator("title", "content_description", "expected_gesture")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)


class LessonResponse(BaseModel):
    lesson_id: str
    module_id: str
    title: str
    content_description: str
    expected_gesture: str

    class Config:
        from_attributes = True


class ModuleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1, max_length=2000)
    course_id: str = Field(..., min_length=1, max_length=36)

    @field_validator("title", "description", "course_id")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)


class ModuleResponse(BaseModel):
    module_id: Optional[str] = None
    course_id: str
    title: str
    description: str
    lessons: List[LessonResponse] = []

    class Config:
        from_attributes = True
