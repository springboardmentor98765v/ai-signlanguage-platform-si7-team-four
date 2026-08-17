# Security Scan — AI Sign Language Platform (Milestone 4, Day 4)

Intern 2 (Backend) security re-check of the running API at
`http://127.0.0.1:8000` on **Day 4 of Milestone 4**. Full test suite at the end of
this pass: **126 tests green** (`python3 -m pytest -q`).

## Method

An automated scanner (ZAP / nikto / nuclei / wpscan / sqlmap / bandit / sslyze)
was **not installed** on this machine and no Docker is available, so a **manual
offline security audit** was performed instead:

1. **Input validation sweep** of every request body/query against a malicious
   payload corpus (SQL injection, `<script>`/XSS, oversized/typed values) —
   extended `Backend/test_input_validation.py` (+20 security tests) and drove the
   live server directly.
2. **Auth & authorization review** — token handling, role checks, the `admin_email`
   query-param auth pattern, account `is_active` enforcement, refresh-token flow.
3. **Error & information-disclosure review** — response bodies for internals,
   stack traces, and verbose exception messages.
4. **Datastore review** — SQLAlchemy model types vs SQLite affinity behavior,
   unique constraints, missing indexes.
5. **Response-time sweep** of every endpoint (see Performance).
6. **Recommended follow-up**: run OWASP **ZAP (zap-cli)** or Dalfox/nuclei against
   `/api/*` in CI for the next milestone since no scanner binary is available here.

## Findings

| # | Severity | Area | Finding | Status |
|---|----------|------|---------|--------|
| 1 | **Critical** (fixed) | Admin auth bypass | `DELETE /api/admin/users/{id}`, `bulk-delete`, `bulk-status`, `bulk-roles` only verified the caller when `admin_email` was supplied; the param was `Optional`, so the request succeeded with **no admin verification at all**. | `admin_email` is now **required** (`422` when missing) and `verify_admin` always runs. Regression-tested. |
| 2 | High | Registration role escalation | `POST /api/auth/register` accepts role `Admin` / `Accessibility Trainer`, so any user can self-register as an admin. | **Documented only** (kept deliberately: integration tests + demo flows require it). Must be restricted to a setup list in production. |
| 3 | Medium | Password storage | `change-password` stores the new password in **plaintext** in `users.password_hash`. | **Documented only** — pre-existing design; bcrypt is used at registration/login but the change endpoint does not hash. |
| 4 | Medium | Account deactivation | Deactivated accounts could still log in (`is_active` was never checked). | `is_active == False` now blocks login with `403` "This account has been deactivated." Limitation: already-issued JWTs stay valid until expiry (stateless design). |
| 5 | Medium | Error disclosure | `gesture_router` (500), `auth` refresh-token (401), `practice` AI-relay (502) returned raw exception strings (`str(e)`) that could leak internals. | Replaced with generic messages; details now logged server-side in each router. |
| 6 | Medium | Secrets | `JWT_SECRET` falls back to a hardcoded dev key when `SECRET_KEY`/`JWT_SECRET` env vars are absent. | Startup warning added (`app/utils/security.py`); `.env` present here. Set `SECRET_KEY` in any deployment. |
| 7 | Medium | Duplicate-username 500 | Registering with a duplicate `username` hit the SQLite `UNIQUE` constraint and returned an unhandled `500`. | Pre-check added → `400` "Username is already taken." Regression-tested. |
| 8 | Medium | Input validation gaps | `AssignLearnerRequest` (trainer), `AssignStudentRequest` (instructor), and admin `target_email` fields lacked the `reject_malicious` guard. | `reject_malicious` added to every identifier/email field in trainer/instructor/admin routers. |
| 9 | Low | CORS | `allow_origins=["*"]` with `allow_credentials=True`. | **Documented only** — kept for the single-origin demo frontend; restrict in production. |
| 10 | Low | Security headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block` all present (verified live). | OK — no change needed. |
| 11 | Bug (fixed) | SQLite numeric-UUID crash | Some UUID strings are digit-only (e.g. `11111111-1111-1111-1111-111111111111`); SQLite **NUMERIC affinity** stored them as floats and reads crashed (`AttributeError: 'float' object has no attribute 'replace'` → 500). Hit on `/api/practice/start`. | `PracticeSession` + `Assessment` ID/user/lesson/session columns changed UUID→`String(36)`; start/end now works. Indexes added for the new FK columns. |

## Auth & authorization pass (notes)

- Bearer JWT enforced via `HTTPBearer`; missing/invalid token → `401`, wrong role → `403`.
- Admin endpoints deliberately use the `admin_email` query param (documented pattern); the critical gap that let the param be bypassed is fixed (finding #1).
- Trainer/instructor `assign-*` endpoints: unauthenticated → `401`, Learner-role caller → `403`, self-assignment and non-Learner targets rejected (covered by tests).
- Login rate limit (5/min/email) verified; register/forgot-password share the limiter.

## Performance

Response times were measured live for **46 endpoint calls** (`/tmp/timing_m4_day4.py`):

- Every endpoint answered in **< 3 ms** median except:
  - `POST /api/auth/register` and `POST /api/auth/login` — **≈170 ms** (bcrypt hashing, expected).
  - `POST /api/practice/submit` — **39 ms** (real relay to the AI service at `127.0.0.1:8001`).
- **No slow, O(n²), or N+1 patterns found** among list/dashboard queries.
- Indexes added defensively (finding #11 list) on `practice_sessions`, `assessments`, and `trainer_learner_links` FK columns.

## Fixes applied this pass

- `app/routers/admin_router.py` — required `admin_email` + `verify_admin` on delete/bulk endpoints; `reject_malicious` on `target_email`.
- `app/routers/auth.py` — `is_active` enforced at login (`403`); generic refresh-token error (logged); duplicate-`username` pre-check (`400`).
- `app/routers/gesture_router.py` / `app/routers/practice.py` — generic 500/502 detail + server-side logging.
- `app/routers/trainer_router.py` / `app/routers/instructor_router.py` — `reject_malicious` on assign request fields.
- `app/models/models.py` — `PracticeSession`/`Assessment` UUID→`String(36)`; FK indexes.
- `app/utils/security.py` — startup warning when the fallback JWT secret is in use.

## Regression coverage added

- `test_input_validation.py`: trainer assign (malicious/SQL/self/non-Learner/token), admin malicious `target_email`, admin bulk without `admin_email` → `422`, non-admin `admin_email` → `403`, deactivated-user login → `403`, duplicate username → `400`.
- `test_full_api_pass.py`: `test_practice_numeric_looking_lesson_id_is_stable`.
- `test_milestone3_day1.py`: bulk-admin flow now passes `admin_email` and asserts the missing-param `422`.