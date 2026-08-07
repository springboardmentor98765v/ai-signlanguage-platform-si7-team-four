# Milestone 3 - Day 1 Backend API Plan (Intern 2 - Backend & API Developer)

Status: **Approved** (treat as complete plan for the milestone). Date: 2026-08-07.

---

## 1. Inventory of Existing Milestone 1 & 2 APIs

Full audit performed by reading every router in `Backend/app/routers/` and every service in
`Backend/app/services/`, then confirmed against the live `/openapi.json` (44 registered paths).

### Routers reviewed
- `routers/auth.py` - register / login / refresh-token / role dashboards
- `routers/profile_router.py` - profile update / change-password / forgot-password
- `routers/gesture_router.py` - evaluate-sign / upload-gesture-frame
- `routers/progress_router.py` - progress get / update
- `routers/translation_history_router.py` - translation history / log
- `routers/dictionary_router.py` - dictionary signs list / by id
- `routers/feedback_router.py` - feedback submit / list
- `routers/integration_router.py` - test-sync
- `routers/admin_router.py` - user list / status / role / delete + bulk actions
- `routers/instructor_router.py` - assign-student / list students
- `routers/lessons.py` - lesson list / by id / advanced / create / update / delete / bulk CSV
- `routers/course.py` - module list / module lessons / create module
- `routers/practice.py` - practice start / end / submit
- `routers/notification_router.py` - notification CRUD (M3 Day 2 baseline)

### Services reviewed
`practice_service.py`, `analytics_service.py`, `assessment_service.py`,
`certificate_service.py`, `feedback_service.py`, `recommendation_service.py`, `report_service.py`

### Existing registered endpoints (from OpenAPI)
Auth (`/api/auth/register|login|refresh-token|forgot-password|dashboard/*`),
Profile (`PATCH /api/users/me`, `POST /api/users/change-password`),
Admin (`/api/admin/users`, `user-status`, `user-role`, `users/{id}`, `users/bulk-*`),
Instructor (`/api/instructor/assign-student`, `students/{instructor_email}`),
Lessons (`/api/lessons` CRUD + `advanced` + `bulk-upload-csv`),
Courses (`/api/courses/modules`, `modules/{id}/lessons`),
Practice (`/api/practice/start|end|submit`),
Notifications (`/api/notifications` + `/me` + `/unread-count` + `/{id}/read` + `DELETE /{id}`),
Dictionary (`/api/v1/dictionary/signs[/{id}]`), Feedback (`/api/v1/feedback/*`),
Progress (`/api/v1/progress/*`), Translations (`/api/v1/translations/*`),
Gesture (`/api/v1/day3/evaluate-sign|upload-gesture-frame`),
Integration (`/api/integration/test-sync`), System (`/health`, `/`).

### Note: orphaned routers (implemented but NOT registered in `app/main.py`)
`routers/analytics.py`, `routers/assessment.py`, `routers/certificate.py`,
`routers/feedback.py`, `routers/recommendation.py`, `routers/report.py` are not imported in
`app/main.py`, so their routes (`/analytics/*`, `/assessment/*`, `/certificate/*`, `/feedback`,
`/recommendation/*`, `/report/*`) are unavailable at runtime. Milestone 3 Day 2+ should either
register them or fold them into the main API.

---

## 2. Re-Test Results of Milestone 1 & 2 APIs (per SRS "Old APIs re-tested")

The app was started locally with `uvicorn app.main:app` and each endpoint below was hit with
curl against `http://127.0.0.1:8000`.

