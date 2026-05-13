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

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    extract_image_urls,
    get_layer_hierarchy,
)

from .analytics_common import (
    DEFAULT_LIMIT,
    QUERY_OPTIONS,
    TABLE_MAX_LIMIT,
    result_for,
    ui_columns,
)


def _select_to_list(widget: ui.select) -> list[str] | None:
    """Convert a NiceGUI select widget value to a filtered list of strings.

    Returns None when the widget has no selection.
    """
    vals = widget.value
    if isinstance(vals, list) and vals:
        return [str(v).strip() for v in vals if str(v).strip()]
    if isinstance(vals, str) and vals.strip():
        return [vals.strip()]
    return None


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
        - Layer filters follow a Site->Sector->Square->Layer hierarchy.
    """
    ui.label("Analytics — Table").classes("text-h5")

    # Mutable state shared across callbacks (kept in-memory for this page instance).
    state: dict[str, Any] = {
        "query_id": "q2",
        "_refreshing": False,
        "selected_columns": set(),
        "last_items": [],
        "last_columns": [],
        "_hierarchy": {},
        "_all_sites": [],
        "_all_sectors": [],
        "_all_squares": [],
        "_all_layers": [],
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

            with ui.scroll_area().classes(
                "w-full h-[200px] border rounded p-2 bg-white"
            ):
                sel_site_t = ui.select(
                    options=[],
                    label="Site",
                    multiple=True,
                    clearable=True,
                    with_input=True,
                ).classes("w-full").props("dense")

                sel_sector_t = ui.select(
                    options=[],
                    multiple=True,
                    clearable=True,
                    with_input=True,
                    label="Sector",
                ).classes("w-full").props("dense")

                sel_square_t = ui.select(
                    options=[],
                    multiple=True,
                    clearable=True,
                    with_input=True,
                    label="Square",
                ).classes("w-full").props("dense")

                sel_layer_t = ui.select(
                    options=[],
                    multiple=True,
                    clearable=True,
                    with_input=True,
                    label="Layer",
                ).classes("w-full").props("dense")

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

            ui.separator()
            ui.label("Columns").classes("text-subtitle1 font-medium")

            with ui.row().classes("w-full justify-between"):
                btn_select_all = ui.button("Select all")
                btn_clear_all = ui.button("Deselect all")

            columns_container = ui.scroll_area().classes(
                "w-full h-[420px] border rounded p-2 bg-white"
            )

        # Center panel (grid)
        with ui.column().classes("flex-1 min-w-0"):
            ui.label("Table (scrollable)").classes("text-subtitle1 font-medium")
            status = ui.label("").classes("text-sm text-gray-600")
            pending = ui.label("").classes("text-xs text-orange-700")
            dbg = ui.label("").classes("text-xs text-gray-500")

            # AG Grid: horizontal scrollbar stays at the bottom of the grid viewport
            grid = (
                ui.aggrid(
                    {
                        "columnDefs": [],
                        "rowData": [],
                        "defaultColDef": {
                            "resizable": True,
                            "sortable": True,
                            "filter": True,
                            "floatingFilter": True,
                            "menuTabs": [
                                "filterMenuTab"
                            ],
                        },
                        "animateRows": True,
                        "pagination": True,
                        "paginationPageSize": 25,
                        "alwaysShowHorizontalScroll": True,
                        "alwaysShowVerticalScroll": True,
                    }
                )
                .classes("w-full border rounded bg-white")
                .style("height: 740px;")
            )

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
                cb.on("change", lambda e: _apply_view())
                checkboxes[c] = cb

        state["selected_columns"] = current

    def _fetch_layer_cache() -> None:
        """Fetch the layer hierarchy from the database and cache it in state."""
        with session_scope() as db:
            hierarchy_data = get_layer_hierarchy(db, query_id="q2")
        state["_hierarchy"] = hierarchy_data.get("hierarchy", {})
        state["_all_sites"] = hierarchy_data.get("all_sites", [])
        state["_all_sectors"] = hierarchy_data.get("all_sectors", [])
        state["_all_squares"] = hierarchy_data.get("all_squares", [])
        state["_all_layers"] = hierarchy_data.get("all_layers", [])

    def _populate_layer_options_hierarchical() -> None:
        """Populate layer dropdown options based on the cached hierarchy.

        Enforces the Site -> Sector -> Square -> Layer cascade:
        - Selecting a site filters sectors, squares, and layers to that site.
        - Selecting a sector filters squares and layers to that sector.
        - Selecting a square filters layers to that square.
        """
        hierarchy = state["_hierarchy"]

        sel_site_t.clear()
        sel_sector_t.clear()
        sel_square_t.clear()
        sel_layer_t.clear()

        all_sites = state["_all_sites"]
        all_sectors = state["_all_sectors"]
        all_squares = state["_all_squares"]
        all_layers = state["_all_layers"]

        sel_site_t.set_options(all_sites, label="Site")
        sel_sector_t.set_options(all_sectors, label="Sector")
        sel_square_t.set_options(all_squares, label="Square")
        sel_layer_t.set_options(all_layers, label="Layer")

        sel_site_t.update()
        sel_sector_t.update()
        sel_square_t.update()
        sel_layer_t.update()

        # Apply cascade based on current selections
        site_val = _select_to_list(sel_site_t)
        sector_val = _select_to_list(sel_sector_t)
        square_val = _select_to_list(sel_square_t)

        # Determine effective site(s) for filtering
        if site_val:
            sites_to_use = site_val
        else:
            sites_to_use = all_sites

        # Filter sectors based on selected sites
        if sites_to_use:
            filtered_sectors = set()
            for site in sites_to_use:
                site_hier = hierarchy.get(site, {})
                filtered_sectors.update(site_hier.keys())
            filtered_sectors = sorted(filtered_sectors)
            sel_sector_t.set_options(filtered_sectors, label="Sector")
            sel_sector_t.update()

            # If current sector selection is no longer valid, clear it
            current_sector = _select_to_list(sel_sector_t)
            if current_sector:
                valid_sectors = set(filtered_sectors)
                for s in current_sector:
                    if s not in valid_sectors:
                        sel_sector_t.set_value(None)
                        break
        else:
            sel_sector_t.set_value(None)

        # Determine effective sectors
        sector_sel = _select_to_list(sel_sector_t)
        if sector_sel:
            sectors_to_use = sector_sel
        else:
            sectors_to_use = (sel_sector_t.options or [])[:]

        # Filter squares based on selected sites and sectors
        if sites_to_use and sectors_to_use:
            filtered_squares = set()
            for site in sites_to_use:
                site_hier = hierarchy.get(site, {})
                for sector in sectors_to_use:
                    sector_hier = site_hier.get(sector, {})
                    filtered_squares.update(sector_hier.keys())
            filtered_squares = sorted(filtered_squares)
            sel_square_t.set_options(filtered_squares, label="Square")
            sel_square_t.update()

            current_square = _select_to_list(sel_square_t)
            if current_square:
                valid_squares = set(filtered_squares)
                for sq in current_square:
                    if sq not in valid_squares:
                        sel_square_t.set_value(None)
                        break
        else:
            sel_square_t.set_value(None)

        # Determine effective squares
        square_sel = _select_to_list(sel_square_t)
        if square_sel:
            squares_to_use = square_sel
        else:
            squares_to_use = (sel_square_t.options or [])[:]

        # Filter layers based on selected sites, sectors, and squares
        if sites_to_use and sectors_to_use and squares_to_use:
            filtered_layers = set()
            for site in sites_to_use:
                site_hier = hierarchy.get(site, {})
                for sector in sectors_to_use:
                    sector_hier = site_hier.get(sector, {})
                    for square in squares_to_use:
                        square_layers = sector_hier.get(square, [])
                        filtered_layers.update(square_layers)
            filtered_layers = sorted(filtered_layers)
            sel_layer_t.set_options(filtered_layers, label="Layer")
            sel_layer_t.update()

            current_layer = _select_to_list(sel_layer_t)
            if current_layer:
                valid_layers = set(filtered_layers)
                for item in current_layer:
                    if l not in valid_layers:
                        sel_layer_t.set_value(None)
                        break
        else:
            sel_layer_t.set_value(None)

    def _read_filters() -> dict[str, Any]:
        """Read current filter widgets and normalize the filter payload."""
        query_id = QUERY_OPTIONS.get(sel_query.value, "q2")

        layer_filters_map: dict[str, list[str] | None] = {}
        layer_filters_map["Site"] = _select_to_list(sel_site_t)
        layer_filters_map["Sector"] = _select_to_list(sel_sector_t)
        layer_filters_map["Square"] = _select_to_list(sel_square_t)
        layer_filters_map["Layer"] = _select_to_list(sel_layer_t)

        limit = int(inp_limit.value or DEFAULT_LIMIT)
        limit = max(1, min(limit, TABLE_MAX_LIMIT))

        # Persist and expose selected query id.
        state["query_id"] = query_id
        app.storage.general["analytics_last_query_id"] = query_id
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps(query_id)};")

        return {
            "query_id": query_id,
            "layer_filters": layer_filters_map,
            "limit": limit,
            "offset": 0,
        }

    def refresh() -> None:
        """Run the backend query and refresh grid + images + status labels."""
        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            _fetch_layer_cache()
            _populate_layer_options_hierarchical()

            f = _read_filters()

            res = result_for(
                f["query_id"],
                layer_filters=f.get("layer_filters"),
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
            pending.set_text("Filters changed - click Run query")

    btn_run.on("click", lambda e: (pending.set_text(""), refresh()))

    sel_query.on("change", lambda e: request_refresh())

    def _on_site_change(e) -> None:
        _populate_layer_options_hierarchical()
        request_refresh()

    def _on_sector_change(e) -> None:
        _populate_layer_options_hierarchical()
        request_refresh()

    def _on_square_change(e) -> None:
        _populate_layer_options_hierarchical()
        request_refresh()

    def _on_layer_change(e) -> None:
        _populate_layer_options_hierarchical()
        request_refresh()

    sel_site_t.on("change", _on_site_change)
    sel_sector_t.on("change", _on_sector_change)
    sel_square_t.on("change", _on_square_change)
    sel_layer_t.on("change", _on_layer_change)

    inp_limit.on("change", lambda e: request_refresh())

    # Initial load
    _fetch_layer_cache()
    _populate_layer_options_hierarchical()
    refresh()
