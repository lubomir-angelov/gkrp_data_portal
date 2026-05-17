# Exploratory Data Analysis — Dynamic Charting

Generated: 2026-05-13

This document records the data exploration done to assess feasibility of dynamic charting on the Analytics page.

## Data Overview

| Table | Rows |
|---|---|
| tbllayers | 2,340 |
| tblfragments | 83,561 |
| tblornaments | 67,459 |
| tblfinds | 0 |

2,259 layers have fragments; 61,134 fragments have ornaments. ~37 fragments per layer, ~1.1 ornaments per fragment.

## Field Coverage & Cardinality

Sorted by data coverage (best for charting first).

| Field | Coverage | Distinct | Chart Suitability |
|---|---|---|---|
| piecetype | 100% | 14 | Excellent |
| technology | 100% | 2 (1, 2) | Excellent for pie/donut |
| surface | 98.9% | 7 | Excellent |
| primarycolor | 93.2% | 11 | Very good |
| baking | 92.5% | 2 (Р, Н) | Excellent for pie |
| covering | 92.1% | 7 | Very good |
| wallthickness | 90.9% | 4 (С, Г, М) | Excellent |
| handlesize | 1.9% | 3 | Only for handle sub-analysis |
| bottomtype | 6.4% | 10 | Poor overall, OK for дръжка only |
| handletype | 15% | 111 | Too many values for bar chart |
| category | 26.5% | 43 | Too many for bar, OK for pie with top-N |
| form | 21.4% | 44 | Too many for bar, OK for pie with top-N |
| type | 19.1% | 7 | Good but 81% are "0" |
| subtype | 18.5% | 25 | Marginal |
| variant | 45.7% | 8 | Good (but skewed: 95% are "0") |

### Ornament Fields

| Field | Coverage | Distinct | Chart Suitability |
|---|---|---|---|
| o_primary | 59% | 12 | Very good |
| o_secondary | 59% | 16 | Good |
| o_encrustcolor1 | 26% | 12 | Marginal |
| o_tertiary | 60% | 18 | Good |
| o_quarternary | 56% | 54 | Too many |
| o_color1 | <1% | 3 | Negligible |

## Key Discoveries

### technology splits cleanly
97.3% is "1", 2.7% is "2" — perfect for pie chart comparisons and as a series dimension for grouped bars.

### handle type is only meaningful for дръжка (handle) pieces
92% of all handle type values come from `piecetype = дръжка` (11,532 of 12,518). For other piece types, handle types are noise. Only ~15% of all fragments have a non-null handle type.

### Site distribution is heavily skewed
Top 2 sites account for 74% of all fragments:

| Site | Fragments | Layers |
|---|---|---|
| Глухите камъни | 31,637 | 916 |
| Ада тепе | 31,331 | 696 |
| Глухите Камъни | 8,539 | 220 |
| Д. Черковище - Аул кая | 4,276 | 139 |
| Чала | 1,997 | 9 |

### piecetype distribution (top 5)

| Piecetype | Count |
|---|---|
| стена (wall) | 43,646 |
| устие (rim) | 21,277 |
| дръжка (handle) | 8,215 |
| дъно (base) | 5,624 |
| стена+дръжка (wall+handle) | 3,223 |

### technology by piecetype
Both technology values (1 and 2) appear across all major piecetypes, making technology a useful series dimension:

| Piecetype | Tech 1 | Tech 2 |
|---|---|---|
| стена | 42,595 | 1,047 |
| устие | 20,737 | 540 |
| дръжка | 8,010 | 205 |
| дъно | 5,273 | 351 |
| стена+дръжка | 3,153 | 70 |

### handle type by piecetype
Handle types are concentrated in дръжка fragments:

| Piecetype | Top handle types |
|---|---|
| дръжка | ВП (2,281), ВО (1,771), Р (1,271), ВЧ (604), ВТ (329) |
| стена | ВП (7), ВО (7), Е1 (3) |
| устие | Е1 (34), Е2 (19), Е (19) |

