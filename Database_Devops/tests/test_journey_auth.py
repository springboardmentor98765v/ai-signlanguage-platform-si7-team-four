import requests
import uuid
import sys
from sqlalchemy import create_engine, text

BASE_URL = "http://localhost:8000"
DB_URL = "postgresql+psycopg2://signlang:signlang_dev_pw@localhost:5432/signlang_db"

results = []


def check(description, condition, extra=""):
    status = "PASS" if condition else "FAIL"
    results.append((description, status))
    print(f"[{status}] {description}" + (f" - {extra}" if extra else ""))
    return condition


def main():
    test_email = f"day6_journey_{uuid.uuid4().hex[:8]}@example.com"
    test_username = f"day6user_{uuid.uuid4().hex[:8]}"
    test_password = "TestPass123!"

    print("=" * 70)
    print("INTEGRATION TEST: Auth Journey (register -> login -> dashboard)")
    print("=" * 70)

    resp = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "username": test_username,
            "email": test_email,
            "password": test_password,
            "role": "Learner",
        },
    )
    ok = check("Register returns 201", resp.status_code == 201, f"got {resp.status_code}")
    if not ok:
        print(f"        Response body: {resp.text}")
        sys.exit(1)

    user_id = resp.json().get("user_id")
    check("Register response includes user_id", bool(user_id), user_id)

    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, username, email, role FROM users WHERE id = :uid"),
            {"uid": user_id},
        ).fetchone()
    check("User row exists in Postgres users table", row is not None)
    if row:
        check("Persisted email matches what was registered", row[2] == test_email)
        check("Persisted role matches what was registered", row[3] == "Learner")

    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": test_email, "password": test_password},
    )
    ok = check("Login returns 200", resp.status_code == 200, f"got {resp.status_code}")
    if not ok:
        print(f"        Response body: {resp.text}")
        sys.exit(1)

    access_token = resp.json().get("access_token")
    check("Login response includes access_token", bool(access_token))

    resp = requests.get(
        f"{BASE_URL}/api/auth/dashboard/learner",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    check("Learner dashboard accessible with valid token", resp.status_code == 200, f"got {resp.status_code}")

    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": test_email, "password": "WrongPassword!"},
    )
    check("Login with wrong password returns 401", resp.status_code == 401, f"got {resp.status_code}")

    print("\n" + "=" * 70)
    passed = sum(1 for _, s in results if s == "PASS")
    print(f"SUMMARY: {passed}/{len(results)} checks passed")
    print("=" * 70)

    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
