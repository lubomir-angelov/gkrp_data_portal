# Chart Page Performance Optimization

## Analysis Summary

### Current State

- **Data volumes**: 2,340 layers, 83,561 fragments, 67,456 ornaments
- **q2 query** (default, most expensive): `tbllayers INNER JOIN tblfragments LEFT JOIN tblornaments`
- **Chart fetch limit**: 25,000 rows (reduced from 250k in commit 783e973)
- **Table fetch limit**: 100,000 rows (when "max" is selected)
- **Histogram**: only needs top-30 buckets from those rows

### Why It's Slow — Root Causes

#### 1. Row multiplication from LEFT JOIN tblornaments (primary bottleneck)

`analytics_repo.py:348`: fragments LEFT JOIN ornaments creates a cartesian-like explosion. With 83k fragments and 67k ornaments, a single fragment with 2-3 ornaments doubles/triples the result set. The 25k row fetch limit may still pull 50k-100k+ actual joined rows from the DB.

#### 2. `get_distinct_values` fires N separate queries per refresh

`analytics_repo.py:596-617`: For each filter column needed (20+ columns for q2), it runs a separate `SELECT DISTINCT col::text FROM ... WHERE ... ORDER BY v`. On every `refresh()`, this is **20+ additional queries** on top of the main query.

#### 3. `get_layer_hierarchy` also fires a full query

`analytics_repo.py:725-731`: On every page load, fetches all distinct site/sector/square/layer combinations.

#### 4. Python-side histogram building on large row sets

`analytics_common.py:688-722`: `build_histogram()` iterates all 25k rows in Python to build top-30 buckets. This is O(n) in Python — fast enough for 25k but wasteful.

#### 5. `_populate_frag_filter_options` re-reads filters from UI state

`analytics_chart_fragments.py:729`: Inside `_populate_frag_filter_options`, it calls `_read_filters()` which re-reads all UI widget values. The filter dropdowns are populated based on a query filtered by their own current (possibly stale) values.

### Is It Resource-Bound?

**Partially.** The queries are already reasonably indexed (commit 0005 added join and filter indexes). The main cost is:

- **PostgreSQL I/O**: Reading 25k+ joined rows with all columns (4 tables x ~30 columns each = 120 column values per row) requires significant memory bandwidth. If the working set doesn't fit in shared_buffers + OS cache, you'll see disk I/O waits.
- **Python memory**: 25k rows x ~50 columns = 1.25M dict entries loaded into Python memory, then iterated for histogram building.

**Bigger containers would help if:**
- PostgreSQL is currently I/O-bound. If shared_buffers is small relative to the joined working set, more RAM lets more of the join fit in memory.
- The Python process is being OOM-killed or swapping (unlikely at 25k rows, but possible at 100k "max").

**It is NOT purely resource-bound because:**
- The query fetches all 50+ columns when only 5-10 are needed for charting
- The N+1 distinct-value queries could be consolidated
- The row multiplication from the ornament join is structural, not resource-related

### Programmatic Improvements

#### High Impact

1. **Push histogram aggregation into SQL** — Instead of fetching 25k rows and building the histogram in Python, run the GROUP BY in the database. The main data query (for the table) and the chart query should be separate.
2. **Consolidate `get_distinct_values` into a single query** — Instead of N separate `SELECT DISTINCT` queries, use a single query with `json_agg(DISTINCT ...)` per column or a CTE that computes all distinct values in one pass.
3. **Add a covering index for the q2 query's common filter path** — The current composite index is `site, sector, square`. When filtering by `recordenteredon` too, PostgreSQL may not use both.

#### Medium Impact

4. **Cache distinct values** — The filter dropdown options don't change between queries unless the underlying data changes. Cache them with a short TTL (e.g., 5 minutes) keyed by the filter state.
5. **Selective column fetching for chart queries** — The chart only needs the X-axis column + f_count. Fetch only those columns for charting, not all 50+ columns from all 4 tables.
6. **Debounce the distinct-value queries** — Currently `_populate_frag_filter_options` fires on every refresh. If the user changes the X-axis or chart type, the distinct values don't need to re-fetch.

#### Lower Impact

7. **Use `LIMIT` before `ORDER BY` in the ornament join** — If ornaments aren't needed for the chart, exclude them from the chart fetch query entirely (separate code path for chart vs. table).
8. **Materialized view for common aggregations** — Pre-compute top-level aggregations (counts by site, sector, piecetype) in a materialized view that refreshes periodically.

---

## Plan: Push Histogram Aggregation into SQL

### Overview

Currently, the chart page fetches up to 25,000 full rows from the database, then iterates them in Python to build a top-30 histogram. This is wasteful because:

- The chart only needs aggregated counts per bucket, not individual rows
- The LEFT JOIN to tblornaments multiplies rows (one fragment can have multiple ornaments)
- All 50+ columns from 4 tables are fetched when only 2-3 are needed for charting

