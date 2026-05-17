#!/bin/bash
# Dump the fixed database as a new SQL dump file.
# This produces a clean, self-contained dump that can be used to restore
# as the new app_db.
#
# Usage: ./scripts/dump_fixed_db.sh [output_filename]
#
# Prerequisites:
#   1. Locationids have been restored (run restore_locationids.sh first)
#   2. Any other intentional cleanups have been applied
#
# Output: /tmp/Pottery_backup_fixed_YYYYMMDD.sql

set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-gkrp-pg}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
APP_DB="${APP_DB:-app_db}"

OUTPUT_FILE="${1:-/tmp/Pottery_backup_fixed_$(date +%Y%m%d).sql}"

echo "=== Dumping fixed database ==="
echo "Target DB: ${APP_DB}"
echo "Output file: ${OUTPUT_FILE}"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  pg_dump -U "${POSTGRES_USER}" -d "${APP_DB}" \
  --no-owner --no-privileges --no-password \
  -f /tmp/Pottery_backup_fixed_$(date +%Y%m%d).sql

docker cp "${PG_CONTAINER}:/tmp/Pottery_backup_fixed_$(date +%Y%m%d).sql" "${OUTPUT_FILE}"

echo ""
echo "=== Dump complete ==="
ls -lh "${OUTPUT_FILE}"
echo ""
echo "To restore as app_db:"
echo "  1. Drop the current app_db"
echo "  2. Create a new app_db"
echo "  3. Run: psql -U postgres -d app_db -f ${OUTPUT_FILE}"
echo "  4. Run: alembic stamp 0001_base_schema && alembic upgrade head"
