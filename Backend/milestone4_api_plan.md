# Milestone 4 - Day 1 Backend API Plan (Intern 2 - Backend & API Developer)

Status: **Draft for Day 2** - Date: 2026-08-16. Final milestone (M4). Scope = finish the
Accessibility Trainer role + dashboard, NOT new features. Cross-team: Intern 1 (Frontend,
dashboard UI), Intern 4 (Business Logic, metric formulas), Intern 3 (AI).

---

## 1. Re-Test of Every Existing API (Milestones 1-3) - PASSING

The app was started locally (`AI_SERVICE_URL=http://127.0.0.1:8001 uvicorn app.main:app
--port 8000`) with the AI service running on port 8001, and every registered endpoint was
probed with `httpx` against `http://127.0.0.1:8000` (script: `/tmp/retest_m4_day1.py`).

**Result: 62/62 probes passed.** Live `/openapi.json` exposes 44 paths. No broken endpoints
found; nothing needed fixing.

| Area | Endpoints probed | Result |
| :--- | :--- | :--- |
| System | `/health`, `/` | 200 / 200 |
| Auth | register (L/I/A), login (200 + wrong-pw 401), refresh-token, learner dashboard (200 + RBAC 403), instructor dashboard (200 + RBAC 403), forgot-password (200 + unknown-email 404) | OK |
| Profile | `PATCH /api/users/me`, `POST /api/users/change-password` | OK |
| Lessons | list / advanced / by-id / create (Instructor 201, Learner 403) / update / delete / bulk-upload-csv | OK |
| Courses | modules / module-lessons / create module (Instructor 201, Learner 403) | OK |
| Practice | start / submit (real AI relay) / submit bad image 400 / end missing-session 404 | OK |
| Notifications | create / list / mark-read | OK |
| Admin | users list (+ non-admin 403) / user-status / user-role / delete / bulk-delete / bulk-status / bulk-role / bulk-user-status / bulk-upload-lessons (CSV) | OK |
| Instructor | assign-student / students list | OK |
| Integration | test-sync | OK |
| M1/M2 v1 | dictionary signs(+/{id}), feedback submit(+all), progress update/get, translations history/log, gesture evaluate/upload-frame | OK |
| Security | security headers (nosniff, frame-options, SRI) | OK |
| Rate limit | login hammered -> 429 | OK |

Automated suite also re-confirmed green: `python3 -m pytest -q` in `Backend/` -> **87 passed**
in ~13s.

---

## 2. Current Role System (audit)

- Single source of truth for allowed roles:
  `Backend/app/utils/validation.py` -> `ALLOWED_ROLES = {"Learner", "Instructor", "Admin"}`.
- Enforced at registration via `UserRegister._validate_role` (`Backend/app/schemas/user.py`)
  and at admin role-change via `admin_router.py` (`RoleUpdateRequest._validate_role`).
- JWT carries `{"user_id", "username", "role"}`; RBAC enforced by
  `verify_token_and_role([...])` (`Backend/app/utils/security.py`).

**Confirmed: "Accessibility Trainer" does NOT exist today.** It is not in `ALLOWED_ROLES`,
so `POST /api/auth/register` and `PATCH /api/admin/user-role` currently reject it with 422.
Adding it is a one-line change to `ALLOWED_ROLES` (plus a name constant re-used by the
register validator and the new trainer router).

---

## 3. New APIs Required This Milestone (Accessibility Trainer)

All endpoints below are **new** and must be registered in `app/main.py` (none exist today).
Intern 1 builds the corresponding Trainer dashboard on top of these.

### 3.1 Role addition

| # | Change | File |
| :--- | :--- | :--- |
| 1 | Add `"Accessibility Trainer"` to `ALLOWED_ROLES` | `app/utils/validation.py` |
| 2 | `POST /api/auth/register` and `PATCH /api/admin/user-role` accept the new role automatically (already whitelist-driven; re-test after change) | `app/schemas/user.py`, `app/routers/admin_router.py` |

Note: the JWT role string will be `"Accessibility Trainer"` (with the space), exactly as
registered - keep it consistent for RBAC.

### 3.2 New trainer endpoints (all RBAC `["Accessibility Trainer"]` via `verify_token_and_role`)

| # | Method | Path | Purpose |
| :--- | :--- | :--- | :--- |
| 1 | GET | `/api/trainer/learners` | List learners assigned to the calling trainer. |
| 2 | GET | `/api/trainer/learners/{learner_id}/engagement` | Engagement data (practice sessions/attempts, recency, notifications). |
| 3 | GET | `/api/trainer/learners/{learner_id}/skill-development` | Skill/improvement trajectory (accuracy over time, weak letters). |
| 4 | GET | `/api/trainer/learners/{learner_id}/assessment-analytics` | Average scores, attempt counts, pass rates from assessment records. |
| 5 | GET | `/api/trainer/learners/{learner_id}/certification-status` | Pass / fail / proficiency level from certificates + assessment history. |

