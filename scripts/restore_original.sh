#!/bin/bash
# Restore original dump to backup_check_db for analysis
# Usage: ./scripts/restore_original.sh

set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-gkrp-pg}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

echo "=== Step 1: Drop and create backup_check_db ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS backup_check_db;"
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE backup_check_db;"

echo "=== Step 2: Restore original dump ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  pg_restore -U "${POSTGRES_USER}" -d backup_check_db --clean --if-exists --no-owner --no-privileges /tmp/Pottery_backup_260118.sql

echo "=== Step 3: Verify row counts ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d backup_check_db -c "
SELECT 'tbllayers' as tbl, COUNT(*) FROM public.tbllayers
UNION ALL
SELECT 'tblfragments', COUNT(*) FROM public.tblfragments
UNION ALL
SELECT 'tblornaments', COUNT(*) FROM public.tblornaments;
"

echo "Done."
