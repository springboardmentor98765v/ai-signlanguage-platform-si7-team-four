from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://signlang:signlang_dev_pw@postgres:5432/signlang_db",
)

engine = create_engine(DATABASE_URL)

issues_found = []


def run_check(description, query):
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        if rows:
            issues_found.append((description, rows))
            print(f"[ISSUE] {description}: {len(rows)} row(s) found")
            for row in rows:
                print(f"        {row}")
        else:
            print(f"[OK]    {description}: no issues found")


print("=" * 70)
print("DATA INTEGRITY CHECK - Milestone 3 Day 4")
print("=" * 70)

print("\n--- Duplicate checks ---")

run_check(
    "Duplicate active recommendations (same user + lesson, both active)",
    """
    SELECT user_id, lesson_id, COUNT(*) as cnt
    FROM recommendations
    WHERE is_active = true
    GROUP BY user_id, lesson_id
    HAVING COUNT(*) > 1
    """,
)

run_check(
    "Duplicate instructor-student assignments (same pair assigned more than once)",
    """
    SELECT instructor_id, student_id, COUNT(*) as cnt
    FROM instructor_student
    GROUP BY instructor_id, student_id
    HAVING COUNT(*) > 1
    """,
)

run_check(
    "Multiple certificates issued to the same user on the same day",
    """
    SELECT user_id, DATE(issued_date) as day, COUNT(*) as cnt
    FROM certificates
    GROUP BY user_id, DATE(issued_date)
    HAVING COUNT(*) > 1
    """,
)

print("\n--- Missing required field checks ---")

run_check(
    "Users with empty username or email",
    """
    SELECT id, username, email FROM users
    WHERE username IS NULL OR username = '' OR email IS NULL OR email = ''
    """,
)

run_check(
    "Lessons with missing expected_gesture",
    """
    SELECT id, title FROM lessons
    WHERE expected_gesture IS NULL OR expected_gesture = ''
    """,
)

print("\n--- Orphaned record checks ---")

run_check(
    "Practice sessions with no matching user",
    """
    SELECT ps.id, ps.user_id FROM practice_sessions ps
    LEFT JOIN users u ON ps.user_id = u.id
    WHERE u.id IS NULL
    """,
)

run_check(
    "Practice sessions with no matching lesson",
    """
    SELECT ps.id, ps.lesson_id FROM practice_sessions ps
    LEFT JOIN lessons l ON ps.lesson_id = l.id
    WHERE l.id IS NULL
    """,
)

run_check(
    "Assessments with no matching practice session",
    """
    SELECT a.id, a.session_id FROM assessments a
    LEFT JOIN practice_sessions ps ON a.session_id = ps.id
    WHERE ps.id IS NULL
    """,
)

run_check(
    "Instructor-student rows pointing to a non-existent user",
    """
    SELECT ins.id, ins.instructor_id, ins.student_id FROM instructor_student ins
    LEFT JOIN users ui ON ins.instructor_id = ui.id
    LEFT JOIN users us ON ins.student_id = us.id
    WHERE ui.id IS NULL OR us.id IS NULL
    """,
)

run_check(
    "Notifications with no matching user",
    """
    SELECT n.id, n.user_id FROM notifications n
    LEFT JOIN users u ON n.user_id = u.id
    WHERE u.id IS NULL
    """,
)

run_check(
    "Streaks with no matching user",
    """
    SELECT s.id, s.user_id FROM streaks s
    LEFT JOIN users u ON s.user_id = u.id
    WHERE u.id IS NULL
    """,
)

run_check(
    "User_badges with no matching user or badge",
    """
    SELECT ub.id, ub.user_id, ub.badge_id FROM user_badges ub
    LEFT JOIN users u ON ub.user_id = u.id
    LEFT JOIN badges b ON ub.badge_id = b.id
    WHERE u.id IS NULL OR b.id IS NULL
    """,
)

print("\n" + "=" * 70)
if issues_found:
    print(f"SUMMARY: {len(issues_found)} check(s) found issues. See [ISSUE] lines above.")
else:
    print("SUMMARY: No integrity issues found across any check.")
    print("(Note: database currently has limited test data - see Day 4 notes.)")
print("=" * 70)
