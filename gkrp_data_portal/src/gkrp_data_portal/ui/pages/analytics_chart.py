"""NiceGUI page: Analytics (CHART — legacy, redirects to split pages).

This page is deprecated in favour of the split chart pages:
- /analytics/chart_fragments  (fragments + ornaments)
- /analytics/chart_finds      (finds)

Kept for backwards-compatibility; redirects to chart_fragments.
"""

from __future__ import annotations

import csv
import io
import json
import pathlib
import markdown
from loguru import logger
from nicegui import app, ui
from starlette.responses import HTMLResponse, PlainTextResponse, Response

from .analytics_common import (
    CHART_FINDS_ROUTE,
    CHART_FRAGMENTS_ROUTE,
    DEFAULT_LIMIT,
    TABLE_MAX_LIMIT,
    build_histogram,
    build_histogram_series,
    parse_date,
    plotly_bar,
    plotly_donut,
    plotly_grouped_bar,
    plotly_pie,
    result_for,
    ui_columns,
    _column_to_label,
)
from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    build_chart_histogram,
)
from gkrp_data_portal.ui.lang import t

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[5]
_CHART_GUIDE_PATH = _PROJECT_ROOT / "CHART.md"


def _load_chart_guide() -> str:
    """Load and render CHART.md as HTML."""
    if _CHART_GUIDE_PATH.exists():
        md = _CHART_GUIDE_PATH.read_text(encoding="utf-8")
        return markdown.markdown(md, extensions=["tables", "fenced_code"])
    return "<p>Chart guide not found.</p>"


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

    logger.info(
        "DEBUG first_row_keys: {}",
        sorted(res.items[0].keys()) if res.items else "NO_ROWS",
    )
    logger.info("DEBUG first_row_sample: {}", res.items[0] if res.items else "NO_ROWS")

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


@app.get("/api/analytics/chart.json")
def analytics_chart_json(
    query_id: str = "q2",
    x: str | None = None,
    chart_type: str = "bar",
    series: str | None = None,
    site: str | None = None,
    sector: str | None = None,
    square: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
) -> Response:
    df = parse_date(date_from)
    dt = parse_date(date_to)

    if not x:
        x = "f_piecetype" if query_id in ("q2", "finds") else "fi_find_type"

    with session_scope() as db:
        chart_agg = build_chart_histogram(
            db,
            query_id=query_id,
            x_key=x,
            series_key=series,
            site=site or None,
            sector=sector or None,
            square=square or None,
            date_from=df,
            date_to=dt,
            q=q or None,
            top_n=30,
        )

    if not chart_agg:
        if chart_type == "pie":
            fig = plotly_pie([], [], title=f"Count by {x} ({query_id})")
        elif chart_type == "donut":
            fig = plotly_donut([], [], title=f"Count by {x} ({query_id})")
        else:
            fig = plotly_bar([], [], title=f"Count by {x} ({query_id})")
        return Response(content=json.dumps(fig), media_type="application/json")

    if series:
        xs, series_data = build_histogram_series(
            [], x, series, top_n=30, pre_aggregated=chart_agg
        )
        series_label = _column_to_label(series)
        fig = plotly_grouped_bar(
            xs,
            series_data,
            title=f"Count by {x} grouped by {series} ({query_id})",
            series_label=series_label,
        )
    else:
        xs, ys = build_histogram(
            [], x, top_n=30, pre_aggregated=chart_agg
        )
        if chart_type == "pie":
            fig = plotly_pie(xs, ys, title=f"Count by {x} ({query_id})")
        elif chart_type == "donut":
            fig = plotly_donut(xs, ys, title=f"Count by {x} ({query_id})")
        else:
            fig = plotly_bar(xs, ys, title=f"Count by {x} ({query_id})")
    return Response(content=json.dumps(fig), media_type="application/json")


@app.get("/api/analytics/chart.html")
def analytics_chart_html(query_id: str = "q2") -> Response:
    qid = query_id or (app.storage.general.get("analytics_last_query_id") or "q2")
    fig_json = analytics_chart_json(query_id=qid).body.decode("utf-8")

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Analytics Chart</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    body {{ margin: 0; font-family: sans-serif; }}
    #chart {{ width: 100vw; height: 92vh; }}
    .hint {{ padding: 10px; }}
  </style>
</head>
<body>
  <div class="hint">Use browser Print \u2192 Save as PDF.</div>
  <div id="chart"></div>
  <script>
    const fig = {fig_json};
    const cfg = fig.config || {{responsive: true, displaylogo: false}};
    Plotly.newPlot('chart', fig.data || [], fig.layout || {{}}, cfg);
  </script>
</body>
</html>
"""
    return HTMLResponse(html)


@app.get("/api/analytics/health")
def analytics_health() -> Response:
    return PlainTextResponse("ok")
