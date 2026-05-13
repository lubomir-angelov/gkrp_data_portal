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

TABLE_MAX_LIMIT = 50000  # table UI cap
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


def plotly_bar(xs: list[str], ys: list[int], title: str) -> dict:
    return {
        "data": [{"type": "bar", "x": xs, "y": ys}],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 50, "r": 20, "t": 50, "b": 90},
            "xaxis": {"automargin": True, "tickangle": -30},
            "yaxis": {"automargin": True},
        },
    }
