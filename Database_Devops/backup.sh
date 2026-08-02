#!/bin/bash
set -e
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

if [ -z "$DATABASE_URL" ]; then
  echo "DATABASE_URL not set — backing up local Docker Postgres instead"
  OUTFILE="backups/backup_local_${TIMESTAMP}.dump"
  PGPASSWORD=signlang_dev_pw pg_dump -h localhost -p 5432 -U signlang -F c -f "$OUTFILE" signlang_db
else
  echo "Backing up Neon database..."
  OUTFILE="backups/backup_neon_${TIMESTAMP}.dump"
  /usr/lib/postgresql/18/bin/pg_dump "$DATABASE_URL" -F c -f "$OUTFILE"
fi

SIZE=$(stat -c%s "$OUTFILE" 2>/dev/null || stat -f%z "$OUTFILE")
if [ "$SIZE" -eq 0 ]; then
  echo "ERROR: Backup file is empty (0 bytes). pg_dump likely failed silently."
  echo "Run pg_dump manually to see the real error:"
  echo "  pg_dump \"\$DATABASE_URL\" -F c -f test.dump"
  rm -f "$OUTFILE"
  exit 1
fi

echo "Backup saved successfully: $OUTFILE ($SIZE bytes)"