### primarycolor distribution

| Color | Count |
|---|---|
| черен (black) | 24,597 |
| кафяв (brown) | 20,614 |
| сив (gray) | 9,987 |
| червен (red) | 7,374 |
| тъмнокафяв (dark brown) | 4,632 |

### surface distribution

| Surface | Count |
|---|---|
| В1 | 33,839 |
| Б | 20,073 |
| В2 | 17,769 |
| А | 8,283 |

### Ornament primary distribution

| Primary | Count |
|---|---|
| П | 11,144 |
| Щ | 9,484 |
| К | 8,935 |
| Н | 5,600 |
| В | 3,804 |

## Current Charting Limitations

- Only **one chart type**: vertical bar chart (`plotly_bar()` in `analytics_common.py:148`)
- No pie, donut, line, or stacked bar charts
- No multi-series support — `build_histogram()` returns `(xs, ys)` tuples only
- No auto-refresh on fragment/ornament filter changes
- No chart type selector in UI
- `handletype` (111 distinct values) and `category`/`form` (43-44 values) produce unreadable charts without filtering

## Suggestions for Dynamic Charting

### Phase 1 — Chart Type Switcher (bar / pie / donut)

**Feasibility: High. Low risk. Minimal code changes.**

- Add `sel_chart_type` alongside `sel_x` in the UI
- Add `plotly_pie()` and `plotly_donut()` helpers in `analytics_common.py`
- Same histogram data from `build_histogram()`, just different Plotly trace types
- Fields well-suited: all high-coverage fields have 2-14 distinct values

### Phase 2 — Multi-series / Grouped Bars

**Feasibility: Medium. Requires changes to `build_histogram()` return type.**

- Let user pick a "series" field (e.g., technology, surface, wallthickness)
- `build_histogram()` returns `dict[str, dict[str, int]]` — keyed by series value
- `plotly_bar()` produces multiple traces (one per series value)
- Enables: "show technology 1&2 per piecetype for selected site-square"

### Phase 3 — Small Multiples / Faceted Charts

**Feasibility: Medium. Requires Plotly subplots or multiple chart components.**

- When a low-cardinality field is selected as a "facet" dimension, render one chart per value
- Best candidates: site (top 5-10), sector, piecetype
- Example: user selects site=Глухите камъни → show one bar chart per sector

### Phase 4 — Dynamic Chart Recommendations

**Feasibility: High. UI-only enhancement.**

- Auto-suggest chart types based on selected field cardinality:
  - 2-3 values → pie/donut recommended
  - 4-10 values → bar chart recommended
  - 10+ values → suggest filtering first
- Show data coverage percentage next to field selector so user knows if data is sparse

## What NOT to Do

- Don't use `handletype` as a primary x-axis — 111 distinct values produce unreadable charts
- Don't use `category` or `form` without top-N aggregation — 43-44 values too many
- Don't make fragment/ornament filters auto-refresh the chart — the current "Run query" button is appropriate given the number of distinct-value queries needed to populate filter options
- Don't reintroduce hidden/non-displayable analytics columns into UI selectors
- Don't use `bottomtype` as a primary chart field — only 6.4% coverage

## Data Dictionary Reference

### Fragment Fields (tblfragments)

| Column | Type | Coverage | Distinct |
|---|---|---|---|
| piecetype | enum | 100% | 14 |
| technology | enum | 100% | 2 |
| surface | enum | 98.9% | 7 |
| primarycolor | enum | 93.2% | 11 |
| baking | enum | 92.5% | 2 |
| covering | text | 92.1% | 7 |
| wallthickness | enum | 90.9% | 4 |
| variant | integer | 45.7% | 8 |
| category | varchar | 26.5% | 43 |
| form | varchar | 21.4% | 44 |
| type | integer | 19.1% | 7 |
| subtype | varchar | 18.5% | 25 |
| handletype | varchar | 15.0% | 111 |
| bottomtype | enum | 6.4% | 10 |
| handlesize | enum | 1.9% | 3 |