The fix introduces a **chart-specific query path** that performs GROUP BY aggregation in SQL, returning only the top-N buckets directly from the database. The existing row-fetching path is preserved for the table view.

### Changes

#### 1. New repository function: `build_chart_histogram`

**File**: `gkrp_data_portal/src/gkrp_data_portal/ui/repository/analytics_repo.py`

Add a new function `build_chart_histogram` that:

- Accepts the same filter parameters as the existing query functions
- Accepts `x_key` (the column to group by) and `series_key` (optional secondary grouping)
- Accepts `top_n` (default 30) and `limit` (safety cap, default 25000)
- Builds and executes a SQL query that:
  - Applies the same WHERE clause filters as the existing queries
  - Groups by the x_key column (and series_key if provided)
  - Sums `f_count` or `f_count_deduped` per group (matching existing histogram logic)
  - Orders by count descending, LIMIT top_n
- Returns a list of `{bucket: str, count: int, series: str | None}` dicts

**SQL structure for q2 (no series):**
```sql
SELECT
    <x_key_column> AS bucket,
    COALESCE(SUM(f_count_deduped), 0) AS count
FROM (
    SELECT l.<x_key>, f.count AS f_count_deduped,
           MAX(f.count) OVER (PARTITION BY f.fragmentid) AS f_count_deduped
    FROM tbllayers l
    INNER JOIN tblfragments f ON l.layerid = f.locationid
    LEFT JOIN tblornaments o ON f.fragmentid = o.fragmentid
    <WHERE clause>
) sub
WHERE bucket IS NOT NULL
GROUP BY bucket
ORDER BY count DESC
LIMIT <top_n>
```

**Key design decisions:**

- The window function `MAX(f.count) OVER (PARTITION BY f.fragmentid)` is applied in a subquery to de-duplicate fragment counts across ornament rows, then the outer query groups and sums. This matches the existing `f_count_deduped` semantics in `query_q2_layers_fragments_ornaments`.
- The WHERE clause is built using the same `_build_where` helper to ensure filter consistency.
- For the "finds" and "finds_arch" queries, the subquery structure adapts to their respective joins.

**SQL structure for q2 (with series):**
```sql
SELECT
    <x_key_column> AS x_bucket,
    <series_key_column> AS series_bucket,
    COALESCE(SUM(f_count_deduped), 0) AS count
FROM (...) sub
WHERE x_bucket IS NOT NULL AND series_bucket IS NOT NULL
GROUP BY x_bucket, series_bucket
ORDER BY count DESC
```
The caller then pivots the result into the `{x_bucket: {series: count}}` structure matching `build_histogram_series` output.

#### 2. Update `analytics_common.py` histogram builders

**File**: `gkrp_data_portal/src/gkrp_data_portal/ui/pages/analytics_common.py`

Modify `build_histogram` and `build_histogram_series` to accept an optional pre-aggregated data source:

```python
def build_histogram(
    rows: list[dict],
    x_key: str,
    top_n: int = 30,
    pre_aggregated: list[dict] | None = None,
) -> tuple[list[str], list[int]]:
    """Build a top-N histogram.

    If *pre_aggregated* is provided (from SQL aggregation), use it directly.
    Otherwise, fall back to Python-side aggregation from raw rows.
    """
    if pre_aggregated:
        # pre_aggregated is [{bucket: str, count: int}, ...]
        items = sorted(pre_aggregated, key=lambda x: x["count"], reverse=True)[:top_n]
        return [i["bucket"] for i in items], [i["count"] for i in items]
    # ... existing Python-side logic unchanged ...
```

Similarly for `build_histogram_series`, accept `pre_aggregated_series` as a list of `{x_bucket, series_bucket, count}` dicts and pivot them in Python (the pivot is O(n) where n = top_n x series_count, which is small).

