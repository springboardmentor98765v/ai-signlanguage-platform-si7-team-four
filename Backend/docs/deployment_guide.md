# Deployment Guide — Backend (Milestone 4, Day 6)

Deploy the FastAPI backend to the **free tier** of a hosting platform per the
SRS zero-cost rule. **Primary platform: Render** (blueprint-first). Railway and
Fly.io one-liners are given as alternatives.

- **Status:** `READY FOR MANUAL DEPLOY` — no hosting credentials were available
  in this sandbox (no `render`/`railway`/`flyctl` CLIs, no API tokens), so the
  click-through deploy was NOT performed here. Everything below is prepared so a
  human can deploy in a few clicks, and a **temporary live URL** was verified
  during this pass (see section 6).
- **Permanent live URL:** `<LIVE_BACKEND_URL>` (set after the Render deploy).

---

## 1. What was verified in this repo

- App is **env-driven** — no hardcoded production config:
  - `DATABASE_URL` — `Database_Devops/app/db/database.py`
  - `SECRET_KEY` / `JWT_SECRET` / `ACCESS_TOKEN_EXPIRE_MINUTES` — `utils/security.py`, `routers/auth.py`, `main.py`
  - `ALLOWED_ORIGINS` — `Backend/app/main.py` (comma-separated CORS list, default `*`)
  - `AI_SERVICE_URL` — `routers/practice.py`
  - `PORT` / `WEB_CONCURRENCY` — `Dockerfile.backend` CMD (`uvicorn ... --port ${PORT} --workers ${WEB_CONCURRENCY} --proxy-headers`, no `--reload`)
- Docker image builds and runs: `docker build -f Dockerfile.backend -t signlang-backend-prod .`
  → `/health` answered **200** from inside the container (verified live, Day 5).
- Health endpoint: `GET /health` → `{"status":"healthy", ...}` (Render `healthCheckPath`).
- Blueprint: [`render.yaml`](../../render.yaml) defines the free Postgres DB +
  backend service and wires `DATABASE_URL` automatically.

## 2. Prerequisites

- A GitHub repo containing this project (already at
  `github.com/springboardmentor98765v/ai-signlanguage-platform-si7-team-four`).