### Ornament Fields (tblornaments)

| Column | Coverage | Distinct |
|---|---|---|
| o_tertiary | 60% | 18 |
| o_secondary | 59% | 16 |
| o_primary | 59% | 12 |
| o_quarternary | 56% | 54 |
| o_encrustcolor1 | 26% | 12 |
| o_color1 | <1% | 3 |

---

# Exploratory Data Analysis — Refreshed (2026-05-17)

*Data refreshed after database reset from a cleaned/unified dump (Pottery_backup_260513.sql). Original EDA (Pottery_backup_260118.sql) is preserved above as historical record.*

## Data Overview

| Table | Rows (original) | Rows (refreshed) |
|---|---|---|
| tbllayers | 2,340 | 2,335 |
| tblfragments | 83,561 | 83,558 |
| tblornaments | 67,459 | 67,459 |
| tblfinds | 0 | 0 |

| Metric | Original | Refreshed |
|---|---|---|
| Layers with fragments | 2,259 | **105** |
| Fragments with ornaments | 61,134 | 61,134 |
| Avg fragments per layer | ~37 | **35.8** |
| Avg ornaments per fragment | ~1.1 | **0.81** |

The refreshed data has **~2,154 fewer layers with fragments**. This is not a schema or migration issue — the newer dump file itself contains only 105 distinct `locationid` values in `tblfragments`, compared to 2,259 in the original dump. The total fragment count is nearly identical (83,561 vs 83,558), meaning fragments from ~2,154 layers were reassigned to the remaining 105 layers during data cleanup.

## Field Coverage & Cardinality (Refreshed)

Sorted by data coverage (best for charting first).

| Field | Coverage (original) | Coverage (refreshed) | Distinct | Changed? |
|---|---|---|---|---|
| piecetype | 100% | **100.0%** | 14 | No |
| technology | 100% | **100.0%** | 2 | No |
| surface | 98.9% | **98.9%** | 7 | No |
| primarycolor | 93.2% | **93.2%** | 11 | No |
| baking | 92.5% | **92.5%** | 2 | No |
| covering | 92.1% | **92.4%** | 7 | No |
| wallthickness | 90.9% | **91.0%** | 4 | No |
| handlesize | 1.9% | **1.9%** | 3 | No |
| bottomtype | 6.4% | **48.0%** | 10 | **Yes** |
| handletype | 15% | **53.5%** | 111 | **Yes** |
| category | 26.5% | **60.6%** | 43 | **Yes** |
| form | 21.4% | **57.2%** | 44 | **Yes** |
| type | 19.1% | **56.3%** | 7 | **Yes** |
| subtype | 18.5% | **55.9%** | 25 | **Yes** |
| variant | 45.7% | **45.7%** | 8 | No |

### Ornament Fields (Refreshed)

| Field | Coverage (original) | Coverage (refreshed) | Distinct | Changed? |
|---|---|---|---|---|
| o_primary | 59% | **59.4%** | 12 | No |
| o_secondary | 59% | **58.6%** | 16 | No |
| o_tertiary | 60% | **59.5%** | 18 | No |
| o_quarternary | 56% | **55.5%** | 54 | No |
| o_encrustcolor1 | 26% | **26.2%** | 12 | No |
| o_color1 | <1% | **0.0%** | 3 | No |

Ornament fields are stable — no meaningful changes after data cleanup.

## Key Discoveries (Refreshed)

### technology splits cleanly
Unchanged: 97.3% is "1", 2.7% is "2".

### handle type distribution changed significantly
**Original finding:** "92% of all handle type values come from дръжка (11,532 of 12,518). Only ~15% of all fragments have a non-null handle type."

