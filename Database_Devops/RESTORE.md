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
