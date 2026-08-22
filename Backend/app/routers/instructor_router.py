from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, PracticeSession, Assessment
from app.utils.validation import reject_malicious
from app.utils.security import verify_token_and_role
from datetime import datetime as _dt

router = APIRouter(prefix="/api/instructor", tags=["Instructor-Student Management"])

class AssignStudentRequest(BaseModel):
    instructor_email: str
    student_email: str

    @field_validator("instructor_email", "student_email")
    @classmethod
    def _reject_malicious_emails(cls, value: str) -> str:
        return reject_malicious(value)

@router.post("/assign-student", status_code=status.HTTP_200_OK)
def assign_student_to_instructor(
    data: AssignStudentRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"])),
):
    acting_user_id = token_payload.get("user_id")
    acting_role = token_payload.get("role")

    instructor = db.query(User).filter(User.email == data.instructor_email, User.role == "Instructor").first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found or user is not an instructor.")

    # Non-admin must act only on their own account.
    if acting_role != "Admin" and str(acting_user_id) != str(instructor.id):
        raise HTTPException(status_code=403, detail="You may only assign students to your own instructor account.")

    student = db.query(User).filter(User.email == data.student_email).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    student.instructor_id = instructor.id
    db.commit()

    return {
        "message": "Student successfully assigned to instructor.",
        "instructor": instructor.username,
        "student": student.username
    }

@router.get("/students/{instructor_email}", status_code=status.HTTP_200_OK)
def get_instructor_students(
    instructor_email: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Instructor", "Admin"])),
):
    instructor = db.query(User).filter(User.email == instructor_email).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found.")

    assigned_students = db.query(User).filter(User.instructor_id == instructor.id).all()

    student_list = []
    for s in assigned_students:
        sessions = (
            db.query(PracticeSession)
            .filter(PracticeSession.user_id == s.id, PracticeSession.status == "completed")
            .all()
        )
        assessments: list = []
        for session in sessions:
            assessments.extend(session.assessments)

        lessons_completed = len({session.lesson_id for session in sessions})
        accuracies = [a.overall_accuracy for a in assessments if a.overall_accuracy is not None]
        avg_accuracy = round(sum(accuracies) / len(accuracies), 1) if accuracies else 0.0

        last_active = None
        for session in sessions:
            ts = session.ended_at or session.started_at
            if last_active is None or (ts or _dt.min) > last_active:
                last_active = ts
        status_label = "Active" if last_active and (_dt.utcnow() - last_active).days <= 7 else "Inactive"

        student_list.append({
            "student_id": str(s.id),
            "username": s.username,
            "email": s.email,
            "progress_summary": {
                "lessons_completed": lessons_completed,
                "average_accuracy": f"{avg_accuracy}%",
                "status": status_label,
            }
        })

    return {
        "instructor_email": instructor_email,
        "total_students": len(student_list),
        "students": student_list
    }