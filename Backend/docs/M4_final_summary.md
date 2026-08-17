# Milestone 4 — Final Summary (Intern 2, Backend)

**Final acceptance day (Day 7).** Everything below is the backend Intern 2 scope
for Milestone 4. Final state: **129 backend tests green**, Swagger finalised,
Docker/production-ready image builds and runs, and the same smoke + team
walkthrough suites run against a live HTTPS URL.

---

## 1. What was built this milestone

### 1.1 Accessibility Trainer APIs (Day 1–2)
Six endpoints under **/api/trainer** (tag `Accessibility Trainer`, RBAC-locked to
the `Accessibility Trainer` role — 401/403 verified):

| Endpoint | Purpose |
| :--- | :--- |
| `GET /api/trainer/learners` | trainer's assigned learners |
| `POST /api/trainer/assign-learner` | link a Learner (id or email), idempotent |
| `GET /api/trainer/learners/{id}/engagement` | practice frequency/score |
| `GET /api/trainer/learners/{id}/skill-development` | improvement trend |
| `GET /api/trainer/learners/{id}/assessment-analytics` | score + letter breakdown |
| `GET /api/trainer/learners/{id}/certification-status` | pass/level or not_attempted |

Role `Accessibility Trainer` added to the role system; `trainer_learner_links`
table; metric payloads marked `formula_owner: Intern 4 (pending)`.
Tests: `test_trainer.py`, trainer coverage in `test_input_validation.py`,
`test_full_api_pass.py`.

### 1.2 Security + performance pass (Day 4)
- **Critical fix:** admin delete/bulk endpoints previously skipped admin
  verification when `admin_email` was omitted → now required (422) + always
  verified.
- **`is_active` enforced at login** (403 for deactivated accounts).
- **Login now reads role/status from the DB** (not the stale in-memory snapshot),
  so admin role changes take effect on the next login (Day 7 bug fix, see §5).
- `reject_malicious` added to trainer/instructor/admin identifier+email fields;
  duplicate-username ✓ 400 (was an unhandled 500); SQLite numeric-UUID crash
  fixed (`String(36)` columns); error messages made generic (no internals leaked);
  FK indexes added; duplicate JWT-secret now warns at startup.
- **Performance:** 46-endpoint sweep — all <3 ms except bcrypt auth (~170 ms)
  and the live AI relay (`/api/practice/submit` ~39 ms). No slow endpoints.

### 1.3 Docker / production readiness (Day 5)
- `Dockerfile.backend` pinned to `python:3.11.9-slim`; production uvicorn
  (`0.0.0.0`, `$PORT`, `$WEB_CONCURRENCY` workers, `--proxy-headers`, **no
  --reload**); deps already include slowapi/sqlalchemy/reportlab/psycopg2-binary.
- `docker-compose.yml` wires env vars and persists Postgres on `signlang_pgdata`.
- `Backend/.env.production.example` template; `.gitignore` keeps
  `.env.production` out while tracking the example; `.dockerignore` keeps
  secrets/pycache/DBs out of the image.
- **Image verified live:** `docker build -f Dockerfile.backend -t
  signlang-backend-prod .` builds, container `/health` answers 200, no `.env`
  or dev files inside the image.

### 1.4 Deployment status (Day 6–7)
- **Chosen free platform: Render** (per SRS zero-cost rule). `render.yaml`
  blueprint at repo root: `signlang-backend` (Docker, free plan,
  `/health`) + free Postgres `signlang-db` with `DATABASE_URL` auto-wired, plus
  an optional `signlang-ai` service.
- `Backend/docs/deployment_guide.md` — complete step-by-step (Blueprint +
  manual web service), full env-var table, and the frontend connectivity/CORS
  plan for Intern 1.
- **Status: `READY FOR MANUAL DEPLOY`.** No hosting credentials existed in this
  environment, so the Render account flow is left to a human (a few clicks).
  Permanent live URL placeholder: `<LIVE_BACKEND_URL>`.
- **Live verification WAS run**: the Docker image was exposed via a temporary
  Cloudflare quick tunnel at
  `https://demonstrates-philip-connecticut-mobiles.trycloudflare.com`
  (verified reachable, `/health` 200, CORS reflected) and both live test suites
  passed against it.

## 2. Final test results (Day 7)

