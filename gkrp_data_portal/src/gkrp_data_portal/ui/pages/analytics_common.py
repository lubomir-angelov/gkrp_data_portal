"""Shared helpers/constants for Analytics NiceGUI pages."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    AnalyticsResult,
    query_finds,
    query_q2_layers_fragments_ornaments,
)

QUERY_OPTIONS: dict[str, str] = {
    "Filter #2 (Layers + Fragments + Ornaments)": "q2",
    "Finds (tblfinds)": "finds",
}

DEFAULT_LIMIT = 500

TABLE_MAX_LIMIT = 100000  # table UI cap
CHART_MAX_FETCH = 25000  # chart safety cap (top-N buckets don't benefit from >25k rows)


_UI_HIDDEN_COLUMNS = frozenset(
    {
        "l_recordenteredon",
        "l_recordenteredby",
        "l_recordcreatedby",
        "l_recordcreatedon",
        "l_level",
        "l_structure",
        "l_includes",
        "l_color1",
        "l_color2",
        "l_description",
        "l_akb_num",
        "l_layerid",
        "l_layertype",
        "l_stratum",
        "l_parentid",
        "l_photos",
        "l_drawings",
        "l_handfragments",
        "l_wheelfragment",
        "f_fragmentid",
        "f_locationid",
        "f_outline",
        "f_speed",
        "f_recrodenteredby",
        "f_recrodenteredon",
        "f_topsize",
        "f_necksize",
        "f_bodysize",
        "f_bottomsize",
        "f_dishheight",
        "f_composition",
        "f_parallels",
        "f_decoration",
        "f_recordcreatedby",
        "f_recordcreatedon",
        "f_recordenteredby",
        "f_recordenteredon",
        "f_image",
        "f_count",
    }
)


def is_ui_hidden_column(name: str) -> bool:
    return (name or "").strip().lower() in _UI_HIDDEN_COLUMNS


def ui_columns(columns: list[str]) -> list[str]:
    """Return columns allowed to appear in UI (preserves original casing)."""
    return [c for c in columns if not is_ui_hidden_column(c)]


def parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def result_for(query_id: str, **kwargs) -> AnalyticsResult:
    with session_scope() as db:
        if query_id == "q2":
            return query_q2_layers_fragments_ornaments(db, **kwargs)
        return query_finds(db, **kwargs)


def _extract_layer_filters(kwargs: dict) -> dict[str, Any] | None:
    """Extract layer_filters from kwargs, falling back to legacy site/sector/square."""
    lf = kwargs.get("layer_filters")
    if lf:
        return lf
    site = kwargs.get("site")
    sector = kwargs.get("sector")
    square = kwargs.get("square")
    if site or sector or square:
        return {
            "Site": [site] if site else [],
            "Sector": [sector] if sector else [],
            "Square": [square] if square else [],
        }
    return None


def norm_bucket(v: Any) -> str:
    """Normalize values into a histogram bucket label (never empty)."""
    if v is None:
        return "(null)"
    if isinstance(v, str):
        s = v.strip()
        return s if s else "(null)"
    return str(v)


_COLUMN_LABELS: dict[str, str] = {
    "f_piecetype": "Piecetype",
    "f_technology": "Technology",
    "f_baking": "Baking",
    "f_primarycolor": "Primary color",
    "f_covering": "Covering",
    "f_surface": "Surface",
    "f_wallthickness": "Wall thickness",
    "f_handletype": "Handle type",
    "f_handlesize": "Handle size",
    "f_bottomtype": "Bottom type",
    "f_category": "Category",
    "f_form": "Form",
    "f_type": "Type",
    "f_subtype": "Subtype",
    "f_variant": "Variant",
    "o_primary": "Ornament primary",
    "o_secondary": "Ornament secondary",
    "o_tertiary": "Ornament tertiary",
    "o_quarternary": "Ornament quarternary",
    "o_color1": "Ornament color",
    "o_encrustcolor1": "Encrust color",
    "l_site": "Site",
    "l_sector": "Sector",
    "l_square": "Square",
    "l_layer": "Layer",
}


def _column_to_label(col: str) -> str:
    """Convert a prefixed column name to a readable label."""
    return _COLUMN_LABELS.get(col, col)


def build_histogram(
    rows: list[dict], x_key: str, top_n: int = 30
) -> tuple[list[str], list[int]]:
    """Build a top-N histogram for a column from dict rows.

    The y-values always sum ``f_count`` instead of counting rows, because each
    row represents *count* physical fragments.
    """
    if not rows or not x_key:
        return [], []

    bucket_sum: dict[str, int] = {}
    for r in rows:
        bucket = norm_bucket(r.get(x_key))
        val = r.get("f_count")
        bucket_sum[bucket] = bucket_sum.get(bucket, 0) + (
            val if isinstance(val, (int, float)) else 0
        )

    items = sorted(bucket_sum.items(), key=lambda x: x[1], reverse=True)[:top_n]
    xs = [k for k, _ in items]
    ys = [v for _, v in items]
    return xs, ys


def build_histogram_series(
    rows: list[dict], x_key: str, series_key: str, top_n: int = 30
) -> tuple[list[str], dict[str, list[int]]]:
    """Build a top-N histogram grouped by a series dimension.

    Returns ``(xs, series_data)`` where ``xs`` are the top-N bucket labels and
    ``series_data`` is ``{series_value: [y1, y2, ...]}`` — one list per series
    value, aligned to ``xs``.
    """
    if not rows or not x_key or not series_key:
        return [], {}

    bucket_series: dict[tuple[str, str], int] = {}
    for r in rows:
        x_bucket = norm_bucket(r.get(x_key))
        s_bucket = norm_bucket(r.get(series_key))
        val = r.get("f_count")
        bucket_series[(x_bucket, s_bucket)] = bucket_series.get(
            (x_bucket, s_bucket), 0
        ) + (val if isinstance(val, (int, float)) else 0)

    # Aggregate per x_bucket (sum across series) to pick top-N
    bucket_total: dict[str, int] = {}
    for (xb, sb), v in bucket_series.items():
        bucket_total[xb] = bucket_total.get(xb, 0) + v

    top_buckets = sorted(bucket_total.items(), key=lambda x: x[1], reverse=True)[:top_n]
    xs = [k for k, _ in top_buckets]

    # Collect all series values seen in the top-N buckets
    all_series: set[str] = set()
    for xb in xs:
        for bx, bs in bucket_series:
            if bx == xb:
                all_series.add(bs)

    # Build aligned series data — trace names are raw values, group title is column label
    series_vals: dict[str, list[int]] = {}
    for sv in all_series:
        key = sv
        series_vals[key] = []
        for xb in xs:
            series_vals[key].append(bucket_series.get((xb, sv), 0))

    return xs, series_vals


def plotly_bar(xs: list[str], ys: list[int], title: str) -> dict:
    return {
        "data": [
            {
                "type": "bar",
                "x": xs,
                "y": ys,
                "textposition": "outside",
                "texttemplate": "%{y}",
                "textfont": {"size": 12},
                "hovertemplate": "<b>%{x}</b><br>Count: %{y}<extra></extra>",
            }
        ],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 50, "r": 20, "t": 50, "b": 90},
            "xaxis": {"automargin": True, "tickangle": -30},
            "yaxis": {"automargin": True},
        },
    }


def plotly_pie(labels: list[str], values: list[int], title: str) -> dict:
    return {
        "data": [
            {
                "type": "pie",
                "labels": labels,
                "values": values,
                "hole": 0.0,
                "textinfo": "label+percent",
                "textposition": "outside",
                "automargin": True,
            }
        ],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
            "showlegend": True,
        },
    }


def plotly_donut(labels: list[str], values: list[int], title: str) -> dict:
    return {
        "data": [
            {
                "type": "pie",
                "labels": labels,
                "values": values,
                "hole": 0.4,
                "textinfo": "label+percent",
                "textposition": "outside",
                "automargin": True,
            }
        ],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
            "showlegend": True,
        },
    }


def plotly_grouped_bar(
    xs: list[str],
    series_data: dict[str, list[int]],
    title: str,
    series_label: str = "Series",
) -> dict:
    """Build a grouped (clustered) bar chart with one trace per series value."""
    if not xs or not series_data:
        return plotly_bar([], [], title)

    data_traces: list[dict] = []
    for series_name, ys in series_data.items():
        data_traces.append(
            {
                "type": "bar",
                "name": series_name,
                "x": xs,
                "y": ys,
                "legendgroup": series_label,
                "showlegend": True,
                "textposition": "outside",
                "texttemplate": "%{y}",
                "textfont": {"size": 12},
                "hovertemplate": f"<b>%{{x}}</b><br>{series_name}: %{{y}}<extra></extra>",
                "legendgrouptitle_text": series_label,
            }
        )

    return {
        "data": data_traces,
        "layout": {
            "title": {"text": title},
            "barmode": "group",
            "margin": {"l": 50, "r": 20, "t": 50, "b": 90},
            "xaxis": {"automargin": True, "tickangle": -30},
            "yaxis": {"automargin": True},
            "showlegend": True,
            "legend": {
                "title": {"text": series_label},
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        },
    }
