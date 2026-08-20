# Day 6 — Local Integration Testing: Findings

**Milestone 3 | Intern 5 — Database & QA Engineer**
**Date tested:** 2026-08-07 (Ubuntu local dev environment)
**Stack tested:** Docker Compose — postgres (v16) + backend + ai-service, all confirmed healthy before testing began.

---

## SRS Day 6 Checkpoints

- [x] Docker Compose confirmed to start the entire local stack correctly
- [x] At least 2 full-journey local test scripts written
- [x] Tests run successfully against the local stack (one full pass, one caught a real bug — see below)

---

## Test 1: Auth Journey — test_journey_auth.py

**Result: 9/9 checks passed**

Journey: register -> verify persisted in Postgres -> login -> access role-protected dashboard -> confirm wrong password is rejected.

This confirms Auth (previously mock/in-memory as of the Milestone 2 handoff) has since been correctly wired to the real database — register writes a real row via SQLAlchemy, and login reads from it. This is a genuine improvement since M2; worth noting positively.

---

## Test 2: Course Catalog Journey — test_journey_course.py

**Result: 6/7 checks passed — 1 failure, and the failure is a real, severe bug.**

Journey: register as Instructor -> login -> list modules (baseline) -> create a module -> confirm it appears in the updated list -> confirm unauthenticated creation is rejected.

### The bug

    [PASS] POST /courses/modules returns 201 (with Instructor token) - got 201
    [FAIL] Module count increased after creation - before=1, after=-1

The second GET /courses/modules call — made immediately after a successful module creation — returned HTTP 500 for every request, from every user, until the backend container was restarted.

### Root cause (traced to Backend/app/routers/course.py)

course.router stores modules in an in-memory dictionary, MOCK_MODULE_DB, not the real modules table in Postgres (a separate finding in itself — see "Additional findings" below).

The two functions disagree on what keys belong in that dictionary:

- create_custom_module (the POST /modules handler) stores each new module without ever setting a module_id key. It sets course_id to the module's own generated id instead of a real course.

- get_all_modules (the GET /modules handler) unconditionally reads mod_data["module_id"], which raises a KeyError the moment any module lacks that key.

The only reason GET /modules worked before our test is that the one pre-seeded module (seed_alphabet_course, run at startup) happens to include a module_id key. The moment any module is created through the live API, it's missing that key, and the very next GET /modules call throws:

    File "/code/app/routers/course.py", line 51, in get_all_modules
        module_id=mod_data["module_id"],
    KeyError: 'module_id'

### Severity

High. This isn't a bug that only affects the creator — it breaks GET /courses/modules for every user on the platform, immediately, and the failure persists until someone restarts the backend. In a live environment this would mean one instructor adding a single lesson module could take down the entire course catalog for all learners.

### Status

Flagged to Intern 2 (Backend/API owner, via WhatsApp) same day. Not yet fixed as of this writeup. Backend was restarted locally to clear the corrupted in-memory state and restore normal operation for continued testing.

### Suggested fix (for Intern 2, not applied here — out of scope for Database/QA role)

Add the missing module_id key when storing a new module in create_custom_module, and use the real course_id from the input instead of the generated module id.

---

## Additional findings (from related Day 6 investigation)

These surfaced while tracing the bug above and while confirming what's reachable through the live API. Documented here for completeness; none were introduced by today's testing.

1. course.router is entirely mock-data backed (MOCK_MODULE_DB, MOCK_LESSON_DB), not connected to the real courses/modules/lessons tables in Postgres, despite those tables existing and being populated with schema since Milestone 1. Any module "created" via the API is lost on server restart and was never in the real database.

2. Duplicate route definition in Backend/app/routers/practice.py: @router.post("/start") is defined twice (once around line 35, again around line 51). The second silently overrides the first in FastAPI's routing table.

3. /practice/start is broken: practice_service.start_session() is defined with 0 parameters but is called from the router with 2 (user_id, lesson_id) — raises TypeError on every call.

4. 8 router files exist on disk but are never registered in main.py: assessment.py, certificate.py, recommendation.py, instructor_router.py, admin_router.py, analytics.py, lessons.py, report.py. Some of these correspond directly to tables built in Milestone 2 (certificates, recommendations, instructor_student) — the tables and models exist, but the API layer to use them isn't wired in.

5. Duplicate models.py files (Backend/app/models/models.py vs Database_Devops/app/db/models.py) — a known issue carried over from Milestone 2, still unresolved. Confirmed this milestone that all currently-active routers import from the older, stale file, meaning the 4 new Milestone 3 tables (notifications, badges, user_badges, streaks) are invisible to the live API layer until this is resolved.

6. A local .env misconfiguration was found and fixed during today's testing: DATABASE_URL was set to use localhost as the host, which fails when substituted into the backend container's environment by Docker Compose (inside the container, localhost refers to the container itself, not the neighboring postgres service). Changed to use postgres as the host. This was silently breaking every DB-dependent request made through the containerized backend, including basic registration.

---

## Summary for stand-up / Day 10 presentation

Local Docker Compose integration testing (Day 6) confirmed the full stack starts cleanly and that Auth now correctly persists to the real database. It also caught a severe, previously-unknown bug: creating a single course module breaks the course catalog listing endpoint for every user on the platform until the server is restarted. This is exactly the kind of cross-endpoint failure that isolated unit testing would likely miss, and is now flagged to the Backend/API owner with root cause and a suggested fix. Several additional gaps were also surfaced (unwired routers, a broken practice-session endpoint, a stale duplicate models file) and documented for the team.