| Suite | Command | Result |
| :--- | :--- | :--- |
| Full backend suite | `python3 -m pytest Backend/ -v` | **129 passed** |
| Live smoke (Docker container, HTTPS) | `BACKEND_BASE_URL=<live> python3 -m pytest test_smoke_live.py -q` | **2 passed** |
| Team walkthrough (Docker container, HTTPS) | `BACKEND_BASE_URL=<live> python3 -m pytest test_acceptance_walkthrough.py -q` | **1 passed** |
| Live smoke (local server) | same, `http://127.0.0.1:8000` | 2 passed |
| Team walkthrough (local server) | same | 1 passed |

`test_smoke_live.py` = health + register + login + protected route.
`test_acceptance_walkthrough.py` = full four-role walkthrough (see §3).
Both are `@pytest.mark.integration` and fall back to in-process `TestClient`
when `BACKEND_BASE_URL` is unset, so the normal suite needs no live server.

## 3. Full team walkthrough (Day 7) — how it went

One end-to-end journey, exactly as the four interns would exercise the platform:

- **Learner:** register, login, learner dashboard (200), lessons list, practice
  start (200) + end (200), notification create/list/mark-read, and RBAC reject
  on the instructor dashboard (403).
- **Instructor:** register, login, instructor dashboard (200), create custom
  lesson (201), assign the learner as a student, list students (shows learner).
- **Accessibility Trainer:** register, login, assign the learner, list assigned
  learners, then read **all four** per-learner metric endpoints (200), and get
  **403 for a learner that is not assigned** to them.
- **Admin:** register, login, list all users, **deactivate a user → their login
  is blocked (403) → reactivate → login works again**, promote a Learner to
  Instructor and confirm the promoted account then creates lessons (201) and is
  listed as `Instructor`.

This is codified in `Backend/test_acceptance_walkthrough.py` and can be re-run
against the live platform by the whole team in one command once deployed:

```bash
BACKEND_BASE_URL=https://<LIVE_BACKEND_URL> python3 -m pytest Backend/test_smoke_live.py Backend/test_acceptance_walkthrough.py -q
```

## 4. Swagger / OpenAPI (finalised)

- **54 operations**, 16 tags, **61 component schemas** — audited against the
  live `/openapi.json`: every operation has a clear summary and a proper tag
  (no `default`, no missing summaries). Every router is present and grouped:
  Authentication, Admin Management, Instructor-Student Management,
  **Accessibility Trainer**, Lessons, Course, Practice, Notifications, System,
  plus the legacy v1 tags.
- Live UI: `http://127.0.0.1:8000/docs`. Reference doc:
  `Backend/docs/api_reference.md` (updated through Day 3).

## 5. Known remaining issues (non-blocking)

1. **Role escalation at signup** (High, deliberate): `register` accepts
   `Admin` / `Accessibility Trainer` as a role. Kept for the demo/tests;
   **must** be restricted to a setup list in production.
2. **`change-password` stores plaintext** (`users.password_hash`). Pre-existing
   design; bcrypt is used at register/login.
3. **JWT is stateless**: deactivating a user blocks *new* logins, but already
   issued tokens stay valid until expiry.
4. **CORS defaults to `*`** until the deployed frontend origin is set via
   `ALLOWED_ORIGINS`.
5. **Free-tier limits:** Render web sleeps after ~15 min (cold start), free
   Postgres expires after 30 days, and the slowapi limiter is in-memory per
   worker (not global across replicas).
6. **Trainer metric formulas** are Intern-4 placeholders (field
   `formula_owner`) — API shape is final, numbers may change.
7. **AI service not deployed yet**: `/api/practice/submit` and gesture
   endpoints need `AI_SERVICE_URL` to point at a deployed `Dockerfile.ai`
   service. All other endpoints work without it.
8. **Day 7 fix applied:** the Docker image no longer overlays
   `BD_Logic/app/routers|services` (its old `practice` stub used `/practice/*`
   and dropped `/submit`, clobbering the frozen API). The image now ships the
   canonical `Backend/app` + the `DATABASE_URL` db layer, so container == local.

## 6. AI model / dataset ground rule — confirmed

**No AI models, datasets, or ML code were changed this milestone.**
All work was confined to API/backend code, tests, docs, deployment config, and
dependency lists. `AIML_CV/` (the AI service) was not modified; no model weights,
datasets, or training scripts were touched, per the SRS ground rule.