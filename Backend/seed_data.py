import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.models import models

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # This automatically creates a list for A through Z
    lessons_to_add = [
        {"slug": f"les_alphabet_{char.lower()}", "title": f"Alphabet {char.upper()}", "expected_gesture": char.upper()}
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ]

    try:
        module = db.query(models.Module).first()
        if not module:
            course = models.Course(title="Default Course", level="Beginner")
            db.add(course)
            db.commit()
            db.refresh(course)
            module = models.Module(course_id=course.id, module_name="Alphabet Basics")
            db.add(module)
            db.commit()
            db.refresh(module)

        for item in lessons_to_add:
            existing = db.query(models.Lesson).filter(models.Lesson.slug == item["slug"]).first()
            if not existing:
                new_lesson = models.Lesson(
                    id=str(uuid.uuid4()),
                    slug=item["slug"],
                    module_id=module.id,
                    title=item["title"],
                    expected_gesture=item["expected_gesture"],
                    category="alphabet",
                    difficulty="easy"
                )
                db.add(new_lesson)
                print(f"Added: {item['title']}")
        
        db.commit()
        print("Seeding complete.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()