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
    role = Column(String(30), nullable=False, default="Learner")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    instructor_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)

    sessions = relationship("PracticeSession", back_populates="user")
    analytics = relationship("AnalyticsSummary", back_populates="user", uselist=False)
    weekly_analytics = relationship("WeeklyAnalytics", back_populates="user")
    certificates = relationship("Certificate", back_populates="user")


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
    slug = Column(String(100), unique=True, index=True)
    module_id = Column(UUID(as_uuid=False), ForeignKey("modules.id"), nullable=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    expected_gesture = Column(String(5), nullable=True)
    category = Column(String(20), nullable=False, default="alphabet")
    difficulty = Column(String(20), nullable=False, default="easy")

    module = relationship("Module", back_populates="lessons")
    sessions = relationship("PracticeSession", back_populates="lesson")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=False), ForeignKey("lessons.id"), nullable=False)
    status = Column(String(20), default="initialized")
    attempt_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    lesson = relationship("Lesson", back_populates="sessions")
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


class WeeklyAnalytics(Base):
    __tablename__ = "weekly_analytics"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    week_start = Column(DateTime, nullable=False)
    improvement_rate_percentage = Column(Float, nullable=True)
    weak_letters = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="weekly_analytics")


class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    issued_date = Column(DateTime, nullable=False)
    overall_score = Column(Float, nullable=False)
    pdf_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="certificates")


class InstructorStudent(Base):
    __tablename__ = "instructor_student"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    instructor_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    student_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    assigned_at = Column(DateTime, default=datetime.utcnow)


class TrainerLearnerLink(Base):
    """
    Milestone 4: Accessibility Trainer -> Learner assignment.

    One row per (trainer, learner) pair. `users.instructor_id` was considered but is
    Instructor-flavored and shared with a different role flow; a dedicated link table
    keeps Trainer assignments explicit and independently queryable.
    """
    __tablename__ = "trainer_learner_links"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    trainer_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    learner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    assigned_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# Milestone 3 - Day 2: Notifications table
# Created with Intern 5 (Database/DevOps) collaboration
# ============================================================
class Notification(Base):
    """
    Database-backed Notifications table.
    Stores all platform notifications for users, supports
    create, list (by user), and mark-as-read operations.

    NOTE: id/user_id are stored as String(36) UUIDs (not the PostgreSQL
    UUID(as_uuid=False) type used elsewhere) because the app runs on SQLite,
    whose NUMERIC column affinity converts all-numeric UUID hex strings into
    floats, corrupting/breaking reads. String(36) stores the same UUID text
    safely on SQLite while remaining a real ForeignKey to users.id.
    """
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    event_type = Column(String(50), nullable=False, default="info")
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", backref="notifications")
