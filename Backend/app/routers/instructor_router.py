from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User
from app.utils.validation import reject_malicious

router = APIRouter(prefix="/api/instructor", tags=["Instructor-Student Management"])

class AssignStudentRequest(BaseModel):
    instructor_email: str
    student_email: str

    @field_validator("instructor_email", "student_email")
    @classmethod
    def _reject_malicious_emails(cls, value: str) -> str:
        return reject_malicious(value)

@router.post("/assign-student", status_code=status.HTTP_200_OK)
def assign_student_to_instructor(data: AssignStudentRequest, db: Session = Depends(get_db)):
    instructor = db.query(User).filter(User.email == data.instructor_email, User.role == "Instructor").first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found or user is not an instructor.")
        
    student = db.query(User).filter(User.email == data.student_email).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
        
    # Assign the instructor's ID directly to the student row
    student.instructor_id = instructor.id
    db.commit()
    
    return {
        "message": "Student successfully assigned to instructor.",
        "instructor": instructor.username,
        "student": student.username
    }

@router.get("/students/{instructor_email}", status_code=status.HTTP_200_OK)
def get_instructor_students(instructor_email: str, db: Session = Depends(get_db)):
    instructor = db.query(User).filter(User.email == instructor_email).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found.")
        
    # Query all students where instructor_id matches this instructor's ID
    assigned_students = db.query(User).filter(User.instructor_id == instructor.id).all()
    
    student_list = []
    for s in assigned_students:
        student_list.append({
            "student_id": s.id,
            "username": s.username,
            "email": s.email,
            "progress_summary": {
                "lessons_completed": 12,
                "average_accuracy": "88.5%",
                "status": "Active"
            }
        })
        
    return {
        "instructor_email": instructor_email,
        "total_students": len(student_list),
        "students": student_list
    }