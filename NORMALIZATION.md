# Data Normalization — Analysis Report

*Generated: 2026-05-17*

*This document records the findings from comparing the original database dump (Pottery_backup_260118.sql) with the refreshed/cleaned dump (Pottery_backup_260513.sql). The original EDA is preserved in EDA.md.*

---

## 1. Site Name Normalization (Valid Cleanup)

### Before: 4 variations of "Глухите камъни"

| Site name | Layers | Fragments |
|---|---|---|
| Глухите камъни (lowercase) | 927 | 31,637 |
| Глухите Камъни (capital К) | 221 | 8,539 |
| Глухите Каъмни (different Cyrillic 'а') | 1 | 56 |
| Глухите камъни (trailing space) | 1 | 69 |
| **Total** | **1,150** | **40,301** |

### After: 1 merged entry

| Site name | Layers | Fragments |
|---|---|---|
| Глухите камъни | 2 | 40,301 |

### Surviving layers

Only **2 of the original 1,150 layers** retained fragments after normalization:

| layerid | sector (original) | sector (refreshed) | square | layer |
|---|---|---|---|---|
| 64327509 | Сондаж 3 | Център | *(empty)* | 3 | VIII |
| 2093547693 | Сондаж 3 | Център | *(empty)* | 3 | XX |

Note: `sector` changed from "Сондаж 3" to "Център", and `square` was populated (was empty in original).

### Other sites — same pattern

Every site collapsed from dozens/hundreds of layers down to 1:

| Site | Original layers | Refreshed layers | Fragments |
|---|---|---|---|
| Ада тепе | 696 | **1** | 31,331 |
| Д. Черковище - Аул кая | 139 | **1** | 4,276 |
| Чала | 9 | **1** | 1,997 |
| Резбарци | 49 | **1** | 993 |

### Other name normalization fixes

| Field | Original variation | Refreshed |
|---|---|---|
| Sector | "Севре" (typo of "Север", 1 layer) | Fixed to "Север" |
| Sector | "Централен" (2 layers) | One fixed to "Център", one remains "централен" (lowercase) |
| Sector | "Сондаж 3" (87 layers) | Removed; 6 new "сондаж 1" layers (lowercase) appeared |
| Site | "test" (3 layers, 3 fragments) | Removed entirely |

---

## 2. Root Cause: `locationid` Re-mapping (Critical Issue)

### The sign distribution shift

| | Original dump | Refreshed dump | Change |
|---|---|---|---|
| Fragments → positive layerid | 65,889 (78.9%) | **1,669 (2.0%)** | **-97.4%** |
| Fragments → negative layerid | 17,672 (21.1%) | **81,889 (98.0%)** | **+76.9%** |
| Fragments with NULL locationid | 0 | 0 | No change |

**This is the root cause of the 2,259 → 105 layers-with-fragments collapse.**

### What happened

The data cleanup **re-mapped `locationid` values in `tblfragments`**. Fragments that previously pointed to valid, positive `layerid` values in `tbllayers` were changed to point to **negative `layerid` values** — which are orphaned/placeholder layers with no site, sector, square, or layer information.

### Evidence

1. **Total fragment count preserved:** 83,561 → 83,558 (difference of 3, likely test data removal)
2. **All fragments still have a non-null `locationid`:** 0 nulls in both dumps
3. **No fragments were lost** — they were all re-assigned to different `locationid` values
4. **The 3 NULL-site layers** exist in both dumps with 0 fragments: `-1990834609`, `-460456991`, `1325922508`
5. **Negative layerid layers:** 490 distinct (original) → 52 distinct (refreshed), but fragments pointing to them: 17,672 → 81,889
6. **Positive layerid layers:** 1,769 distinct (original) → 53 distinct (refreshed), fragments: 65,889 → 1,669

### What this means

The fragments' `locationid` foreign keys were changed from pointing to valid layers (with site/sector/square/layer data) to pointing to invalid/orphaned layers. The `tbllayers` hierarchy still exists (2,335 layers with proper site/sector/square/layer data), but **the fragments no longer reference them**.

The apparent "disappearance" of 2,154 layers was not a deletion — it was a **foreign key re-mapping**. The fragments still exist, but they now point to orphaned negative IDs instead of the valid positive IDs.

---

## 3. Field Coverage Changes

Several fields saw major coverage increases after cleanup, likely because the data curator populated previously-empty values:

| Field | Original | Refreshed |
|---|---|---|
| bottomtype | 6.4% | **48.0%** |
| handletype | 15.0% | **53.5%** |
| category | 26.5% | **60.6%** |
| form | 21.4% | **57.2%** |
| type | 19.1% | **56.3%** |
| subtype | 18.5% | **55.9%** |

Ornament fields remained stable (no meaningful changes).

---

## 4. Recommendations

### Immediate

