#!/bin/bash
# Restore locationid values in the refreshed DB using the extracted mapping.
# This is the main fix: re-connects fragments to their correct layers.
#
# Usage: ./scripts/restore_locationids.sh
#
# Prerequisites:
#   1. Original dump restored to backup_check_db
#   2. Mapping extracted via extract_locationid_mapping.sh
#   3. Refreshed DB is the target (app_db)
#
# What it does:
#   1. Creates temporary table tmp_locationid_fix
#   2. Loads the CSV mapping into it
#   3. Runs UPDATE tblfragments SET locationid = ... FROM tmp_locationid_fix
#   4. Verifies the fix
#   5. Drops the temporary table

set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-gkrp-pg}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
APP_DB="${APP_DB:-app_db}"
MAPPING_FILE="${MAPPING_FILE:-/tmp/locationid_mapping.csv}"

echo "=== Restore locationid values ==="
echo "Mapping file: ${MAPPING_FILE}"
echo "Target DB: ${APP_DB}"

# Verify mapping file exists
if [ ! -f "${MAPPING_FILE}" ]; then
  echo "ERROR: Mapping file not found: ${MAPPING_FILE}"
  echo "Run extract_locationid_mapping.sh first."
  exit 1
fi

MAPPING_LINES=$(wc -l < "${MAPPING_FILE}")
echo "Mapping has ${MAPPING_LINES} rows."

# Step 1: Create regular table (not temporary — must persist across docker exec calls)
echo "Step 1: Creating table..."
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "
DROP TABLE IF EXISTS tmp_locationid_fix;
CREATE TABLE tmp_locationid_fix (
  fragmentid INTEGER,
  correct_locationid INTEGER
);
"

# Step 2: Copy mapping file into container, then load
echo "Step 2: Loading mapping data..."
docker cp "${MAPPING_FILE}" "${PG_CONTAINER}:/tmp/locationid_mapping.csv"
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "
COPY tmp_locationid_fix (fragmentid, correct_locationid)
FROM '/tmp/locationid_mapping.csv' WITH (FORMAT csv);
"

# Verify load
LOADED=$(docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -t -c "
SELECT COUNT(*) FROM tmp_locationid_fix;
" -t | tr -d ' ')
echo "Loaded ${LOADED} rows into table."

# Step 3: Run UPDATE (skip locationids that don't exist in tbllayers)
echo "Step 3: Running UPDATE..."
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "
UPDATE tblfragments f
SET locationid = t.correct_locationid
FROM tmp_locationid_fix t
WHERE f.fragmentid = t.fragmentid
  AND EXISTS (SELECT 1 FROM tbllayers l WHERE l.layerid = t.correct_locationid);
"

SKIPPED=$(docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -t -c "
SELECT COUNT(*) FROM tmp_locationid_fix t
WHERE NOT EXISTS (SELECT 1 FROM tbllayers l WHERE l.layerid = t.correct_locationid);
" -t | tr -d ' ')
echo "Skipped ${SKIPPED} fragments (locationid not in tbllayers)."

UPDATED=$(docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -t -c "
SELECT COUNT(*) FROM tblfragments WHERE locationid > 0;
" -t | tr -d ' ')
echo "Updated ${UPDATED} fragments to positive locationid."

# Step 4: Verify
echo ""
echo "=== Verification ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "
-- Locationid sign distribution after fix
SELECT 
  CASE WHEN locationid > 0 THEN 'positive' ELSE 'negative' END as sign,
  COUNT(*) as cnt,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
FROM tblfragments
GROUP BY sign;
"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "
-- Layers with fragments after fix
SELECT COUNT(DISTINCT f.locationid) as layers_with_frags
FROM tblfragments f;
"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "
-- Site distribution after fix (top 10)
SELECT l.site, COUNT(f.fragmentid) as frags, COUNT(DISTINCT l.layerid) as layers
FROM tbllayers l
INNER JOIN tblfragments f ON l.layerid = f.locationid
GROUP BY l.site
ORDER BY frags DESC
LIMIT 10;
"

# Step 5: Drop temporary table
echo "Step 5: Cleaning up..."
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d "${APP_DB}" -c "
DROP TABLE IF EXISTS tmp_locationid_fix;
"

echo ""
echo "=== Done ==="
echo "The locationid values have been restored."
echo "Layers with fragments should now match the original count."
