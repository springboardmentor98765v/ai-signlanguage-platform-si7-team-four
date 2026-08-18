import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
)
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

    # Increased from 20 to 50 so "Accessibility Trainer" fits safely.
    role = Column(String(50), nullable=False, default="Learner")

    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("PracticeSession", back_populates="user")
    analytics = relationship(
        "AnalyticsSummary",
        back_populates="user",
        uselist=False,
    )

    certificates = relationship("Certificate", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    weekly_analytics = relationship("WeeklyAnalytics", back_populates="user")

    students_assigned = relationship(
        "InstructorStudent",
        foreign_keys="InstructorStudent.instructor_id",
        back_populates="instructor",
    )

    instructors_assigned = relationship(
        "InstructorStudent",
        foreign_keys="InstructorStudent.student_id",
        back_populates="student",
    )

    notifications = relationship("Notification", back_populates="user")
    user_badges = relationship("UserBadge", back_populates="user")

    streak = relationship(
        "Streak",
        back_populates="user",
        uselist=False,
    )

    # Correct User <-> CertificationExamResult relationship.
    certification_exam_results = relationship(
        "CertificationExamResult",
        back_populates="user",
    )

    trainer_assignments = relationship(
        "AccessibilityTrainerLearner",
        foreign_keys="AccessibilityTrainerLearner.trainer_id",
        back_populates="trainer",
    )

    learner_assignments = relationship(
        "AccessibilityTrainerLearner",
        foreign_keys="AccessibilityTrainerLearner.learner_id",
        back_populates="learner",
    )


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
    course_id = Column(
        UUID(as_uuid=False),
        ForeignKey("courses.id"),
        nullable=False,
    )
    module_name = Column(String(150), nullable=False)

    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    slug = Column(String(100), unique=True, nullable=True)
    module_id = Column(
        UUID(as_uuid=False),
        ForeignKey("modules.id"),
        nullable=False,
    )
    title = Column(String(150), nullable=False)
    description = Column(Text)
    expected_gesture = Column(String(5), nullable=False)
    category = Column(
        String(20),
        nullable=False,
        default="alphabet",
        index=True,
    )
    difficulty = Column(String(20), nullable=False, default="easy")

    module = relationship("Module", back_populates="lessons")
    recommendations = relationship("Recommendation", back_populates="lesson")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    lesson_id = Column(
        UUID(as_uuid=False),
        ForeignKey("lessons.id"),
        nullable=False,
    )
    status = Column(String(20), default="initialized")
    attempt_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    assessments = relationship("Assessment", back_populates="session")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    session_id = Column(
        UUID(as_uuid=False),
        ForeignKey("practice_sessions.id"),
        nullable=False,
    )
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
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    overall_accuracy_percentage = Column(
        Float,
        default=0.0,
        index=True,
    )
    lessons_completed = Column(Integer, default=0)
    practice_hours = Column(Float, default=0.0)
    improvement_rate_percentage = Column(Float, default=0.0)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = relationship("User", back_populates="analytics")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    issued_date = Column(DateTime, default=datetime.utcnow)
    overall_score = Column(Float, nullable=False)
    pdf_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="certificates")

    # Correct Certificate <-> CertificationExamResult relationship.
    certification_exam_results = relationship(
        "CertificationExamResult",
        back_populates="certificate",
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    lesson_id = Column(
        UUID(as_uuid=False),
        ForeignKey("lessons.id"),
        nullable=False,
    )
    reason = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")
    lesson = relationship("Lesson", back_populates="recommendations")


class InstructorStudent(Base):
    __tablename__ = "instructor_student"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    instructor_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    assigned_at = Column(DateTime, default=datetime.utcnow)

    instructor = relationship(
        "User",
        foreign_keys=[instructor_id],
        back_populates="students_assigned",
    )

    student = relationship(
        "User",
        foreign_keys=[student_id],
        back_populates="instructors_assigned",
    )


class WeeklyAnalytics(Base):
    __tablename__ = "weekly_analytics"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    week_start = Column(DateTime, nullable=False)
    improvement_rate_percentage = Column(Float, nullable=True)
    weak_letters = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="weekly_analytics")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    related_id = Column(UUID(as_uuid=False), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    criteria_description = Column(Text, nullable=True)
    icon_name = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_badges = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "badge_id",
            name="uq_user_badge",
        ),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    badge_id = Column(
        UUID(as_uuid=False),
        ForeignKey("badges.id"),
        nullable=False,
    )
    earned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="user_badges")
    badge = relationship("Badge", back_populates="user_badges")


class Streak(Base):
    __tablename__ = "streaks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    current_streak_count = Column(Integer, default=0, nullable=False)
    longest_streak_count = Column(Integer, default=0, nullable=False)
    last_practice_date = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = relationship("User", back_populates="streak")


class CertificationExamResult(Base):
    __tablename__ = "certification_exam_results"

    __table_args__ = (
        Index(
            "ix_cert_exam_level_passed",
            "level",
            "passed",
        ),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)

    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    level = Column(String(20), nullable=False)
    signs_tested = Column(Text, nullable=True)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    certificate_id = Column(
        UUID(as_uuid=False),
        ForeignKey("certificates.id"),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    # User <-> CertificationExamResult
    user = relationship(
        "User",
        back_populates="certification_exam_results",
    )

    # Certificate <-> CertificationExamResult
    certificate = relationship(
        "Certificate",
        back_populates="certification_exam_results",
    )


class AccessibilityTrainerLearner(Base):
    __tablename__ = "accessibility_trainer_learner"

    __table_args__ = (
        UniqueConstraint(
            "trainer_id",
            "learner_id",
            name="uq_trainer_learner",
        ),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_id)

    trainer_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    learner_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    assigned_at = Column(DateTime, default=datetime.utcnow)

    trainer = relationship(
        "User",
        foreign_keys=[trainer_id],
        back_populates="trainer_assignments",
    )

    learner = relationship(
        "User",
        foreign_keys=[learner_id],
        back_populates="learner_assignments",
    )


Index(
    "ix_streaks_current_streak_count",
    Streak.current_streak_count,
)