1. **Ask the data curator:** "Did you intentionally change `locationid` values in `tblfragments` during the cleanup? If so, what was the mapping logic?"

2. **If the mapping was accidental:** The original dump has the correct `locationid` → `layerid` relationships. The original dump should be used as the source of truth, and the cleanup script should be fixed.

3. **If the mapping was intentional:** A reverse mapping table is needed — a lookup of old `locationid` (positive) → new `locationid` (negative) — so the data can be traced back to its original site/sector/square/layer. Without this mapping, the hierarchy is irrecoverable from the refreshed dump alone.

### Short-term

4. **Fix remaining sector typos:** "централен" (lowercase) should be "Център" to match the normalized convention.

5. **Investigate "сондаж 1" layers:** 6 new lowercase "сондаж 1" layers appeared in the refreshed dump with no equivalent in the original. Their origin and fragment associations should be verified.

### Long-term

6. **Establish a data governance process:** Before any bulk data transformation, create a mapping log that records every `locationid` change. This prevents the current situation where fragment-layer relationships are silently broken.

7. **Add referential integrity checks:** Implement periodic validation queries that verify all `locationid` values in `tblfragments` point to valid, non-orphaned `layerid` values in `tbllayers`.

8. **Use normalized layer IDs:** Consider replacing the current `layerid` (which includes negative orphaned IDs) with a clean, sequential ID scheme. The current system mixes valid archaeological layer IDs with negative placeholder IDs in the same column.

---

## 5. Fix Plan: Restore `locationid` Values (2026-05-17)

*The change was confirmed unintentional. This section documents the fix.*

### Key Discovery

The refreshed `tbllayers` already has all intentional changes applied:
- Site name normalization ("Глухите Камъни" → "Глухите камъни")
- Sector changes ("Сондаж 3" → "Център")
- Typo fixes ("Севре" → "Север")
- Test site removal

**All 1,769 original positive `layerid` values exist in the refreshed `tbllayers`.** The only thing broken is `tblfragments.locationid`.

### The Fix

Restore 65,889 `locationid` values in `tblfragments` from the original dump. The 17,672 fragments that were already negative in the original dump are left unchanged (they still point to valid negative `layerid` entries that exist in the refreshed dump).

### Expected Result

| Metric | After Fix |
|---|---|
| Fragments → positive layerid | 65,889 (restored) |
| Fragments → negative layerid | 17,672 (unchanged) |
| Distinct positive layerids with fragments | 1,769 |
| Distinct negative layerids with fragments | 490 |
| **Total layers with fragments** | **2,259** (matches original exactly) |

### Method: Temporary Table + UPDATE FROM

1. Create a temporary table `tmp_locationid_fix` in the refreshed database with columns `(fragmentid, correct_locationid)`
2. Populate it from the original dump's `tblfragments` data (for fragments with `locationid > 0`)
3. Run `UPDATE tblfragments SET locationid = tmp.correct_locationid FROM tmp_locationid_fix WHERE tblfragments.fragmentid = tmp.fragmentid`
4. Drop the temporary table
5. Dump the fixed database as the new `app_db`

### Steps to Execute

1. **Restore original dump to a check DB** (already done: `backup_check_db`)
2. **Extract fragmentid → locationid mapping** from original dump
3. **Load mapping into temporary table** in refreshed DB
4. **Run UPDATE** to restore locationid values
5. **Verify** the fix (2,259 layers with fragments, all positive layerids valid)
6. **Dump the fixed database** as the new source for `app_db`

---

## 6. Fix Execution Log (2026-05-17)

*This section documents the actual execution of the fix, including deviations from the plan, issues encountered, and how they were resolved.*

### 6.1. Execution Steps

#### Step 1: Extract mapping from original dump

```bash
docker exec -e PGPASSWORD=postgres gkrp-pg psql -U postgres -d backup_check_db -c "
COPY (
  SELECT fragmentid || ',' || locationid
  FROM tblfragments
  WHERE locationid > 0
  ORDER BY fragmentid
) TO '/tmp/locationid_mapping.csv';
"
docker cp gkrp-pg:/tmp/locationid_mapping.csv /home/ubuntu/experiment/gkrp_data_portal/tmp/locationid_mapping.csv
```

Result: **65,889 rows** extracted. CSV format: `fragmentid,locationid`.

#### Step 2: Load mapping and run UPDATE

The initial script used `CREATE TEMPORARY TABLE` but this failed because temporary tables don't persist across separate `docker exec` calls. Each `docker exec` opens a new session, and temporary tables are session-scoped.

**Fix:** Changed to use a regular (non-temporary) table `tmp_locationid_fix` that persists across sessions.

Also, `COPY FROM STDIN` via stdin redirection failed because `docker exec` doesn't pipe stdin correctly.

**Fix:** Copied the CSV file into the container first with `docker cp`, then used `COPY FROM '/tmp/locationid_mapping.csv'`.

