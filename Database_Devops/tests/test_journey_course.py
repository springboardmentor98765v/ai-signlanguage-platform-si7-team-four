import requests
import uuid
import sys

BASE_URL = "http://localhost:8000"

results = []


def check(description, condition, extra=""):
    status = "PASS" if condition else "FAIL"
    results.append((description, status))
    print(f"[{status}] {description}" + (f" - {extra}" if extra else ""))
    return condition


def main():
    test_email = f"day6_instructor_{uuid.uuid4().hex[:8]}@example.com"
    test_username = f"day6instructor_{uuid.uuid4().hex[:8]}"
    test_password = "TestPass123!"

    print("=" * 70)
    print("INTEGRATION TEST: Course Catalog Journey (mock-backed, see note below)")
    print("=" * 70)

    resp = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "username": test_username,
            "email": test_email,
            "password": test_password,
            "role": "Instructor",
        },
    )
    ok = check("Register (Instructor) returns 201", resp.status_code == 201, f"got {resp.status_code}")
    if not ok:
        print(f"        Response body: {resp.text}")
        sys.exit(1)

    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": test_email, "password": test_password},
    )
    ok = check("Login returns 200", resp.status_code == 200, f"got {resp.status_code}")
    if not ok:
        print(f"        Response body: {resp.text}")
        sys.exit(1)

    access_token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(f"{BASE_URL}/courses/modules")
    ok = check("GET /courses/modules returns 200", resp.status_code == 200, f"got {resp.status_code}")
    if not ok:
        print(f"        Response body: {resp.text}")
        sys.exit(1)

    baseline_count = len(resp.json())
    check("Modules list is valid JSON array", isinstance(resp.json(), list))

    resp = requests.post(
        f"{BASE_URL}/courses/modules",
        json={
            "title": "Day 6 Test Module",
            "description": "Created by integration test",
            "course_id": "day6-test-course",
        },
        headers=headers,
    )
    ok = check("POST /courses/modules returns 201 (with Instructor token)", resp.status_code == 201, f"got {resp.status_code}")
    if not ok:
        print(f"        Response body: {resp.text}")
        sys.exit(1)

    resp = requests.get(f"{BASE_URL}/courses/modules")
    new_count = len(resp.json()) if resp.status_code == 200 else -1
    check(
        "Module count increased after creation",
        new_count == baseline_count + 1,
        f"before={baseline_count}, after={new_count}",
    )

    resp = requests.post(
        f"{BASE_URL}/courses/modules",
        json={"title": "Should Fail", "description": "No auth", "course_id": "x"},
    )
    check("POST /courses/modules without token returns 401", resp.status_code == 401, f"got {resp.status_code}")

    print("\n" + "=" * 70)
    passed = sum(1 for _, s in results if s == "PASS")
    print(f"SUMMARY: {passed}/{len(results)} checks passed")
    print("NOTE: This journey is backed by in-memory mock data (MOCK_MODULE_DB), not")
    print("Postgres. Real DB persistence for course/module creation is NOT yet wired up.")
    print("Flagged to Intern 2 (Backend/API owner) as a Day 6 finding.")
    print("=" * 70)

    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
