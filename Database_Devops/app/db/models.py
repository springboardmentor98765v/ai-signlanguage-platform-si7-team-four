import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


def new_id():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(180), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="Learner")
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("PracticeSession", back_populates="user")
    analytics = relationship("AnalyticsSummary", back_populates="user", uselist=False)


class Course(Base):
    __tablename__ = "courses"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    title = Column(String(150), nullable=False)
    description = Column(Text)
    level = Column(String(30), nullable=False, default="Beginner")

    modules = relationship("Module", back_populates="course")


class Module(Base):
    __tablename__ = "modules"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=False)
    module_name = Column(String(150), nullable=False)

    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module")


class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    module_id = Column(UUID(as_uuid=False), ForeignKey("modules.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text)
    expected_gesture = Column(String(5), nullable=False)

    module = relationship("Module", back_populates="lessons")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=False), ForeignKey("lessons.id"), nullable=False)
    status = Column(String(20), default="initialized")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    assessments = relationship("Assessment", back_populates="session")


class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    session_id = Column(UUID(as_uuid=False), ForeignKey("practice_sessions.id"), nullable=False)
    predicted_sign = Column(String(5))
    expected_sign = Column(String(5), nullable=False)
    confidence = Column(Float)
    hand_shape_score = Column(Float)
    finger_position_score = Column(Float)
    timing_score = Column(Float)
    overall_accuracy = Column(Float)
    is_correct = Column(Boolean, default=False)
    suggestions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("PracticeSession", back_populates="assessments")


class AnalyticsSummary(Base):
    __tablename__ = "analytics_summary"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)
    overall_accuracy_percentage = Column(Float, default=0.0)
    lessons_completed = Column(Integer, default=0)
    practice_hours = Column(Float, default=0.0)
    improvement_rate_percentage = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="analytics")