- A free [Render](https://render.com) account (sign in with GitHub).
- Optional: a free hosted Postgres if you do **not** want Render's bundled DB
  (Render free DB expires after **30 days**; Neon / Supabase free tiers are
  drop-in replacements — the app only needs `DATABASE_URL`).

## 3. Environment variables (match `Backend/.env.production.example`)

Set these on the hosting platform (Render dashboard: *Environment*).

| Variable | Required | Example / notes |
| :--- | :--- | :--- |
| `DATABASE_URL` | yes | `postgresql+psycopg2://user:pass@host:5432/db` — auto-wired by `render.yaml`; for Neon/Supabase paste their connection string |
| `SECRET_KEY` | yes | long random string, e.g. `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_SECRET` | no (falls back to `SECRET_KEY`) | same as above |
| `ALLOWED_ORIGINS` | yes | comma-separated browser origins, e.g. `https://signlang-frontend.onrender.com` (use `*` only during bring-up) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | default `30` |
| `AI_SERVICE_URL` | no* | URL of the deployed AI service, e.g. `https://signlang-ai.onrender.com` (*needed for `/api/practice/submit` + gesture endpoints) |
| `WEB_CONCURRENCY` | no | `1` on the free 512 MB instance (default image value is `4`) |
| `PORT` | no | Render injects `PORT` automatically; the Dockerfile CMD honours it |
| `EMAIL_HOST` / `EMAIL_APP_PASSWORD` / `EMAIL_SENDER` | no | only for forgot-password email |
| `PDF_OUTPUT_DIR` | no | e.g. `/tmp/certificates` (writable) |

Secrets (`SECRET_KEY`, `JWT_SECRET`, `EMAIL_APP_PASSWORD`) are marked
`sync: false` in `render.yaml`, so they are entered in the dashboard and never
stored in the repo.

## 4. Deploy on Render (primary — few clicks)

**Option A — Blueprint (recommended):**
1. Push this repo to GitHub.
2. Render dashboard → **New → Blueprint** → select the repo.
3. Render detects `render.yaml` → **Apply**.
4. Render creates the free Postgres (`signlang-db`) + web service
   (`signlang-backend`) and fills `DATABASE_URL` for you.
5. Open the service → **Environment** → set `SECRET_KEY`, `JWT_SECRET`, and
   `ALLOWED_ORIGINS` (see section 7 for the frontend value).
6. Deploy completes automatically; click the service URL →
   `<LIVE_BACKEND_URL>/health`.

**Option B — Manual web service:**
1. **New → Web Service** → connect the repo.
2. Runtime **Docker**, root dir `.`, Dockerfile `Dockerfile.backend`.
3. `Health Check Path` → `/health`, plan **Free**.
4. Add a free Postgres (**New → PostgreSQL**) and copy its
   *Internal Connection String* into `DATABASE_URL`.
5. Add the remaining env vars from the table above.
6. **Create Web Service** and wait for the deploy → `Deploy successful`.

**After first boot:** tables are created automatically
(`Base.metadata.create_all` runs at startup). Optional seed data:
`python3 Backend/seed_data.py` via the Render **Shell** tab.

## 5. Deploy on Railway / Fly.io (alternatives)

- **Railway:** `railway init` → `railway up` (Dockerfile auto-detected) → set the
  same env vars in the dashboard → `railway domain` to get a URL. Add a Railway
  Postgres and point `DATABASE_URL` at it.
- **Fly.io:** `fly launch` → select `Dockerfile.backend` → `fly secrets set
  SECRET_KEY=... JWT_SECRET=... ALLOWED_ORIGINS=... DATABASE_URL=...` →
  `fly deploy`. `fly postgres create` for the DB. (Note: Fly free allowance may
  require a payment card on file.)

## 6. Live verification performed here (temporary)

No Render/other credentials existed in this environment, so instead of an
account-based deploy we proved the same path end-to-end with a **temporary
Cloudflare quick tunnel** in front of the Docker image:

- Container `signlang-backend-prod` (built from `Dockerfile.backend`) run with
  `DATABASE_URL=sqlite:////tmp/m4test.db`.
- Exposed to the internet (Cloudflare quick tunnel, no account) at:
  `https://demonstrates-philip-connecticut-mobiles.trycloudflare.com` —
  **reachable live, verified 200 on `/health` + CORS header reflected; the
  tunnel is temporary and expires when the cloudflared process is stopped.**
- Smoke test passed against it: `BACKEND_BASE_URL=<that-url> python3 -m pytest
  test_smoke_live.py -q` → **2 passed** (health, register+login+protected).

Once the Render service is live, run the exact same one-liner against it:

```bash
BACKEND_BASE_URL=https://<LIVE_BACKEND_URL> python3 -m pytest Backend/test_smoke_live.py -q
```

This is the required "one-command verification" — the test file
(`Backend/test_smoke_live.py`) is marked `@pytest.mark.integration` and
exercises: `/health`, register (Learner), login, and one Bearer-JWT-protected
route (learner dashboard). Without `BACKEND_BASE_URL` it runs in-process against
`TestClient`, so the normal suite stays green.

## 7. Frontend connectivity plan (for Intern 1)

- **CORS / env var:** the backend reads `ALLOWED_ORIGINS` (comma-separated).
  After the frontend is deployed, set it to the frontend origin, e.g.
  `https://signlang-frontend.onrender.com` (Intern 1's deployed URL). The
  backend then answers the browser with the correct `Access-Control-Allow-Origin`
  header.
- **Base URL:** the frontend API client should point its base URL at
  `<LIVE_BACKEND_URL>` (e.g. `/api` calls go to
  `<LIVE_BACKEND_URL>/api/...`), replacing the current `http://127.0.0.1:8000`.
- **Auth:** frontend stores `access_token`/`refresh_token` from
  `POST /api/auth/login` and sends `Authorization: Bearer <token>`.
- **AI features:** practice/gesture calls go through the backend to
  `AI_SERVICE_URL`; deploy `Dockerfile.ai` (or point it at Intern 3's service).

## 8. Known limitations on free tier

- Render free web services **sleep after ~15 min idle** → first request after
  idle has a cold-start delay (~30–60 s). `curl` retries are fine.
- `WEB_CONCURRENCY=1` is used on the free 512 MB instance (multi-worker + bcrypt
  auth can spike memory).
- The slowapi rate limiter is **in-memory per worker** — with multiple replicas
  the per-email counters are not global. Acceptable for this milestone; move to
  Redis-backed limits if a paid tier is ever used.
- Render's free Postgres expires after 30 days — switch `DATABASE_URL` to Neon /
  Supabase before then.
