import uuid
from app.db.database import SessionLocal
from app.db import models

def seed():
    db = SessionLocal()
    try:
        course = db.query(models.Course).first()
        if not course:
            course = models.Course(title="Default Course", level="Beginner")
            db.add(course)
            db.commit()
            db.refresh(course)

        module = db.query(models.Module).first()
        if not module:
            module = models.Module(course_id=course.id, module_name="Alphabet Basics")
            db.add(module)
            db.commit()
            db.refresh(module)

        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            slug = f"les_alphabet_{char.lower()}"
            existing = db.query(models.Lesson).filter(models.Lesson.slug == slug).first()
            if not existing:
                lesson = models.Lesson(
                    slug=slug,
                    module_id=module.id,
                    title=f"Alphabet {char}",
                    expected_gesture=char,
                    category="alphabet",
                    difficulty="easy"
                )
                db.add(lesson)
                print(f"Added: {lesson.title}")
        db.commit()
        print("Seeding complete.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
