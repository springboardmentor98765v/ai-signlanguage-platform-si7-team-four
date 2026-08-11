"""
Milestone 3 - Day 10: Demo User Seed Script
Intern 5 - Database & QA Engineer

Creates a demo learner user with a properly bcrypt-hashed password, for use
in Day 10 final demonstration / presentation. Safe to run multiple times -
skips creation if the user already exists.

Usage:
    docker compose exec -e DATABASE_URL=postgresql+psycopg2://signlang:signlang_dev_pw@postgres:5432/signlang_db backend python app/db/seed_demo_user.py
"""

import os
import uuid
import bcrypt
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://signlang:signlang_dev_pw@postgres:5432/signlang_db",
)

DEMO_USERNAME = "demo_learner"
DEMO_EMAIL = "demo_learner@example.com"
DEMO_PASSWORD = "DemoPass123!"
DEMO_ROLE = "Learner"


def main():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": DEMO_USERNAME},
        ).fetchone()

        if existing:
            print(f"[SKIP] Demo user '{DEMO_USERNAME}' already exists (id={existing[0]}). Nothing to do.")
            return

        password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        new_id = str(uuid.uuid4())

        conn.execute(
            text(
                """
                INSERT INTO users (id, username, email, password_hash, role, created_at)
                VALUES (:id, :username, :email, :password_hash, :role, now())
                """
            ),
            {
                "id": new_id,
                "username": DEMO_USERNAME,
                "email": DEMO_EMAIL,
                "password_hash": password_hash,
                "role": DEMO_ROLE,
            },
        )
        conn.commit()

        print(f"[CREATED] Demo user '{DEMO_USERNAME}' (id={new_id}, email={DEMO_EMAIL}, role={DEMO_ROLE})")
        print(f"          Login with: email={DEMO_EMAIL}  password={DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