This keeps the existing Python-side path as a fallback (for backward compatibility and for cases where pre-aggregation isn't used) while enabling the SQL path.

#### 3. Wire chart-specific query into the page refresh flow

**File**: `gkrp_data_portal/src/gkrp_data_portal/ui/pages/analytics_chart_fragments.py`

In `refresh()`, split the data fetching into two paths:

```python
def refresh() -> None:
    f = _read_filters()
    x_key = sel_x.value
    series_key = sel_series.value

    # --- Chart path: use SQL aggregation ---
    chart_agg = build_chart_histogram(
        db,
        query_id="q2",
        x_key=x_key,
        series_key=series_key,
        layer_filters=f.get("layer_filters"),
        frag_filters=f.get("frag_filters"),
        top_n=30,
        limit=CHART_MAX_FETCH,
    )

    # Build figure from pre-aggregated data (no raw rows needed for chart)
    xs, ys_or_series = _build_chart_data_from_agg(chart_agg, series_key)
    _set_chart(_build_figure(xs, ys_or_series, ...))

    # --- Table path: still needs raw rows ---
    # Only fetch raw rows if the table view is active
    if table_view_active:
        res = result_for(f["query_id"], limit=table_limit, ...)
        # ... existing table rendering logic unchanged ...
```

**For the current NiceGUI chart-only page**, the raw row fetch can be **eliminated entirely** for chart rendering. The raw rows are only needed for:
- Populating filter dropdown options (already handled by `get_distinct_values`)
- The table view (separate page, unchanged)

So for the chart page, `refresh()` only needs:
1. `get_layer_hierarchy` (cached, fires once on load)
2. `build_chart_histogram` (SQL aggregation, replaces the 25k-row fetch)
3. `get_distinct_values` for filter dropdowns (can be cached, separate concern)

#### 4. Handle column name resolution

The `x_key` and `series_key` values come from the UI as column names like `l_site`, `l_sector`, `f_piecetype`. The `build_chart_histogram` function needs to resolve these to actual SQL column expressions.

**Approach**: Reuse the existing `_COLUMN_LABEL_KEYS` mapping in reverse (label -> column) and the `_DISTINCT_COL_DEFS` which already maps `(label, sql_col_expr, query_ids)`. Build a lookup:

```python
# In analytics_repo.py
_COL_EXPR_LOOKUP: dict[str, dict[str, str]] = {}
for label, sql_expr, qids in _DISTINCT_COL_DEFS:
    for qid in qids:
        _COL_EXPR_LOOKUP.setdefault(qid, {})[label] = sql_expr
```

When `build_chart_histogram` receives `x_key="l_site"`, it looks up the SQL expression. For columns that are already in the `l_`/`f_`/`o_` prefixed format (as they appear in query results), the function needs to map them back to the base table column names used in SQL.

**Simpler approach**: Instead of reverse-mapping, have the UI send the SQL column expression directly, or use a mapping from the prefixed result column name to the SQL expression. Since the query functions already use `_model_select_list` which produces `{prefix}{col_name}`, the reverse mapping is: strip the prefix, look up the base column name.

For q2:
- `l_site` -> `l.site`
- `l_sector` -> `l.sector`
- `f_piecetype` -> `f.piecetype`
- `o_primary` -> `o.primary_` (note the underscore)

This mapping can be built from `_COLUMN_LABEL_KEYS` and the alias prefixes.

#### 5. Handle the "max" limit case

When the user selects "max" (100,000 rows), the SQL aggregation path is still correct — GROUP BY with LIMIT 30 is independent of the total row count. The `limit` parameter becomes a safety cap on the subquery to prevent runaway memory in the window function, but for the histogram aggregation it has minimal impact since we're grouping, not returning individual rows.

### File Change Summary

| File | Change |
|---|---|
| `analytics_repo.py` | Add `build_chart_histogram()` function with SQL GROUP BY aggregation |
| `analytics_common.py` | Update `build_histogram()` and `build_histogram_series()` to accept pre-aggregated data |
| `analytics_chart_fragments.py` | Replace raw-row chart fetch with `build_chart_histogram` call in `refresh()` |
| `analytics_chart_finds.py` | Same change for the finds chart page |
| `analytics_chart.py` | Same change for the main chart page (if it still exists as a separate route) |

### Risk Assessment

| Risk | Mitigation |
|---|---|
| SQL aggregation doesn't match Python histogram semantics exactly | Keep Python-side path as fallback; add tests comparing SQL vs Python output |
| Column name resolution is fragile | Use existing `_DISTINCT_COL_DEFS` as the single source of truth for column mappings |
| Series grouping with SQL adds complexity | Start with single-axis (no series) support; add series in a follow-up |
| Existing pages that rely on raw rows for charting break | The change is additive: `build_chart_histogram` is a new function; existing `result_for` path is unchanged |

### Testing Plan

1. **Unit tests for `build_chart_histogram`**:
   - Test with q2 query, various x_key values (l_site, l_sector, f_piecetype)
   - Test with series_key provided
   - Test with filters applied (site, sector, frag_filters)
   - Test that results match `build_histogram` output for the same data
   - Test empty result set
   - Test that f_count_deduped de-duplication works correctly

2. **Integration test**:
   - Load the chart page, verify the chart renders correctly with SQL-aggregated data
   - Compare chart output before/after the change for the same filter state

3. **Regression test**:
   - Ensure the table view page still works (it uses the existing `result_for` path, unchanged)
   - Ensure filter dropdown population still works (uses `get_distinct_values`, unchanged)

### Estimated Impact

- **Chart page load time**: Expected 5-10x improvement (eliminating 25k-row fetch + Python iteration)
- **Database load**: Significantly reduced (GROUP BY with LIMIT 30 vs. full join + LIMIT 25000)
- **Memory**: Python process no longer holds 25k x 50-column row dicts for chart rendering
- **Table view**: No change (uses existing path)
