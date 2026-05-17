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
