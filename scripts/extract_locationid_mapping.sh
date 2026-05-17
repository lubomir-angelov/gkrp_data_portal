#!/bin/bash
# Extract the fragmentid → locationid mapping from the original dump
# Usage: ./scripts/extract_locationid_mapping.sh
#
# Prerequisites: Original dump must be restored to backup_check_db
# Output: /tmp/locationid_mapping.csv (fragmentid,locationid pairs)

set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-gkrp-pg}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

echo "=== Extracting locationid mapping from original dump ==="

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d backup_check_db -c "
COPY (
  SELECT fragmentid || ',' || locationid
  FROM tblfragments
  WHERE locationid > 0
  ORDER BY fragmentid
) TO '/tmp/locationid_mapping.csv';
"

echo "=== Copying to host ==="
docker cp "${PG_CONTAINER}:/tmp/locationid_mapping.csv" /tmp/locationid_mapping.csv

echo "=== Verification ==="
wc -l /tmp/locationid_mapping.csv
head -3 /tmp/locationid_mapping.csv
echo "..."
tail -3 /tmp/locationid_mapping.csv

echo "Done. ${LINES} rows exported."
