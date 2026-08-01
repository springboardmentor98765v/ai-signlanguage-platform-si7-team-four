# How to Restore a Database Backup

Backups live in `backups/` and are created by running `./backup.sh`.
Each file is named `backup_neon_<timestamp>.dump` or `backup_local_<timestamp>.dump`.

## Important — PostgreSQL version match

Our Neon database runs PostgreSQL 18. Your local `pg_dump`/`pg_restore` must be
version 18 or newer, or restoring a Neon backup will fail with a version
mismatch error.

Check your version:
    pg_restore --version

If it's older than 18, use the full path to the v18 binary instead:
    /usr/lib/postgresql/18/bin/pg_restore

## Restoring into an EXISTING database (real recovery scenario)

This replaces whatever is currently in the target database.

    pg_restore --clean --no-owner -h <host> -U <user> -d <dbname> backups/backup_neon_<timestamp>.dump

You will see some harmless errors about roles like "neon_superuser" not
existing if restoring onto a non-Neon Postgres instance — these are safe to
ignore, they only affect a permissions grant, not your data.

## Restoring into a NEW/empty database (safe way to test a backup)

    # Create a fresh empty database first
    psql -h <host> -U <user> -d postgres -c "CREATE DATABASE <new_db_name>;"

    # Restore without --clean, since there's nothing to clean out
    pg_restore --no-owner -h <host> -U <user> -d <new_db_name> backups/backup_neon_<timestamp>.dump

    # Verify all tables came back
    psql -h <host> -U <user> -d <new_db_name> -c "\dt"

## Verified

This restore process was tested on 2026-07-23:
- Backup taken from live Neon database (11 tables)
- Restored successfully into a disposable local test database
- All 11 tables confirmed present after restore


## Known issue: unrecognized configuration parameter transaction_timeout (found M3 Day 5)

If you restore a locally-taken backup (not Neon) into local Docker Postgres, you may see:

    pg_restore: error: could not execute query: ERROR:  unrecognized configuration parameter "transaction_timeout"
    Command was: SET transaction_timeout = 0;
    pg_restore: warning: errors ignored on restore: 1

This is safe to ignore. Cause: our local pg_dump/pg_restore binaries were upgraded to
v18 (for Neon compatibility, per M2 Day 4), but our local Docker Postgres container is
still v16. v18's pg_dump writes a SET transaction_timeout = 0; statement (a v17+ feature)
into every dump file it creates, which v16 does not recognize during restore.

pg_restore reports this as "1 error ignored" but continues and completes the restore
normally - all tables and data come through intact. Verified 2026-08-01 by restoring a
15-table local backup into a disposable test database; all tables and row counts matched
the source exactly.

If this ever becomes a real problem, the fix would be either upgrading the local Docker
Postgres image to v18 as well, or downgrading pg_dump/pg_restore for local-only backups.
Not necessary today.

## Verified - Milestone 3 Day 5

Re-tested with the larger, 15-table Milestone 3 database (11 original plus notifications,
badges, user_badges, streaks):
- Backup taken from local Docker Postgres: backup_local_20260801_141609.dump (27149 bytes)
- Restored into a disposable local database (signlang_test_restore)
- All 15 tables confirmed present after restore
- Row counts verified matching source: users (2), instructor_student (1)
- One cosmetic transaction_timeout warning encountered and documented above - does not
  affect restore success or data integrity
