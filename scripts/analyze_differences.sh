#!/bin/bash
# Analyze the difference between original and refreshed dumps
# Usage: ./scripts/analyze_differences.sh

set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-gkrp-pg}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

echo "=== Original Dump Analysis ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d backup_check_db -c "
-- Row counts
SELECT 'tbllayers' as tbl, COUNT(*) FROM public.tbllayers
UNION ALL
SELECT 'tblfragments', COUNT(*) FROM public.tblfragments
UNION ALL
SELECT 'tblornaments', COUNT(*) FROM public.tblornaments
UNION ALL
SELECT 'tblfinds', COUNT(*) FROM public.tblfinds;
"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d backup_check_db -c "
-- Layers with fragments
SELECT COUNT(DISTINCT f.locationid) as layers_with_frags FROM tblfragments f;
"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d backup_check_db -c "
-- Locationid sign distribution
SELECT 
  CASE WHEN locationid > 0 THEN 'positive' ELSE 'negative' END as sign,
  COUNT(*) as cnt,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
FROM tblfragments
GROUP BY sign;
"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d backup_check_db -c "
-- Site distribution (top 5)
SELECT l.site, COUNT(f.fragmentid) as frags, COUNT(DISTINCT l.layerid) as layers
FROM tbllayers l
INNER JOIN tblfragments f ON l.layerid = f.locationid
GROUP BY l.site
ORDER BY frags DESC
LIMIT 5;
"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${PG_CONTAINER}" \
  psql -U "${POSTGRES_USER}" -d backup_check_db -c "
-- Site name variations for Глухите
SELECT site, COUNT(DISTINCT layerid) as layers, COUNT(*) as frags
FROM tbllayers l
INNER JOIN tblfragments f ON l.layerid = f.locationid
WHERE l.site ILIKE '%глухите%'
GROUP BY site;
"

echo "=== Done ==="
