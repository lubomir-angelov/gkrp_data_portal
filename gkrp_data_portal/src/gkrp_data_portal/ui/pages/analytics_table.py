"""NiceGUI page: Analytics (TABLE only).

Layout:
- Left: query selector, filters, column toggles
- Center: grid (scrollable, with per-column dropdown filters)
- Right: images (from fragment/find image_url)
"""

from __future__ import annotations

import json
from typing import Any

from nicegui import app, ui

from gkrp_data_portal.ui.repository.analytics_repo import extract_image_urls

from .analytics_common import (
    DEFAULT_LIMIT,
    QUERY_OPTIONS,
    TABLE_MAX_LIMIT,
    result_for,
    ui_columns,
)


@ui.page("/analytics/table")
def page_analytics_table() -> None:
    """Render the Analytics Table page.

    This page provides:
    - a left panel for selecting a predefined query and applying filters,
    - a center panel with an interactive AG Grid table (filterable/sortable),
    - a right panel that previews images extracted from the result rows.

    Notes:
        - Date filters are intentionally removed (date_from/date_to are passed as None).
        - Column visibility is controlled via checkboxes and AG Grid column visibility APIs.
        - Functionality is intentionally unchanged; this is a readability/docstrings pass.
    """
    ui.label("Analytics — Table").classes("text-h5")

    # Mutable state shared across callbacks (kept in-memory for this page instance).
    state: dict[str, Any] = {
        "query_id": "q1",
        "_refreshing": False,
        "selected_columns": set(),
        "last_items": [],
        "last_columns": [],
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
            inp_q = (
                ui.input("free text (inventory/note/piecetype or finds fields)")
                .props("clearable")
                .classes("w-full")
            )

            # Date inputs removed, as requested.

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

            ui.separator()
            ui.label("Columns").classes("text-subtitle1 font-medium")

            with ui.row().classes("w-full justify-between"):
                btn_select_all = ui.button("Select all")
                btn_clear_all = ui.button("Deselect all")

            columns_container = (
                ui.scroll_area().classes("w-full h-[420px] border rounded p-2 bg-white")
            )

        # Center panel (grid)
        with ui.column().classes("flex-1 min-w-0"):
            ui.label("Table (scrollable)").classes("text-subtitle1 font-medium")
            status = ui.label("").classes("text-sm text-gray-600")
            pending = ui.label("").classes("text-xs text-orange-700")
            dbg = ui.label("").classes("text-xs text-gray-500")

            # AG Grid: horizontal scrollbar stays at the bottom of the grid viewport
            grid = ui.aggrid(
                {
                    "columnDefs": [],
                    "rowData": [],
                    "defaultColDef": {
                        "resizable": True,
                        "sortable": True,
                        "filter": True,
                        "floatingFilter": True,  # shows filter UI below header
                        "menuTabs": ["filterMenuTab"],  # focus the header menu on filtering
                    },
                    "animateRows": True,
                    "pagination": True,
                    "paginationPageSize": 25,
                    "alwaysShowHorizontalScroll": True,
                    "alwaysShowVerticalScroll": True,
                }
            ).classes("w-full border rounded bg-white").style("height: 740px;")

            ui.label(
                "Tip: use the filter UI in the header (set filter dropdown shows available values)."
            ).classes("text-xs text-gray-500 mt-1")

        # Right panel (images)
        with ui.column().classes("w-[320px] shrink-0"):
            ui.label("Images").classes("text-subtitle1 font-medium")
            images_box = ui.scroll_area().classes(
                "w-full h-[820px] border rounded p-2 bg-white"
            )

    # Column checkbox widgets keyed by column name.
    checkboxes: dict[str, Any] = {}

    def _set_grid(items: list[dict[str, Any]], visible_cols: list[str]) -> None:
        """Populate AG Grid with the given rows and visible columns.

        Uses the AG Grid Set Filter for each column to provide value dropdowns.
        """
        col_defs = [
            {
                "headerName": c,
                "field": c,
                "filter": "agSetColumnFilter",
                "filterParams": {"buttons": ["reset", "apply"], "closeOnApply": True},
            }
            for c in visible_cols
        ]

        row_data: list[dict[str, Any]] = []
        for i, r in enumerate(items):
            rr: dict[str, Any] = {"__rowid__": i}
            for c in visible_cols:
                rr[c] = r.get(c)
            row_data.append(rr)

        grid.options["columnDefs"] = col_defs
        grid.options["rowData"] = row_data
        grid.update()

    def _set_images(urls: list[str]) -> None:
        """Render up to 50 images from extracted URLs in the right panel."""
        images_box.clear()
        with images_box:
            if not urls:
                ui.label("No image URLs in current result.")
                return
            for u in urls[:50]:
                ui.image(u).classes("w-full").props("fit=contain")

    def _apply_view() -> None:
        """Apply the current checkbox selections to the grid and image panel.

        If no columns are selected, a fallback of the first 25 columns is used.
        """
        items: list[dict[str, Any]] = state.get("last_items", [])
        ui_cols: list[str] = state.get("last_columns", [])

        visible_cols = [c for c, cb in checkboxes.items() if cb.value]
        if not visible_cols:
            visible_cols = ui_cols[:25] if ui_cols else []

        _set_grid(items, visible_cols)
        _set_images(extract_image_urls(items))

        dbg.set_text(
            f"query={state.get('query_id')} table_rows={len(items)} cols={len(visible_cols)}"
        )

    def _rebuild_column_checkboxes(all_columns: list[str]) -> None:
        """Rebuild the checkbox list for all columns.

        Keeps a stable selection set in state['selected_columns'] where possible.
        """
        # Remove permanently hidden columns
        cleaned = all_columns

        current = (
            set(cleaned)
            if not state["selected_columns"]
            else (set(state["selected_columns"]) & set(cleaned))
        )

        columns_container.clear()
        checkboxes.clear()

        def _set_column_visible(col: str, visible: bool) -> None:
            """Toggle visibility of a single column in AG Grid."""
            grid.run_grid_method("setColumnsVisible", [col], visible)


        with columns_container:
            for c in cleaned:
                cb = ui.checkbox(c, value=(c in current)).classes("text-sm")
                #cb.on("change", lambda e, col=c: _set_column_visible(col, e.value))
                cb.on("change", lambda e: _apply_view())
                checkboxes[c] = cb

        state["selected_columns"] = current

    def _read_filters() -> dict[str, Any]:
        """Read current filter widgets and normalize the filter payload."""
        query_id = QUERY_OPTIONS.get(sel_query.value, "q1")

        site = (inp_site.value or "").strip() or None
        sector = (inp_sector.value or "").strip() or None
        square = (inp_square.value or "").strip() or None
        q = (inp_q.value or "").strip() or None

        limit = int(inp_limit.value or DEFAULT_LIMIT)
        limit = max(1, min(limit, TABLE_MAX_LIMIT))

        # Persist and expose selected query id.
        state["query_id"] = query_id
        app.storage.general["analytics_last_query_id"] = query_id
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps(query_id)};")

        return {
            "query_id": query_id,
            "site": site,
            "sector": sector,
            "square": square,
            "q": q,
            "limit": limit,
            "offset": 0,
        }

    def refresh() -> None:
        """Run the backend query and refresh grid + images + status labels."""
        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            f = _read_filters()

            # Date filters removed => pass None for date_from/date_to
            res = result_for(
                f["query_id"],
                site=f["site"],
                sector=f["sector"],
                square=f["square"],
                date_from=None,
                date_to=None,
                q=f["q"],
                limit=f["limit"],
                offset=f["offset"],
            )

            total = int(res.total or 0)
            if total == 0:
                state["last_items"] = []
                state["last_columns"] = []
                _set_grid([], [])
                _set_images([])
                dbg.set_text(f"query={f['query_id']} rows=0 total=0")
                status.set_text("⚠️ No results for current filters.")
                return

            ui_cols = ui_columns(res.columns) or list(res.columns)

            if not checkboxes or list(checkboxes.keys()) != ui_cols:
                _rebuild_column_checkboxes(ui_cols)

            state["last_items"] = res.items
            state["last_columns"] = ui_cols

            _apply_view()

            dbg.set_text(
                f"query={f['query_id']} table_rows={len(res.items)} total={res.total}"
            )
            status.set_text(f"✅ Returned {len(res.items)} rows (total {res.total}).")

        finally:
            state["_refreshing"] = False

    def _select_all() -> None:
        """Select all columns and re-render the grid/images."""
        for cb in checkboxes.values():
            cb.set_value(True)
        _apply_view()

    def _deselect_all() -> None:
        """Deselect all columns and re-render the grid/images."""
        for cb in checkboxes.values():
            cb.set_value(False)
        _apply_view()

    btn_select_all.on("click", lambda e: _select_all())
    btn_clear_all.on("click", lambda e: _deselect_all())

    def request_refresh() -> None:
        """Auto-refresh if enabled; otherwise show a 'pending' hint."""
        if sw_autorun.value:
            pending.set_text("")
            refresh()
        else:
            pending.set_text("Filters changed — click “Run query”")

    btn_run.on("click", lambda e: (pending.set_text(""), refresh()))

    sel_query.on("change", lambda e: request_refresh())
    for w in (inp_site, inp_sector, inp_square, inp_q, inp_limit):
        w.on("change", lambda e: request_refresh())

    # Initial load
    refresh()