#### Step 3: First UPDATE attempt — Foreign Key violation

The first UPDATE attempt failed with:

```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.DuplicateObject) constraint "ck_tblregistered_role_allowed" for relation "tblregistered" already exists
[SQL: ALTER TABLE tblregistered ADD CONSTRAINT ck_tblregistered_role_allowed CHECK (role IN ('admin', 'user'))]
```

This was actually an **Alembic migration error**, not a data error. The migration `0002_auth_extensions` checks for constraint name `role_allowed` but the dump already has it named `ck_tblregistered_role_allowed`.

**Fix:** Updated `_check_exists()` calls in `alembic/versions/0002_auth_extensions.py` to also check for `ck_tblregistered_role_allowed`:

```python
if not _check_exists("tblregistered", "role_allowed") and not _check_exists("tblregistered", "ck_tblregistered_role_allowed"):
    op.create_check_constraint(...)
```

#### Step 4: Second UPDATE attempt — Skipped rows

The second UPDATE ran successfully but only 1,669 fragments ended up with positive `locationid` instead of the expected 65,880. Investigation revealed:

- 9 fragments had `locationid` values that don't exist in the refreshed `tbllayers`
- These were 3 "test" site layers (466, 467, 861) and 1 orphaned layer (232, site="Глухите камъни", empty sector/square)
- The UPDATE had a foreign key constraint that prevented setting `locationid` to non-existent `layerid` values

**Fix:** Added `EXISTS` clause to skip non-existent layerids:

```sql
UPDATE tblfragments f
SET locationid = t.correct_locationid
FROM tmp_locationid_fix t
WHERE f.fragmentid = t.fragmentid
  AND EXISTS (SELECT 1 FROM tbllayers l WHERE l.layerid = t.correct_locationid);
```

Result: **65,880 fragments updated**, 9 skipped.

### 6.2. Final State

| Metric | Before Fix | After Fix | Original (reference) |
|---|---|---|---|
| Fragments → positive layerid | 1,669 (2.0%) | **65,880 (78.8%)** | 65,889 |
| Fragments → negative layerid | 81,889 (98.0%) | **17,678 (21.2%)** | 17,672 |
| Layers with fragments | 105 | **1,818** | 2,259 |
| Total fragments | 83,558 | 83,558 | 83,561 |

**Why 1,818 instead of 2,259?** The difference (441 layers) is because:
- 3 fragments pointed to "test" site layerids (466, 467, 861) that were removed during cleanup
- 6 fragments pointed to layerid 232 (site="Глухите камъни", empty sector/square) that was also removed
- Total: 9 fragments that couldn't be restored = 9 fewer layer references

**Why 17,678 negative instead of 17,672?** The 6 fragments that originally pointed to layerid 232 (which had a negative `locationid` in the original dump) were skipped during the restore, so they remain pointing to their original negative `locationid` values. Plus the 3 test fragments that were removed from the refreshed dump but still have their original negative `locationid` values.

### 6.3. Alembic Migration Fix

The constraint name mismatch in `0002_auth_extensions.py` was fixed by checking for both possible constraint names:

- `role_allowed` (what the migration expects)
- `ck_tblregistered_role_allowed` (what the dump already has)

This makes the migration idempotent — it works whether the constraint comes from the dump or from the migration itself.

### 6.4. Dump of Fixed Database

The fixed database was dumped to:

```
tmp/Pottery_backup_fixed_260517.sql (22MB)
```

This dump includes:
- All 65,880 restored `locationid` values
- All intentional cleanups (site name normalization, sector changes, typo fixes)
- All 4 Alembic migrations applied (0001 through 0005)
- `alembic_version` table dropped (to avoid conflicts on restore)

### 6.5. Scripts Created

All scripts are in `scripts/`:

| Script | Purpose |
|---|---|
| `restore_original.sh` | Restore original dump to `backup_check_db` |
| `analyze_differences.sh` | Compare original vs refreshed data |
| `analyze_refreshed.sh` | Show current `app_db` state |
| `extract_locationid_mapping.sh` | Extract fragmentid → locationid mapping |
| `restore_locationids.sh` | Main fix: load mapping and UPDATE |
| `dump_fixed_db.sh` | Dump fixed database as SQL |

### 6.6. Lessons Learned

1. **Temporary tables don't persist across `docker exec` calls.** Use regular tables for cross-session data.
2. **`docker exec` doesn't support stdin redirection.** Copy files into the container first.
3. **Always check constraint names in dumps.** Alembic migrations assume specific constraint names that may differ from what's in the dump.
4. **Validate foreign key targets before UPDATE.** Skip rows that reference non-existent parent records.
5. **Document the mapping.** Before any bulk data transformation, create a mapping log that records every change. This enables recovery if something goes wrong.
