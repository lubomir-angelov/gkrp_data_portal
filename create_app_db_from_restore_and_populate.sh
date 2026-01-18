#!/bin/bash
set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-gkrp-pg}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
APP_DB="${APP_DB:-app_db}"
PG_HOST_PORT="${PG_HOST_PORT:-5433}"

# Path to dump inside container (Makefile docker cp copies it here)
DUMP_IN_CONTAINER="${DUMP_IN_CONTAINER:-/tmp/Pottery_backup_260118.dump}"

# Used by alembic
DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${PG_HOST_PORT}/${APP_DB}}"
export DATABASE_URL

echo "Using:"
echo "  PG_CONTAINER=$PG_CONTAINER"
echo "  APP_DB=$APP_DB"
echo "  DUMP_IN_CONTAINER=$DUMP_IN_CONTAINER"
echo "  DATABASE_URL=$DATABASE_URL"

# 1) Create DB fresh
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS ${APP_DB};"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${APP_DB};"

# 2) Restore dump
case "${DUMP_IN_CONTAINER}" in
  *.sql)
    docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
      psql -U "${POSTGRES_USER}" -d "${APP_DB}" -v ON_ERROR_STOP=1 -f "${DUMP_IN_CONTAINER}"
    ;;
  *)
    docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
      pg_restore -U "${POSTGRES_USER}" -d "${APP_DB}" --no-owner --no-privileges "${DUMP_IN_CONTAINER}"
    ;;
esac

# IMPORTANT: dump may include alembic_version from some other project/revisions
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -v ON_ERROR_STOP=1 -c "DROP TABLE IF EXISTS public.alembic_version;"

# 3) Stamp baseline (so Alembic will treat restored schema as baseline)
alembic stamp 0001_base_schema

# 4) Apply app migrations
alembic upgrade head

echo "Restore + migrations complete."
