# Scripts for data normalization and locationid fix

## Overview

This directory contains scripts for analyzing the database dumps, fixing the broken `locationid` values, and producing a clean fixed dump.

## Scripts

### `restore_original.sh`
Restores the original dump (`Pottery_backup_260118.sql`) to a check database (`backup_check_db`) for analysis.

```bash
./scripts/restore_original.sh
```

### `analyze_differences.sh`
Shows the original dump's data: row counts, locationid distribution, site distribution.

```bash
./scripts/analyze_differences.sh
```

### `analyze_refreshed.sh`
Shows the refreshed/current `app_db` state for comparison.

```bash
./scripts/analyze_refreshed.sh
```

### `extract_locationid_mapping.sh`
Extracts the `fragmentid → locationid` mapping from the original dump.
Produces `/tmp/locationid_mapping.csv` with 65,889 rows.

```bash
./scripts/extract_locationid_mapping.sh
```

### `restore_locationids.sh`
The main fix script. Creates a temporary table, loads the mapping, runs UPDATE, verifies, and cleans up.

```bash
./scripts/restore_locationids.sh
```

### `dump_fixed_db.sh`
Dumps the fixed database as a clean SQL file.

```bash
./scripts/dump_fixed_db.sh [output_filename]
```

## Fix Workflow

```bash
# 1. Restore original dump for analysis
./scripts/restore_original.sh

# 2. Analyze the differences
./scripts/analyze_differences.sh
./scripts/analyze_refreshed.sh

# 3. Extract the locationid mapping
./scripts/extract_locationid_mapping.sh

# 4. Restore locationids in the refreshed DB
./scripts/restore_locationids.sh

# 5. Verify the fix (check layers_with_frags = 2,259)
./scripts/analyze_refreshed.sh

# 6. Dump the fixed database
./scripts/dump_fixed_db.sh /tmp/Pottery_backup_fixed.sql
```

## Expected Results

After step 4 (`restore_locationids.sh`):

| Metric | Value |
|---|---|
| Fragments → positive layerid | 65,889 |
| Fragments → negative layerid | 17,672 |
| Layers with fragments | 2,259 |
| Site name normalization | Preserved |
| Sector changes (Сондаж→Център) | Preserved |