**Learner assignment (which learners belong to a trainer):** reuse the existing
`users.instructor_id` column (same pattern the Instructor role uses), i.e. a learner is a
trainer's learner when `user.role == "Learner"` and `user.instructor_id == <trainer id>`.
Reuses the already-tested `instructor_router` assignment flow; requires NO new table.
*(If Intern 4's design later needs a distinct mapping, we add it then - flagged as open
question, not scope.)*

### 3.3 Data sources for the metrics (real, derived from existing tables)

No new tables. The endpoints compute numbers from records that already exist in
`app_data.db` (SQLite) and in the models (`Backend/app/models/models.py`):

| Metric API | Derived from |
| :--- | :--- |
| `/learners` | `users` (role Learner, `instructor_id` = trainer), joined with `analytics_summary` |
| `/engagement` | `practice_sessions` (count, `attempt_count`, duration, latest `started_at`), `notifications` (unread count) |
| `/skill-development` | `assessments` (`overall_accuracy`, `is_correct`, `confidence`, `created_at`) and `weekly_analytics.weak_letters`; returns per-week accuracy trend |
| `/assessment-analytics` | `assessments` (avg accuracy, avg confidence, total, correct %, per-letter breakdown) |
| `/certification-status` | `certificates` (`overall_score`, `issued_date`) + `assessments` recent-average -> "pass"/"fail"/level |

### 3.4 Intern 4 (Business Logic) ownership note - IMPORTANT

The **underlying formulas** (what counts as "engaged", how skill improvement is scored, how
assessment analytics are weighted, where the certificate pass threshold is set) are owned by
**Intern 4 (Business Logic)**.

- In this repo, before Intern 4's code exists, we build **reasonable, deterministic
  derived calculations** directly from the tables above so the 5 endpoints are **real and
  functional** (not mocks/`[]`), return stable numbers, and are unit-testable.
- Every placeholder formula will be **clearly marked in code and in Swagger descriptions
  as `# PENDING Intern 4 final formula`**, plus a one-line note in the endpoint response
  (`"formula_owner": "Intern 4 pending"`) so frontend/QA know the numbers may change when
  Intern 4 lands.
- Suggested default formulas (to be reviewed with Intern 4 on Day 2):
  - Engagement score = weighted engagement over last 7 / 30 days (practice sessions per
    week, attempts per session, unread-notification penalty).
  - Skill improvement = accuracy trend slope over completed assessments + `weak_letters`
    regression rate.
  - Assessment analytics = simple means (accuracy, confidence) + per-letter `is_correct`
    pass rate + count of assessments.
  - Certification status = latest `Certificate.overall_score`. `>= 80` = "passed", `>= 60`
    = "in-progress/conditional", else "not-passed"; level = buckets on the same score.
    Thresholds are placeholders pending Intern 4.

---

## 4. Milestone 4 Day 2 Plan (backlog for Day 2, documented so it is "agreed")

1. **Role**: add `"Accessibility Trainer"` to `ALLOWED_ROLES`; re-test register + admin
   role-change accept it and issue working JWT.
2. **Trainer service** (`app/services/trainer_service.py`): query helpers for the five
   endpoints described in 3.3.
3. **Trainer router** (`app/routers/trainer_router.py`): register the 5 endpoints, all
   behind `verify_token_and_role(["Accessibility Trainer"])`, with explicit summaries/
   descriptions (Intern 1 uses `/docs`).
4. **Schemas** (`app/schemas/trainer.py`): response models shown in Swagger.
5. **Assignment flow**: allow a Trainer to be linked to learners - reuse
   `POST /api/instructor/assign-student` is Instructor-specific; add
   `POST /api/trainer/assign-learner` only if needed (prefer reusing
   `users.instructor_id` directly for MVP; decide with Intern 4).
6. **Tests** (`Backend/test_trainer.py`): role acceptance, RBAC 403 for Learner/Admin,
   and endpoint shapes with seeded practice/assessment/certificate rows.
7. **Docs**: update `Backend/docs/frontend_integration_notes.md` with the trainer
   contracts; update `/health` milestone tracker to M4.
8. Re-run `pytest Backend/` (target: existing 87 + new trainer tests all green).

---

## 6. Day 2 - Implemented (2026-08-16)

