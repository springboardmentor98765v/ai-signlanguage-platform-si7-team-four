# Deployment Readiness Checklist

FOR MILESTONE 4 USE — PLANNING DOCUMENT ONLY
No deployment is performed in Milestone 3. This document lists what needs to happen before the platform goes live.

Prepared by: Intern 5 — Database & QA Engineer
Date: Milestone 3, Day 9

---

## 1. Carried-over blocker from Milestone 2 (must resolve first)

- [ ] Render/Railway GitHub access. As of M2 Day 5, the repo is private under the mentor's GitHub org and Render's GitHub App had no access. A formal request was sent to the mentor; no response received by end of M2. This must be resolved before any Milestone 4 deployment work can begin — either the mentor grants GitHub App access, or sets up the Render service directly and adds the team as collaborators. Recommend re-raising this at the very start of Milestone 4, not waiting.
- [ ] Alternative hosting fallback: if Render/Railway access is still blocked, revisit Fly.io (CLI-based, no GitHub App permission needed) as a workaround. Rejected in M2 for not auto-redeploying on push, but may be acceptable as a stopgap if the access issue drags on.

---

## 2. Known code issues to fix before going live

These were found during Milestone 3 local testing and should be resolved before deployment, since they would affect real users immediately:

- [ ] /practice/start is broken. practice_service.start_session() has a 0-argument signature but is called with 2 arguments (user_id, lesson_id). Every practice session start fails. (Found Day 6, flagged to Intern 2.)
- [ ] Duplicate route in practice.py. @router.post("/start") is defined twice; the second silently overrides the first. Needs cleanup regardless of the bug above.
- [ ] Course/module creation breaks the catalog for all users. POST /courses/modules stores a module without a module_id key; the very next GET /courses/modules call then throws a KeyError for every user until the server restarts. High severity — found Day 6, flagged to Intern 2, root cause documented in DAY6_FINDINGS.md.
- [ ] Course/module data is mock, not real. course.router runs entirely on an in-memory MOCK_MODULE_DB/MOCK_LESSON_DB, not the real courses/modules/lessons tables in Postgres, despite those tables existing since Milestone 1. Any content added via the API is lost on every server restart — not acceptable for a live deployment.
- [ ] 8 router files exist but are never wired into main.py: assessment.py, certificate.py, recommendation.py, instructor_router.py, admin_router.py, analytics.py, lessons.py, report.py. Confirm intentionally deferred vs. accidentally missed before launch — several of these correspond to real M2 tables (certificates, recommendations, instructor_student) that are currently unreachable via the API.
- [ ] Duplicate models.py files. Backend/app/models/models.py (used by all live routers) is out of sync with Database_Devops/app/db/models.py (source of truth, has all 15 tables including Milestone 3's Notifications/Badges/Streaks). Needs a decision: merge into one file, or have all routers import from the up-to-date path. This is actively getting riskier as more tables are added each milestone.

---

## 3. Environment & secrets

- [ ] .env currently has a placeholder JWT_SECRET (your_super_secret_jwt_key_here) — must be replaced with a real, randomly generated secret before going live. Never reuse the dev placeholder in production.
- [ ] .env is technically tracked in git (committed once before .gitignore was updated to exclude it — see commit 885c1b6). Decide whether to fully untrack it (git rm --cached .env) before deployment, so no team member's local secrets accidentally leak through git history.
- [ ] Confirm DATABASE_URL in production points to the correct host — note from M3 Day 6: inside Docker Compose, the host must be the service name (postgres), not localhost; production will need its own correct value depending on final hosting choice.
- [ ] EMAIL_HOST / EMAIL_APP_PASSWORD are currently placeholders in docker-compose.yml — needed if email features (password reset, notifications-by-email) are planned; confirm scope before launch.
- [ ] Decide on production ACCESS_TOKEN_EXPIRE_MINUTES — currently 30, fine for dev, worth a deliberate decision for production security/UX tradeoff.


---

## 4. Database

- [ ] Neon (Postgres 18, Singapore region) is already set up and working — confirmed compatible for production use, no changes needed here structurally.
- [ ] Final backup schedule: backup.sh exists and is tested (M2 + re-verified M3 Day 5), but currently must be run manually. Decide on an automated schedule for production (e.g. daily cron job, or Neon's built-in backup/point-in-time-recovery features if on a paid tier — confirm what's available on Neon's free tier specifically).
- [ ] Confirm Neon's free-tier limits (storage, compute hours, connection limits) are sufficient for expected real usage — was fine for milestone testing with 2 test users, unverified at real scale.
- [ ] All 15 tables (11 original + Notifications/Badges/UserBadges/Streaks from M3) are indexed appropriately as of Day 3 — no further action needed unless new tables are added in M4.
- [ ] Known local-vs-Neon quirk: local Postgres is v16, tools upgraded to v18 for Neon compatibility, causing a harmless transaction_timeout warning on local-to-local restores (documented in RESTORE.md). Not a production concern, just a note for anyone restoring locally.

---

## 5. Security

- [ ] OWASP ZAP baseline scan (M3 Day 7) found 0 critical/high issues. 3 low-severity header warnings remain open (X-Content-Type-Options, Cache-Control, Cross-Origin-Resource-Policy) — cheap fixes, should be applied before going live.
- [ ] M3 Day 7's scan only covered 3 URLs due to ZAP's baseline scan not suiting a JSON API well. Before real deployment, run a more thorough scan against the actual API surface (e.g. via the OpenAPI/Swagger spec) to properly test authenticated endpoints, not just the root path.
- [ ] Confirm per-user rate limiting (an Intern 2 M3 Day 6 task) is actually in place before launch, not just for login but for other sensitive actions.
- [ ] Confirm input validation hardening (Intern 2, M3 Day 5) covers all public-facing endpoints, not just the ones tested so far.
- [ ] Rotate/replace any placeholder secrets (see Section 3) before deployment — this is a security item as much as a config item.

---

## 6. Testing coverage before launch

- [ ] Local integration tests exist for Auth journey (9/9 passing) and Course Catalog journey (6/7 — the 1 failure is the real bug in Section 2, not a test problem). Both should be re-run and passing 100% before deployment, meaning the course/module bug must be fixed first.
- [ ] No integration test currently exists for the Practice/Assessment journey, since /practice/start is broken. Add one once that's fixed.
- [ ] Confirm Intern 2's automated unit/integration test suite (pytest, M3 Days 7-8) is passing in full before launch.
- [ ] Confirm accessibility checks (Intern 1, M3 Day 6) and full cross-browser testing (Intern 1, M3 Day 9) are complete.

---

## 7. Monitoring & operations (deferred to M4, not started yet)

- [ ] UptimeRobot (or similar free monitoring) setup was blocked in M2 pending a live URL — revisit once Render/hosting access is resolved.
- [ ] No live error-tracking/logging service currently configured — worth deciding on a free option (e.g. Sentry free tier) before launch, so bugs like the ones found this milestone are caught automatically in production rather than only through manual testing.
- [ ] Decide on a deployment rollback plan — what happens if a bad deploy breaks production? Currently no documented process for this.

---

## 8. Process notes for Milestone 4

- [ ] Re-confirm with the whole team at the start of M4: who is unblocking the Render/GitHub access issue, and by when — this stalled for the second half of M2 without resolution and shouldn't be allowed to repeat.
- [ ] This checklist should be reviewed together as a team (per Day 9's checkpoint) before Milestone 4 planning begins, so nothing here is a surprise once deployment work actually starts.

---

Status: This is a planning document only. No live/public deployment has been performed as part of Milestone 3, consistent with the SRS's explicit scope for this milestone.