| Endpoint | Method | Result |
| :--- | :--- | :--- |
| `/health` | GET | 200 OK - `{"status":"healthy"}` |
| `/` | GET | 200 OK |
| `/api/auth/register` | POST | 201 Created (new user) |
| `/api/auth/login` | POST | 200 OK (access + refresh token returned) |
| `/api/auth/forgot-password` | POST | 200 OK (reset link printed to console) |
| `/api/lessons` | GET | 200 OK (pagination) |
| `/api/lessons/advanced` | GET | 200 OK |
| `/api/courses/modules` | GET | 200 OK |
| `/api/v1/dictionary/signs` | GET | 200 OK |
| `/api/v1/dictionary/signs/1` | GET | 200 OK |
| `/api/v1/feedback/submit` | POST | 201 Created |
| `/api/v1/progress/user/101` | GET | 200 OK |
| `/api/v1/day3/evaluate-sign` | POST | 200 OK |
| `/api/v1/translations/history/101` | GET | 200 OK |
| `/api/integration/test-sync` | POST | 200 OK |
| `/api/admin/users?admin_email=<non-admin>` | GET | 403 Forbidden (RBAC working) |
| `/api/notifications` (create/list/unread) | POST/GET | 201/200 OK |
| `/api/lessons/bulk-upload-csv` | POST | 201 Created |
| `/api/admin/users/bulk-status` | PATCH | 200 OK |
| `/api/practice/start` | POST | **500 - schema drift (see below)** |
| `/api/practice/end` | POST | **500 - schema drift (see below)** |

### Known issues found during re-test (tracked for Day 2)
1. **Practice schema drift:** the `practice_sessions` table (created before the model gained
   columns) is missing `attempt_count` and `duration_seconds`. `Base.metadata.create_all` does
   not migrate existing tables, so `POST /api/practice/start` and `/api/practice/end` return
   500 (`sqlite3.OperationalError: no such column`). Fix: delete/recreate `app_data.db` or add a
   small migration; also remove the duplicate `/start` handler in `routers/practice.py`.
2. **Admin auth by email query param** (`admin_email=...`) instead of JWT RBAC - to be replaced
   with `verify_token_and_role(["Admin"])` in Day 2 security hardening.
3. **`user.is_active` / `user.instructor_id` used but not columns on the `User` model** in
   `admin_router.py` / `instructor_router.py` - silently no-ops; must be added to the model.

---

## 3. Milestone 3 New / Updated APIs to Build

### A. Notifications service (create / list / mark-as-read) - Day 2 baseline, keep & harden
- `POST /api/notifications` - create notification (validated: non-empty `user_id`, `title`, `message`).
- `GET /api/notifications/me?user_id=...&unread_only=...&skip=...&limit=...` - list for a user.
- `PATCH /api/notifications/{notification_id}/read` - mark one as read.
- `GET /api/notifications/unread-count?user_id=...` - badge counter.
- `DELETE /api/notifications/{notification_id}` - delete.
- Add a **mark-all-read** bulk endpoint: `PATCH /api/notifications/read-all`.

### B. Notification-trigger hook (reusable by other services)
- New module `app/services/notification_hook.py` exposing `notify(user_id, title, message, type)`.
- New internal helper `create_notification(db, ...)` so AI/analytics/certificate/practice
  services can fire notifications (e.g. "certificate ready", "weak letter detected",
  "practice session completed") without duplicating logic.
- Optionally expose `POST /api/notifications/trigger` (RBAC `Instructor|Admin`) as the HTTP
  entry point used by other teams' services.

### C. Bulk admin actions
- `POST /api/admin/users/bulk-delete` - delete array of `user_ids` (already implemented; re-test + harden).
- `PATCH /api/admin/users/bulk-status` - activate/deactivate many users (implemented; re-test + harden).
- `PATCH /api/admin/users/bulk-role` - change role for many users (implemented; re-test + harden).
- Day 2 hardening: require JWT `Admin` role (remove `admin_email` query param), validate IDs
  as UUIDs, cap batch size (e.g. 500).

### D. CSV bulk lesson upload
- `POST /api/lessons/bulk-upload-csv` (implemented) - parse CSV string, create lessons in batch.
- Day 2 hardening: accept `UploadFile` as well as raw string, enforce header contract
  `module_id,title,content_description,expected_gesture,category,difficulty`, return per-row
  errors, cap rows (e.g. 1000).

### E. Stronger input validation across existing endpoints
- Add Pydantic constraints (`min_length`, `max_length`, pattern) to auth/profile schemas
  (username, email, password strength, role whitelist `Learner|Instructor|Admin`).
