"""Shared helpers/constants for Analytics NiceGUI pages."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any, Optional

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    AnalyticsResult,
    query_finds,
    query_q1_layers_fragments,
    query_q2_layers_fragments_ornaments,
)

QUERY_OPTIONS: dict[str, str] = {
    "Filter #1 (Layers + Fragments)": "q1",
    "Filter #2 (Layers + Fragments + Ornaments)": "q2",
    "Finds (tblfinds)": "finds",
}

DEFAULT_LIMIT = 500

TABLE_MAX_LIMIT = 50000      # table UI cap
CHART_MAX_FETCH = 250000     # chart safety cap


_UI_HIDDEN_COLUMNS = frozenset(
    {
        "l_recordenteredon",
        "l_recordenteredby",
        "l_recordcreatedby",
        "l_level",
        "l_structure",
        "l_includes",
        "l_color1",
        "l_color2",
        "l_description",
        "l_akb_num",
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
        if query_id == "q1":
            return query_q1_layers_fragments(db, **kwargs)
        if query_id == "q2":
            return query_q2_layers_fragments_ornaments(db, **kwargs)
        return query_finds(db, **kwargs)


def norm_bucket(v: Any) -> str:
    """Normalize values into a histogram bucket label (never empty)."""
    if v is None:
        return "(null)"
    if isinstance(v, str):
        s = v.strip()
        return s if s else "(null)"
    return str(v)


def build_histogram(rows: list[dict], x_key: str, top_n: int = 30) -> tuple[list[str], list[int]]:
    """Build a top-N histogram for a column from dict rows."""
    if not rows or not x_key:
        return [], []
    c = Counter(norm_bucket(r.get(x_key)) for r in rows)
    items = c.most_common(top_n)
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
