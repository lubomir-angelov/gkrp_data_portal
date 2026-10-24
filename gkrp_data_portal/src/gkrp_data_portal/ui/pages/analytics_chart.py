"""NiceGUI page: Analytics (CHART — legacy, redirects to split pages).

This page is deprecated in favour of the split chart pages:
- /analytics/chart_fragments  (fragments + ornaments)
- /analytics/chart_finds      (finds)

Kept for backwards-compatibility; redirects to chart_fragments.
"""

from __future__ import annotations

import csv
import io
from nicegui import app, ui
from starlette.responses import Response

from .analytics_common import (
    CHART_FINDS_ROUTE,
    CHART_FRAGMENTS_ROUTE,
    DEFAULT_LIMIT,
    TABLE_MAX_LIMIT,
    parse_date,
    result_for,
    ui_columns,
)
from gkrp_data_portal.ui.lang import t


@ui.page("/analytics")
def page_analytics_index() -> None:
    ui.label(t("title_analytics")).classes("text-h5 text-blue-600")
    with ui.row().classes("gap-2"):
        ui.button(
            t("btn_chart_fragments"),
            on_click=lambda: ui.navigate.to(CHART_FRAGMENTS_ROUTE),
            icon="bar_chart",
        )
        ui.button(
            t("btn_chart_finds"),
            on_click=lambda: ui.navigate.to(CHART_FINDS_ROUTE),
            icon="show_chart",
        )
        ui.button(
            t("btn_table_view"),
            on_click=lambda: ui.navigate.to("/analytics/table"),
            icon="table_chart",
        )


@ui.page("/analytics/chart")
def page_analytics_chart() -> None:
    """Legacy chart page — redirects to the split fragments chart page."""
    ui.navigate.to(CHART_FRAGMENTS_ROUTE)


# -------------------------
# Export endpoints (kept here so they register once)
# -------------------------


@app.get("/api/analytics/data.csv")
def analytics_data_csv(
    query_id: str = "q2",
    site: str | None = None,
    sector: str | None = None,
    square: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> Response:
    df = parse_date(date_from)
    dt = parse_date(date_to)

    res = result_for(
        query_id,
        site=site or None,
        sector=sector or None,
        square=square or None,
        date_from=df,
        date_to=dt,
        q=q or None,
        limit=min(max(int(limit), 1), TABLE_MAX_LIMIT),
        offset=0,
    )

    buf = io.StringIO()
    cols = ui_columns(res.columns)
    writer = csv.DictWriter(buf, fieldnames=cols)
    writer.writeheader()
    for row in res.items:
        writer.writerow({k: row.get(k) for k in cols})

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="analytics_{query_id}.csv"'
        },
    )