All five trainer endpoints are built, registered in `app/main.py`, RBAC-protected
with the same `verify_token_and_role(["Accessibility Trainer"])` pattern as the
existing dashboards, and live in Swagger under the **Accessibility Trainer** tag:

| Endpoint | Status |
| :--- | :--- |
| `GET /api/trainer/learners` | Live - assigned learners of the logged-in trainer |
| `POST /api/trainer/assign-learner` | Live - links a Learner to the trainer (idempotent) |
| `GET /api/trainer/learners/{id}/engagement` | Live - derived from `practice_sessions` |
| `GET /api/trainer/learners/{id}/skill-development` | Live - derived from `assessments` + `weekly_analytics` |
| `GET /api/trainer/learners/{id}/assessment-analytics` | Live - aggregated from `assessments` (incl. per-letter) |
| `GET /api/trainer/learners/{id}/certification-status` | Live - from `certificates`; `not_attempted` when none |

**Assignment mechanism decision (per Day-1 task):** a dedicated
`TrainerLearnerLink` model (`trainer_id`, `learner_id`, `assigned_at`,
table `trainer_learner_links`) was chosen over reusing `users.instructor_id`,
because that column is Instructor-flavored and shared with the separate
Instructor flow. A dedicated table keeps trainer assignments explicit and
does not couple the roles. (Documented in the model docstring.)

**Formula placeholders:** every metric in `app/services/trainer_service.py` is
marked `# PENDING Intern 4 final formula`; response payloads carry
`"formula_owner": "Intern 4 (pending)"` so frontend/QA know values may change.

**Role change:** `"Accessibility Trainer"` added to `ALLOWED_ROLES`; role column
widened to `String(30)` (21-char role); test suite covers register + RBAC 401/403.

**Tests:** `Backend/test_trainer.py` added. Full suite: `python3 -m pytest -q`
-> **92 passed** (87 existing + 5 trainer).

---

## 5. Checkpoints (updated Day 2)

- [x] All existing APIs re-tested and confirmed working (62/62 live probes, 44/44 paths,
      87 pytest green on Day 1)
- [x] List of missing Accessibility Trainer APIs written (section 3)
- [x] Plan for Day 2 agreed (section 4) - implemented (section 6)
- [x] "Get my assigned learners" API working for the Trainer role
- [x] Engagement / skill / analytics / certification-status APIs working
- [x] Access correctly restricted to the Accessibility Trainer role only (401/403 verified)

---

## 8. Deployment & Database Decision (Day 5)

**Decision: keep the two-tier DB approach — no forced migration.**

- **Local (non-Docker) development** keeps the file-based SQLite default
  (`Backend/app/db/database.py`, `app_data.db`). This is what the pytest suite
  targets and is the fastest dev loop.
- **Containerised / production** (`Dockerfile.backend` + `docker-compose.yml`)
  already uses the `Database_Devops/app/db/database.py` layer, which reads
  `DATABASE_URL` (defaulting to the compose `postgres` service). The PostgreSQL
  data persists across restarts via the named `signlang_pgdata` volume, so
  **no data is lost on container restart** — the SQLite-persistence concern
  does not apply to the compose stack.
- **Hosted free-tier DB (Supabase / Neon) is NOT wired up in this repo.** If a
  later milestone wants it, the app needs no code change: set `DATABASE_URL`
  in `.env.production` to the hosted postgres URL and the container's db layer
  connects automatically. This requires the operators to:
  1. provision the hosted Postgres instance,
  2. run schema creation (`Base.metadata.create_all` runs on startup),
  3. seed data via `Backend/seed_data.py`.
- Production env template lives at `Backend/.env.production.example`
  (placeholders only; real `.env.production` is git-ignored).

### Container changes (Day 5)

- `Dockerfile.backend`: base image pinned to `python:3.11.9-slim`; deps from
  `Backend/requirements.txt` (already includes slowapi + sqlalchemy + reportlab
  added in M3/M4) + `Database_Devops/requirements.txt` (psycopg2-binary).
  uvicorn runs **without `--reload`**, on `0.0.0.0:$PORT` with
  `$WEB_CONCURRENCY` workers and `--proxy-headers`.
- `docker-compose.yml`: backend now receives `SECRET_KEY`/`JWT_SECRET`,
  `ALLOWED_ORIGINS`, `AI_SERVICE_URL`, `WEB_CONCURRENCY` env; Postgres data
  persists on the `signlang_pgdata` volume.
- `Backend/app/main.py`: CORS origins read from `ALLOWED_ORIGINS`
  (comma-separated; default `*`).
- `.dockerignore`: excludes `.env*`, `app_data.db*`, pycache, logs from the
  build context so secrets and dev data never enter the image.