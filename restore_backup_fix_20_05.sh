#!/bin/bash
set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-gkrp-pg}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
APP_DB="${APP_DB:-app_db}"
PG_HOST_PORT="${PG_HOST_PORT:-5433}"

BACKUP_FILE="${BACKUP_FILE:-/tmp/backup_fix_20_05_2026.sql}"
IMPORT_IN_CONTAINER="${IMPORT_IN_CONTAINER:-/tmp/backup_fix_20_05_2026_import.sql}"

DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${PG_HOST_PORT}/${APP_DB}}"
export DATABASE_URL

echo "=== Step 1: Copy backup into container ==="
docker cp "${BACKUP_FILE}" "${PG_CONTAINER}:${IMPORT_IN_CONTAINER}"

echo "=== Step 2: Drop and recreate app_db ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS ${APP_DB};"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${APP_DB};"

echo "=== Step 3: Restore dump (creates staging_* and finds tables) ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  pg_restore -U "${POSTGRES_USER}" -d "${APP_DB}" --no-owner --no-privileges --clean --if-exists "${IMPORT_IN_CONTAINER}"

echo "=== Step 4: Rename staging_* tables to original names ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -v ON_ERROR_STOP=1 <<'SQL'
ALTER TABLE public.staging_tblfragments RENAME TO tblfragments;
ALTER TABLE public.staging_tbllayerincludes RENAME TO tbllayerincludes;
ALTER TABLE public.staging_tbllayers RENAME TO tbllayers;
ALTER TABLE public.staging_tblornaments RENAME TO tblornaments;
ALTER TABLE public.staging_tblpok RENAME TO tblpok;
SQL

echo "=== Step 5: Drop alembic_version (backup may have stale version) ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -v ON_ERROR_STOP=1 -c "DROP TABLE IF EXISTS public.alembic_version;"

echo "=== Step 6: Verify tables ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "\dt public.*"

echo "=== Step 7: Stamp Alembic baseline ==="
VENV_ALEMBIC="${VENV_ALEMBIC:-/home/ubuntu/venvs/gkrp_data_portal/bin/alembic}"
"$VENV_ALEMBIC" stamp 0001_base_schema

echo "=== Step 8: Apply app migrations ==="
"$VENV_ALEMBIC" upgrade head

echo "=== Restore complete ==="
echo "Tables in app_db:"
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "\dt public.*"
