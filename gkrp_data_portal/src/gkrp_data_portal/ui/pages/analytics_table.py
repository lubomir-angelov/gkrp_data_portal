"""NiceGUI page: Analytics (TABLE only).

Layout:
- Left: query selector, filters, column toggles
- Center: table (scrollable)
- Right: images (from fragment/find image_url)
"""

from __future__ import annotations

from typing import Any

from nicegui import app, ui

from gkrp_data_portal.ui.repository.analytics_repo import extract_image_urls

from .analytics_common import (
    DEFAULT_LIMIT,
    QUERY_OPTIONS,
    TABLE_MAX_LIMIT,
    parse_date,
    result_for,
    ui_columns,
)


@ui.page("/analytics/table")
def page_analytics_table() -> None:
    ui.label("Analytics — Table").classes("text-h5")

    state: dict[str, Any] = {
        "query_id": "q1",
        "_refreshing": False,
        "selected_columns": set(),
    }

    with ui.row().classes("w-full gap-4 items-start flex-nowrap"):
        # Left panel
        with ui.column().classes("w-[340px] shrink-0"):
            ui.label("Query + Filters").classes("text-subtitle1 font-medium")

            sel_query = ui.select(
                options=list(QUERY_OPTIONS.keys()),
                value="Filter #1 (Layers + Fragments)",
                label="Predefined query",
            ).classes("w-full")

            with ui.row().classes("w-full gap-2 items-center"):
                btn_run = ui.button("Run query", icon="play_arrow").classes("flex-1")
                sw_autorun = ui.switch("Auto-run", value=True).props("dense")

            inp_site = ui.input("site").props("clearable").classes("w-full")
            inp_sector = ui.input("sector").props("clearable").classes("w-full")
            inp_square = ui.input("square").props("clearable").classes("w-full")
            inp_q = ui.input("free text (inventory/note/piecetype or finds fields)").props("clearable").classes("w-full")

            with ui.row().classes("w-full gap-2"):
                inp_date_from = ui.input("from").props("type=date clearable").classes("w-1/2")
                inp_date_to = ui.input("to").props("type=date clearable").classes("w-1/2")

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

            ui.separator()
            ui.label("Columns").classes("text-subtitle1 font-medium")

            with ui.row().classes("w-full justify-between"):
                btn_select_all = ui.button("Select all")
                btn_clear_all = ui.button("Deselect all")

            columns_container = ui.scroll_area().classes("w-full h-[420px] border rounded p-2 bg-white")

        # Center panel (table only)
        with ui.column().classes("flex-1 min-w-0"):
            ui.label("Table (scrollable)").classes("text-subtitle1 font-medium")
            status = ui.label("").classes("text-sm text-gray-600")
            pending = ui.label("").classes("text-xs text-orange-700")
            dbg = ui.label("").classes("text-xs text-gray-500")

            table_wrap = ui.element("div").classes("w-full border rounded bg-white").style("height: 740px; overflow: auto;")
            with table_wrap:
                table = ui.table(columns=[], rows=[], row_key="__rowid__", pagination=25).classes("w-full")

        # Right panel (images)
        with ui.column().classes("w-[320px] shrink-0"):
            ui.label("Images").classes("text-subtitle1 font-medium")
            images_box = ui.scroll_area().classes("w-full h-[820px] border rounded p-2 bg-white")

    checkboxes: dict[str, Any] = {}

    def _set_table(items: list[dict[str, Any]], visible_cols: list[str]) -> None:
        cols = [{"name": c, "label": c, "field": c} for c in visible_cols]
        rows: list[dict[str, Any]] = []
        for i, r in enumerate(items):
            rr = {"__rowid__": i}
            for c in visible_cols:
                rr[c] = r.get(c)
            rows.append(rr)
        table.columns = cols
        table.rows = rows
        table.update()

    def _set_images(urls: list[str]) -> None:
        images_box.clear()
        with images_box:
            if not urls:
                ui.label("No image URLs in current result.")
                return
            for u in urls[:50]:
                ui.image(u).classes("w-full").props("fit=contain")

    def _rebuild_column_checkboxes(all_columns: list[str]) -> None:
        current = set(all_columns) if not state["selected_columns"] else (set(state["selected_columns"]) & set(all_columns))
        columns_container.clear()
        checkboxes.clear()
        with columns_container:
            for c in all_columns:
                cb = ui.checkbox(c, value=(c in current)).classes("text-sm")
                checkboxes[c] = cb
        state["selected_columns"] = current

    def _read_filters() -> dict[str, Any]:
        query_id = QUERY_OPTIONS.get(sel_query.value, "q1")

        site = (inp_site.value or "").strip() or None
        sector = (inp_sector.value or "").strip() or None
        square = (inp_square.value or "").strip() or None
        q = (inp_q.value or "").strip() or None
        date_from = parse_date(inp_date_from.value)
        date_to = parse_date(inp_date_to.value)

        limit = int(inp_limit.value or DEFAULT_LIMIT)
        limit = max(1, min(limit, TABLE_MAX_LIMIT))

        state["query_id"] = query_id
        app.storage.general["analytics_last_query_id"] = query_id
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps(query_id)};")  # optional consistency

        return {
            "query_id": query_id,
            "site": site,
            "sector": sector,
            "square": square,
            "date_from": date_from,
            "date_to": date_to,
            "q": q,
            "limit": limit,
            "offset": 0,
        }

    def refresh() -> None:
        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            f = _read_filters()

            res = result_for(
                f["query_id"],
                site=f["site"],
                sector=f["sector"],
                square=f["square"],
                date_from=f["date_from"],
                date_to=f["date_to"],
                q=f["q"],
                limit=f["limit"],
                offset=f["offset"],
            )

            total = int(res.total or 0)
            if total == 0:
                _set_table([], [])
                _set_images([])
                dbg.set_text(f"query={f['query_id']} rows=0 total=0")
                status.set_text("⚠️ No results for current filters.")
                return

            ui_cols = ui_columns(res.columns) or list(res.columns)
            if not checkboxes or list(checkboxes.keys()) != ui_cols:
                _rebuild_column_checkboxes(ui_cols)

            visible_cols = [c for c, cb in checkboxes.items() if cb.value]
            if not visible_cols:
                visible_cols = ui_cols[:25] if ui_cols else []

            _set_table(res.items, visible_cols)

            urls = extract_image_urls(res.items)
            _set_images(urls)

            dbg.set_text(f"query={f['query_id']} table_rows={len(res.items)} total={res.total}")
            status.set_text(f"✅ Returned {len(res.items)} rows (total {res.total}).")

        finally:
            state["_refreshing"] = False

    def _select_all() -> None:
        for cb in checkboxes.values():
            cb.set_value(True)
        refresh()

    def _deselect_all() -> None:
        for cb in checkboxes.values():
            cb.set_value(False)
        refresh()

    btn_select_all.on("click", lambda e: _select_all())
    btn_clear_all.on("click", lambda e: _deselect_all())

    def request_refresh() -> None:
        if sw_autorun.value:
            pending.set_text("")
            refresh()
        else:
            pending.set_text("Filters changed — click “Run query”")

    btn_run.on("click", lambda e: (pending.set_text(""), refresh()))

    sel_query.on("change", lambda e: request_refresh())
    for w in (inp_site, inp_sector, inp_square, inp_q, inp_limit):
        w.on("change", lambda e: request_refresh())
    inp_date_from.on("change", lambda e: request_refresh())
    inp_date_to.on("change", lambda e: request_refresh())

    refresh()
