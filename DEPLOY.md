# How to Run This Project

## Local Setup
1. Clone the repo
2. Copy Database_Devops/.env.example to Database_Devops/.env, fill in the
   shared Neon DATABASE_URL (ask Intern 5 / team password manager)
3. Run: docker compose up --build
4. Backend: http://localhost:8000 | AI service: http://localhost:8001

## Database
Shared Neon PostgreSQL — all services should point at the same
DATABASE_URL so data is genuinely shared across the team, not local.

## Known Issue
Backend/app/db/database.py currently hardcodes a local SQLite file and
ignores DATABASE_URL. This must be fixed for Backend to actually use
the shared Neon database. See Database_Devops/docs/day9_deployment_notes.md.

## Backups
Run Database_Devops/backup.sh to create a backup.
See Database_Devops/RESTORE.md to restore one.

## Monitoring
UptimeRobot dashboard — see team notes for link.