**Refreshed data:** Only **18.2%** of handle type values come from дръжка (8,126 of 44,704). The data cleanup populated handle type values across many more piecetypes. The original finding that "handle type is only meaningful for дръжка" is **no longer directionally strong** — while дръжка still has the most handle types, the field is now much more broadly populated.

### Site distribution — consolidation and normalization

**Original:** "Глухите камъни" (31,637 frags, 916 layers) and "Глухите Камъни" (8,539 frags, 220 layers) were separate site entries (case difference + Cyrillic encoding variation). Top 2 sites accounted for 74% of fragments.

**Refreshed:** The site name variations were **merged into a single entry** "Глухите камъни" with **40,301 fragments across only 2 layers**. The other site variations ("Глухите Камъни", "Глухите Каъмни") no longer exist. Top 2 sites now account for **85.1%** of fragments.

| Site | Original fragments | Refreshed fragments | Original layers | Refreshed layers |
|---|---|---|---|---|
| Глухите камъни | 31,637 | **40,301** | 916 | **2** |
| Глухите Камъни | 8,539 | *(merged)* | 220 | — |
| Глухите Каъмни | 56 | *(merged)* | 1 | — |
| Ада тепе | 31,331 | 31,331 | 696 | **1** |

### piecetype distribution (refreshed)
Unchanged from original: стена 43,644, устие 21,276, дръжка 8,215, дъно 5,624, стена+дръжка 3,223.

### technology by piecetype (refreshed)
Unchanged from original: стена 42,593/1,047, устие 20,736/540, дръжка 8,010/205, дъно 5,273/351, стена+дръжка 3,153/70.

### primarycolor distribution (refreshed)
Unchanged from original: черен 24,597, кафяв 20,614, сив 9,986, червен 7,374, тъмнокафяв 4,632.

### surface distribution (refreshed)
Unchanged from original: В1 33,838, Б 20,073, В2 17,769, А 8,281.

### Ornament primary distribution (refreshed)
Unchanged from original: П 11,144, Щ 9,484, К 8,935, Н 5,600, В 3,804.

## What Changed vs. What Stayed the Same

### Changed
- **Layers with fragments:** 2,259 → 105 (fragments reassigned to fewer layers)
- **bottomtype coverage:** 6.4% → 48.0% (data populated)
- **handletype coverage:** 15% → 53.5% (data populated across more piecetypes)
- **category coverage:** 26.5% → 60.6% (data populated)
- **form coverage:** 21.4% → 57.2% (data populated)
- **type coverage:** 19.1% → 56.3% (data populated)
- **subtype coverage:** 18.5% → 55.9% (data populated)
- **Site "Глухите Камъни" / "Глухите Каъмни"** merged into "Глухите камъни"
- **Layers per site** collapsed: most sites went from dozens/hundreds of layers down to 1
- **Handle type no longer concentrated in дръжка** (18.2% vs 92%)

### Unchanged
- All ornament field coverages and distributions
- All piecetype, technology, surface, primarycolor, baking, covering, wallthickness, handlesize, variant coverages
- All distinct value counts for every field
- All top-N distribution values (piecetype, technology, colors, surfaces, ornaments)
- Row counts (nearly identical: 83,561 vs 83,558 fragments)
- technology split (97.3% / 2.7%)

## Data Source Comparison

| | Original dump | Refreshed dump |
|---|---|---|
| File | Pottery_backup_260118.sql | Pottery_backup_260513.sql |
| Total layers | 2,340 | 2,335 |
| Total fragments | 83,561 | 83,558 |
| Distinct locationids in fragments | 2,259 | 105 |
| Layers with fragments | 2,259 | 105 |
| Layers without fragments | 81 | 2,230 |
| All fragments have locationid | Yes (0 nulls) | Yes (0 nulls) |
| Site name issues | 4 variations of "Глухите камъни" | 1 normalized entry |
| "test" site | 3 layers (2 with fragments) | Removed |
