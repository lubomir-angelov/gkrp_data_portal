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
