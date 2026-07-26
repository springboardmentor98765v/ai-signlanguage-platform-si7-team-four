# Day 9 — Deployment Notes

## Hosting Decision
Render/Railway blocked all sprint due to private repo + no GitHub App
access granted. Mentor confirmed local execution is acceptable for
evaluation. Fly.io was evaluated but requires payment info even on
trial (free tier removed in 2024) — not used, given team's no-paid-tools
rule.

## What's Live and Working
- Neon PostgreSQL: fully live, schema matches Database_Devops models,
  seeded with 26 alphabet lessons
- Local Docker Compose: postgres + backend + ai-service all build and
  run cleanly with one command
- Monitoring (UptimeRobot) and backup/restore both tested successfully

## Known Open Issue — NOT YET RESOLVED
Backend/app/db/database.py is hardcoded to a local SQLite file
(app_data.db) and does not read DATABASE_URL from environment at all.
This means Backend's actual API endpoints are not connected to the
shared Neon database — they run against an isolated local SQLite file.
Flagged to Intern 2. Required fix (one line):

    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app_data.db")

Until this is fixed, true end-to-end integration against the shared
database is not possible. This is the primary blocker for full Day 10
integration testing.