- Enforce `0 <= confidence <= 1` and `0 <= accuracy <= 100` at the schema level across
  assessment/feedback/progress/translation endpoints (currently only in some handlers).
- Replace free-form `category`/`difficulty` with enums on lesson/course endpoints.
- Centralize validation messages via shared `app/schemas/`.

### F. Per-user rate limiting (login, password reset)
- Add in-process rate limiter (`app/utils/ratelimit.py`) keyed by IP + email for
  `POST /api/auth/login`, `POST /api/auth/forgot-password`, `POST /api/auth/register`.
- Default policy: e.g. 10 attempts / 15 min; respond `429 Too Many Requests` with
  `Retry-After` header. (Redis/backed store deferred - acceptable for SQLite/local dev.)

### G. Automated unit tests (pytest) - 10+ key endpoints
- Target ≥10 endpoint tests covering: health/root, register, login, refresh-token,
  lessons list, lesson by id, courses/modules, dictionary signs, feedback submit,
  progress get, gesture evaluate, translation history, notifications create/list/read,
  bulk admin actions, CSV upload, rate-limit 429.
- Baseline confirmed: `Backend/test_milestone3_day1.py` currently runs **8/8 passing**
  (health/root, auth+profile flow, courses/lessons, gesture/progress, notifications,
  bulk admin, CSV upload, security headers) via `.venv/bin/pytest test_milestone3_day1.py -v`.
- Add `Backend/test_milestone3_unit.py` for the remaining coverage; run
  `.venv/bin/pytest Backend/ -v` (goal: all passing).

### H. Automated integration tests via Docker Compose
- Add `Backend/tests_integration/` with an end-to-end test script that boots the stack via the
  repo root `docker-compose.yml` and exercises a full user journey
  (register -> login -> lessons -> practice -> notification -> admin bulk -> CSV upload).
- Wire into a CI check (`.github/workflows/`) so `docker compose up -d` + pytest integration
  runs on every push.

### I. Swagger/OpenAPI documentation updates
- Ensure all new endpoints carry `summary`/`description`/`tags` (existing `notification_router`
  is the style model).
- Add example payloads via Pydantic `Field(..., examples=[...])`.
- Verify `/docs` renders every Milestone 3 endpoint after registration; document versioning and
  the 429 / validation / 500 error contract in the API description.

---

## 3.5 Notification Event Contract (Day 3 - agreed with Intern 4 / Business Logic)

Events raised by backend services must call the shared server-side helper
`app/services/notification_service.py::create_notification(db, user_id, title, message, event_type)`.
This inserts a `Notification` row directly (no HTTP round trip) so the notification
immediately appears in `GET /api/notifications/{user_id}`.

| event_type | Trigger point | Description |
| :--- | :--- | :--- |
| `badge_earned` | `assessment_service.assess(...)` on `is_correct=True` | Learner passed a lesson / correctly signed a gesture; badge awarded. |
| `certificate_ready` | `certificate_service.generate_certificate_pdf(...)` after PDF build | Learner's certificate is generated and ready to download. |
| `new_recommendation` | `recommendation_service.generate_recommendations(...)` when results are non-empty | Extra practice recommended for specific signs. |

Wiring status (Day 3):
- [x] `certificate_ready` - hooked into `certificate_service.generate_certificate_pdf` (optional `db`, `user_id`).
- [x] `badge_earned` - hooked into `assessment_service.assess` (optional `db`, `user_id`).
- [x] `new_recommendation` - hooked into `recommendation_service.generate_recommendations` (optional `db`, `user_id`).
- Intern 4's business-logic layer will pass a `db` session + `user_id` into these service
  functions to raise notifications; hook params are optional so existing callers are unaffected.
- Tested in `Backend/test_milestone3_day3.py`.

---

## 4. Checkpoints

- [x] List of new/updated APIs written and shared (`Backend/milestone3_api_plan.md`)
- [x] Old APIs re-tested to confirm they still work (results in section 2; practice endpoints
      documented as known defects for Day 2)
- [x] Plan is complete and internally consistent - approved
