"""Analytics repository: predefined queries + safe filtering.

Implements the predefined queries: layers+fragments+ornaments (q2), tblfinds
(finds) and the archaeological finds table (finds_arch).

All result columns are prefixed to avoid collisions:
- l_<col> for tbllayers
- f_<col> for tblfragments
- o_<col> for tblornaments
- fi_<col> for tblfinds
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from gkrp_data_portal.models.archaeology import (
    Find,
    Tbllayer,
    Tblfragment,
    Tblornament,
    Tblfind,
)


@dataclass(frozen=True)
class AnalyticsResult:
    items: list[dict[str, Any]]
    total: int
    columns: list[str]


def _model_select_list(prefix: str, alias: str, model) -> list[str]:
    cols = []
    for col in model.__table__.columns:
        cols.append(f"{alias}.{col.name} AS {prefix}{col.name}")
    return cols


# Canonical UI-label -> bare column-name maps. Filter widgets on the pages,
# DISTINCT dropdowns, group-by columns and the chart WHERE clause all derive
# from these keys; tests/test_analytics_columns.py checks that every chart
# subquery projects every mapped column. Dict order is the UI/DISTINCT order.
LAYER_FILTER_COLS: dict[str, str] = {
    "Site": "site",
    "Sector": "sector",
    "Square": "square",
    "Layer": "layer",
}
# finds has no site column; its location columns live on the finds table itself
FINDS_LOCATION_FILTER_COLS: dict[str, str] = {
    "Sector": "sector",
    "Square": "square",
    "Layer": "layer_mechanical",
}
FRAGMENT_FILTER_COLS: dict[str, str] = {
    "Piecetype": "piecetype",
    "Technology": "technology",
    "Baking": "baking",
    "Color / Primary color": "primarycolor",
    "Covering": "covering",
    "Surface": "surface",
    "Wall thickness": "wallthickness",
    "Handle type": "handletype",
    "Handle size": "handlesize",
    "Bottom type": "bottomtype",
    "Category": "category",
    "Form": "form",
    "Type": "type",
    "Subtype": "subtype",
    "Variant": "variant",
}
ORNAMENT_FILTER_COLS: dict[str, str] = {
    "Primary": "primary_",
    "Secondary": "secondary",
    "Tertiary": "tertiary",
    "Quarternary": "quarternary",
    "Color / color1": "color1",
    "Encrust color": "encrustcolor1",
}
ARCH_FILTER_COLS: dict[str, str] = {
    "Find Type": "find_type",
    "Material": "material",
    "Coin": "coin",
    "Denomination": "denomination",
    "Mint": "mint",
    "Year": "year",
    "Inv No": "inv_no",
    "Depth": "depth_m",
    "Context": "context",
}


def _qualified(alias: str, cols: Mapping[str, str]) -> dict[str, str]:
    """Prefix every bare column in *cols* with the SQL table alias."""
    return {label: f"{alias}.{col}" for label, col in cols.items()}


def _add_ilike_filters(
    clauses: list[str],
    params: dict[str, Any],
    *,
    param_prefix: str,
    label_to_col: Mapping[str, str],
    filters: Mapping[str, Any],
) -> None:
    """Append one ILIKE clause per non-empty filter; list values are OR-ed.

    Bind names derive from the bare column name (always a valid SQL bind
    identifier). An unknown label raises ``KeyError``.
    """
    for label, values in filters.items():
        col = label_to_col[label]
        col_expr = f"{col}::text"
        param_name = f"{param_prefix}_{col.rsplit('.', 1)[-1]}"
        if isinstance(values, list) and values:
            names = [f"{param_name}_{i}" for i in range(len(values))]
            clauses.append(
                "(" + " OR ".join(f"{col_expr} ILIKE :{n}" for n in names) + ")"
            )
            params.update({n: f"%{v}%" for n, v in zip(names, values)})
        elif isinstance(values, str) and values.strip():
            params[param_name] = f"%{values.strip()}%"
            clauses.append(f"{col_expr} ILIKE :{param_name}")


def _apply_frag_filters(
    clauses: list[str],
    params: dict[str, Any],
    frag_filters: dict[str, Any],
    frag_alias: str = "f",
    orn_alias: str = "o",
) -> None:
    """Apply fragment + ornament field filters from the UI dropdowns."""
    _add_ilike_filters(
        clauses,
        params,
        param_prefix="frag",
        label_to_col={
            **_qualified(frag_alias, FRAGMENT_FILTER_COLS),
            **_qualified(orn_alias, ORNAMENT_FILTER_COLS),
        },
        filters=frag_filters,
    )


def _apply_arch_filters(
    clauses: list[str],
    params: dict[str, Any],
    arch_filters: dict[str, Any],
) -> None:
    """Apply archaeological finds field filters (``fi`` alias)."""
    _add_ilike_filters(
        clauses,
        params,
        param_prefix="arch",
        label_to_col=_qualified("fi", ARCH_FILTER_COLS),
        filters=arch_filters,
    )


def _apply_layer_filters(
    clauses: list[str],
    params: dict[str, Any],
    layer_filters: dict[str, Any],
    layer_alias: str = "l",
) -> None:
    """Apply layer field filters from the UI dropdowns."""
    _add_ilike_filters(
        clauses,
        params,
        param_prefix="layer",
        label_to_col=_qualified(layer_alias, LAYER_FILTER_COLS),
        filters=layer_filters,
    )


def _build_where(
    *,
    query_id: str,
    site: Optional[str],
    sector: Optional[str],
    square: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    q: Optional[str],
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
    layer_alias: str = "l",
    frag_alias: str = "f",
    orn_alias: str = "o",
) -> tuple[str, dict[str, Any]]:
    """Build a safe WHERE clause using only whitelisted filters."""
    clauses: list[str] = []
    params: dict[str, Any] = {}

    # Layer-scoped filters (always safe; all queries include layer_alias)
    if layer_filters:
        _apply_layer_filters(clauses, params, layer_filters, layer_alias)
    else:
        if site:
            clauses.append(f"{layer_alias}.site ILIKE :site")
            params["site"] = f"%{site}%"
        if sector:
            clauses.append(f"{layer_alias}.sector ILIKE :sector")
            params["sector"] = f"%{sector}%"
        if square:
            clauses.append(f"{layer_alias}.square ILIKE :square")
            params["square"] = f"%{square}%"

    if date_from:
        clauses.append(f"{layer_alias}.recordenteredon >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append(f"{layer_alias}.recordenteredon <= :date_to")
        params["date_to"] = date_to

    # Free-text: differs slightly by query (which aliases exist)
    if q:
        params["q"] = f"%{q}%"
        if query_id == "q2":
            clauses.append(
                "(COALESCE(f.inventory,'') ILIKE :q OR COALESCE(f.note,'') ILIKE :q OR COALESCE(f.piecetype::text,'') ILIKE :q)"
            )
        elif query_id == "finds":
            clauses.append(
                "(COALESCE(fi.description,'') ILIKE :q OR COALESCE(fi.findtype,'') ILIKE :q OR COALESCE(fi.inventory,'') ILIKE :q)"
            )

    # Fragment field filters (only applied for q2 which has f alias)
    if frag_filters and query_id in ("q2",):
        _apply_frag_filters(clauses, params, frag_filters, frag_alias, orn_alias)

    # Archaeological finds filters (only applied for finds_arch)
    if frag_filters and query_id == "finds_arch":
        _apply_arch_filters(clauses, params, frag_filters)

    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


def _run_sql(
    db: Session,
    *,
    sql: str,
    params: dict[str, Any],
    limit: int,
    offset: int,
) -> list[RowMapping]:
    sql_paginated = f"{sql} LIMIT :limit OFFSET :offset"
    params2 = dict(params)
    params2["limit"] = limit
    params2["offset"] = offset
    return db.execute(text(sql_paginated), params2).mappings().all()


def _count_sql(db: Session, *, count_sql: str, params: dict[str, Any]) -> int:
    row = db.execute(text(count_sql), params).scalar_one()
    return int(row)


def query_q2_layers_fragments_ornaments(
    db: Session,
    *,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
) -> AnalyticsResult:
    """Filter #2: tbllayers LEFT JOIN tblfragments LEFT JOIN tblornaments.

    ``f_count_deduped`` repeats f.count on every ornament row of a fragment
    (display column of the table; totals count distinct fragments separately).
    Fragments without ornaments are included via LEFT JOIN.
    """
    select_cols = (
        _model_select_list("l_", "l", Tbllayer)
        + _model_select_list("f_", "f", Tblfragment)
        + _model_select_list("o_", "o", Tblornament)
    )
    base = f"""
    SELECT
      {", ".join(select_cols)},
      MAX(f.count) OVER (PARTITION BY f.fragmentid) AS f_count_deduped
    FROM tbllayers l
    INNER JOIN tblfragments f ON l.layerid = f.locationid
    LEFT JOIN tblornaments o ON f.fragmentid = o.fragmentid
    """

    where_sql, params = _build_where(
        query_id="q2",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
        layer_alias="l",
    )

    sql = f"{base}\n{where_sql}\nORDER BY l.layerid DESC, f.fragmentid DESC, o.ornamentid DESC"
    count_where_sql, count_params = _build_where(
        query_id="q2",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
        layer_alias="l2",
        frag_alias="f2",
        orn_alias="o2",
    )
    count_sql = f"""SELECT COALESCE((
        SELECT SUM(f2.count) FROM (
            SELECT DISTINCT f2.fragmentid, f2.count
            FROM tblfragments f2
            INNER JOIN tbllayers l2 ON l2.layerid = f2.locationid
            {count_where_sql}
        ) f2
    ), 0)"""

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=count_params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys())
        if items
        else [c.split(" AS ")[-1] for c in select_cols] + ["f_count_deduped"]
    )
    return AnalyticsResult(items=items, total=total, columns=columns)


def query_finds(
    db: Session,
    *,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
) -> AnalyticsResult:
    """Finds selector: tblfinds tied to layers/fragments/ornaments (left joins).

    Each tblfinds row is a separate find (no count column to deduplicate).
    """
    select_cols = (
        _model_select_list("fi_", "fi", Tblfind)
        + _model_select_list("l_", "l", Tbllayer)
        + _model_select_list("f_", "f", Tblfragment)
        + _model_select_list("o_", "o", Tblornament)
    )

    base = f"""
    SELECT
      {", ".join(select_cols)}
    FROM tblfinds fi
    INNER JOIN tbllayers l ON l.layerid = fi.layerid
    LEFT JOIN tblfragments f ON f.fragmentid = fi.fragmentid
    LEFT JOIN tblornaments o ON o.ornamentid = fi.ornamentid
    """

    where_sql, params = _build_where(
        query_id="finds",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
        layer_alias="l",
    )

    sql = f"{base}\n{where_sql}\nORDER BY fi.findid DESC"
    count_where_sql, count_params = _build_where(
        query_id="finds",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
        layer_alias="l2",
        frag_alias="f2",
        orn_alias="o2",
    )
    count_sql = f"""SELECT COUNT(*) FROM (
        SELECT fi2.findid
        FROM tblfinds fi2
        INNER JOIN tbllayers l2 ON l2.layerid = fi2.layerid
        LEFT JOIN tblfragments f2 ON f2.fragmentid = fi2.fragmentid
        LEFT JOIN tblornaments o2 ON o2.ornamentid = fi2.ornamentid
        {count_where_sql}
    ) x"""

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=count_params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    )
    return AnalyticsResult(items=items, total=total, columns=columns)


# Column definitions for DISTINCT queries: (label, sql_col_expr, query_ids)
_DISTINCT_COL_DEFS: list[tuple[str, str, tuple[str, ...]]] = (
    [(lbl, f"l.{c}", ("q2", "finds")) for lbl, c in LAYER_FILTER_COLS.items()]
    + [(lbl, f"f.{c}", ("q2",)) for lbl, c in FRAGMENT_FILTER_COLS.items()]
    + [("Note", "f.note", ("q2",)), ("Inventory", "f.inventory", ("q2",))]
    + [(lbl, f"o.{c}", ("q2",)) for lbl, c in ORNAMENT_FILTER_COLS.items()]
    + [(lbl, f"fi.{c}", ("finds_arch",)) for lbl, c in ARCH_FILTER_COLS.items()]
    + [
        (lbl, f"fi.{c}", ("finds_arch",))
        for lbl, c in FINDS_LOCATION_FILTER_COLS.items()
    ]
)


# Per-query mapping: query_id -> {prefixed result column name: SQL col expression}
# e.g. {"q2": {"l_site": "l.site", "o_primary_": "o.primary_", ...}}.
# Dict order is the UI order of _DISTINCT_COL_DEFS.
def _build_chart_col_expr() -> dict[str, dict[str, str]]:
    """{query_id: {prefixed_col: "alias.col"}} from _DISTINCT_COL_DEFS."""
    by_query: dict[str, dict[str, str]] = {}
    for _label, sql_expr, qids in _DISTINCT_COL_DEFS:
        alias, col = sql_expr.split(".", 1)
        for qid in qids:
            by_query.setdefault(qid, {})[f"{alias}_{col}"] = sql_expr
    return by_query


CHART_COL_EXPR: dict[str, dict[str, str]] = _build_chart_col_expr()


def get_groupby_columns(query_id: str) -> list[str]:
    """Return the prefixed column names available for group-by for *query_id*.

    Raises ``KeyError`` for an unknown query id.
    """
    return list(CHART_COL_EXPR[query_id])


def get_distinct_values(
    db: Session,
    *,
    query_id: str,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
    columns: Optional[set[str]] = None,
) -> dict[str, list[str]]:
    """Return DISTINCT values for filter dropdown columns via SQL.

    *columns* limits which columns are fetched; if None all applicable columns
    are returned.  The result is keyed by the UI label (e.g. ``"Piecetype"``).
    """
    # Determine which table aliases apply
    if query_id == "q2":
        base = (
            "FROM tbllayers l "
            "INNER JOIN tblfragments f ON l.layerid = f.locationid "
            "INNER JOIN tblornaments o ON f.fragmentid = o.fragmentid"
        )
    elif query_id == "finds":
        base = (
            "FROM tblfinds fi "
            "INNER JOIN tbllayers l ON l.layerid = fi.layerid "
            "LEFT JOIN tblfragments f ON f.fragmentid = fi.fragmentid "
            "LEFT JOIN tblornaments o ON o.ornamentid = fi.ornamentid"
        )
    elif query_id == "finds_arch":
        base = "FROM finds fi"
    else:
        return {}

    where_sql, params = _build_where(
        query_id=query_id,
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
    )

    # Build list of (label, col_expr) pairs
    if columns:
        active = [
            (lbl, expr, qids)
            for lbl, expr, qids in _DISTINCT_COL_DEFS
            if lbl in columns and query_id in qids
        ]
    else:
        active = [
            (lbl, expr, qids)
            for lbl, expr, qids in _DISTINCT_COL_DEFS
            if query_id in qids
        ]

    result: dict[str, list[str]] = {}
    for label, col_expr, _ in active:
        # where_sql is either "" or "WHERE ..."; merge with the IS NOT NULL guard
        if where_sql:
            where_clause = f"{where_sql} AND {col_expr} IS NOT NULL"
        else:
            where_clause = f"WHERE {col_expr} IS NOT NULL"
        sql = f"SELECT DISTINCT {col_expr}::text AS v {base} {where_clause} ORDER BY v"
        rows = db.execute(text(sql), params).mappings().all()
        result[label] = [r["v"] for r in rows if r["v"]]

    return result


def get_layer_hierarchy(
    db: Session,
    *,
    query_id: str,
) -> dict[str, list[str]]:
    """Return the full site->sector->square->layer hierarchy as nested dicts.

    Returns:
        {
            "Site": {"A": {"Sector": ["S1", "S2"], ...}, ...},
            "Sector": {"S1": {"Square": ["Q1", "Q2"], ...}, ...},
            "Square": {"Q1": {"Layer": ["L1", "L2"], ...}, ...},
            "Layer": ["L1", "L2", ...],
            "all_sites": ["A", "B"],
            "all_sectors": ["S1", "S2"],
            "all_squares": ["Q1", "Q2"],
            "all_layers": ["L1", "L2"],
        }
    """
    if query_id == "q2":
        base = (
            "FROM tbllayers l "
            "INNER JOIN tblfragments f ON l.layerid = f.locationid "
            "INNER JOIN tblornaments o ON f.fragmentid = o.fragmentid"
        )
    elif query_id == "finds":
        base = (
            "FROM tblfinds fi "
            "INNER JOIN tbllayers l ON l.layerid = fi.layerid "
            "LEFT JOIN tblfragments f ON f.fragmentid = fi.fragmentid "
            "LEFT JOIN tblornaments o ON o.ornamentid = fi.ornamentid"
        )
    else:
        return {}

    # Fetch all combinations in one query
    id_col = "l.layerid"
    sql = f"""
        SELECT DISTINCT l.site, l.sector, l.square, l.layer, {id_col}
        {base}
        WHERE l.sector IS NOT NULL AND l.square IS NOT NULL
          AND l.layer IS NOT NULL
        ORDER BY l.sector, l.square, l.layer
    """
    rows = db.execute(text(sql)).mappings().all()

    hierarchy: dict[str, Any] = {}
    all_sites: set[str] = set()
    all_sectors: set[str] = set()
    all_squares: set[str] = set()
    all_layers: set[str] = set()

    for r in rows:
        site = r.get("site")
        sector = r["sector"]
        square = r["square"]
        layer = r["layer"]
        if site:
            all_sites.add(site)
        all_sectors.add(sector)
        all_squares.add(square)
        all_layers.add(layer)

        if site:
            if site not in hierarchy:
                hierarchy[site] = {}
            if sector not in hierarchy[site]:
                hierarchy[site][sector] = {}
            if square not in hierarchy[site][sector]:
                hierarchy[site][sector][square] = set()
            hierarchy[site][sector][square].add(layer)

    # Convert sets to sorted lists
    for site in hierarchy:
        for sector in hierarchy[site]:
            hierarchy[site][sector] = dict(
                (sq, sorted(layers)) for sq, layers in hierarchy[site][sector].items()
            )

    return {
        "hierarchy": hierarchy,
        "all_sites": sorted(all_sites),
        "all_sectors": sorted(all_sectors),
        "all_squares": sorted(all_squares),
        "all_layers": sorted(all_layers),
    }


def query_finds_archaeology(
    db: Session,
    *,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
) -> AnalyticsResult:
    """Archaeological finds: finds table only (location = fi.sector/square/layer_mechanical)."""
    select_cols = _model_select_list("fi_", "fi", Find)

    base = f"""
    SELECT
      {", ".join(select_cols)}
    FROM finds fi
    """

    where_sql, params = _build_where_finds(
        query_id="finds_arch",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        layer_filters=layer_filters,
        arch_filters=frag_filters,
    )

    sql = f"{base}\n{where_sql}\nORDER BY fi.findid DESC"
    count_sql = f"SELECT COUNT(*) FROM ({base}\n{where_sql}) x"

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    )
    return AnalyticsResult(items=items, total=total, columns=columns)


def _build_where_finds(
    *,
    query_id: str,
    site: Optional[str],
    sector: Optional[str],
    square: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    q: Optional[str],
    layer_filters: Optional[dict[str, Any]] = None,
    arch_filters: Optional[dict[str, Any]] = None,
) -> tuple[str, dict[str, Any]]:
    """Build WHERE clause for the finds_arch query (finds table + layers)."""
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if layer_filters:
        _add_ilike_filters(
            clauses,
            params,
            param_prefix="layer",
            label_to_col=_qualified("fi", FINDS_LOCATION_FILTER_COLS),
            filters=layer_filters,
        )
    else:
        # legacy site param has no finds column; ignore it
        if sector:
            clauses.append("fi.sector ILIKE :sector")
            params["sector"] = f"%{sector}%"
        if square:
            clauses.append("fi.square ILIKE :square")
            params["square"] = f"%{square}%"

    if date_from:
        clauses.append("fi.date_found >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("fi.date_found <= :date_to")
        params["date_to"] = date_to

    if q:
        params["q"] = f"%{q}%"
        clauses.append(
            "(COALESCE(fi.description,'') ILIKE :q "
            "OR COALESCE(fi.find_type,'') ILIKE :q "
            "OR COALESCE(fi.material,'') ILIKE :q "
            "OR COALESCE(fi.inv_no::text,'') ILIKE :q)"
        )

    if arch_filters:
        _apply_arch_filters(clauses, params, arch_filters)

    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


# ---------------------------------------------------------------------------
# Chart histogram aggregation (SQL-side GROUP BY)
# ---------------------------------------------------------------------------

# Subquery templates per query_id: the FROM/JOIN clause used by the full query.
# Each template projects bare column names (site, piecetype, ...). q2 also
# projects fragmentid + frag_count so histograms can count each fragment once.
_CHART_SUBQUERIES: dict[str, str] = {
    "q2": (
        "SELECT "
        "  l.site, l.sector, l.square, l.layer, "
        "  f.piecetype, f.technology, f.baking, f.primarycolor, f.covering, "
        "  f.surface, f.wallthickness, f.handletype, f.handlesize, "
        "  f.bottomtype, f.category, f.form, f.type, f.subtype, f.variant, "
        "  f.note, f.inventory, f.fragmentid, f.count AS frag_count, "
        "  o.primary_, o.secondary, o.tertiary, o.quarternary, "
        "  o.color1, o.encrustcolor1 "
        "FROM tbllayers l "
        "INNER JOIN tblfragments f ON l.layerid = f.locationid "
        "LEFT JOIN tblornaments o ON f.fragmentid = o.fragmentid"
    ),
    "finds_arch": (
        "SELECT "
        "  fi.sector, fi.square, fi.layer_mechanical, "
        "  fi.find_type, fi.material, fi.coin, fi.denomination, fi.mint, "
        "  fi.year, fi.inv_no, fi.depth_m, fi.context, "
        "  fi.findid, fi.description "
        "FROM finds fi"
    ),
}


# Contracted top-N display window for chart histograms (CHART.md section 6).
CHART_TOP_N = 30


def build_chart_histogram(
    db: Session,
    *,
    query_id: str,
    x_key: str,
    series_key: str | None,
    layer_filters: dict[str, Any] | None,
    frag_filters: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build an exact top-N histogram by aggregating in SQL.

    Returns a list of dicts, already in display (rank) order:
    - Single-axis: ``[{"bucket": str, "count": int}, ...]``
    - With series: ``[{"x_bucket": str, "series_bucket": str, "count": int}, ...]``

    The ``CHART_TOP_N`` x-groups are chosen by their deduplicated x-only total
    (the single-axis chart number; ties ordered by bucket); with a series, every series
    value of those groups is returned. q2 counts each fragment once per
    (x, series) bucket by its fragment count; finds_arch counts rows.

    Raises ``KeyError`` for an unknown query id, or for an x / series column
    that is not valid for *query_id*.
    """
    subquery_sql = _CHART_SUBQUERIES[query_id]
    cols = CHART_COL_EXPR[query_id]
    x_col = cols[x_key].split(".", 1)[1]
    s_col = None if series_key is None else cols[series_key].split(".", 1)[1]

    # WHERE runs against the subquery's bare column names ("site", "piecetype").
    clauses: list[str] = []
    params: dict[str, Any] = {"top_n": CHART_TOP_N}

    if layer_filters:
        _add_ilike_filters(
            clauses,
            params,
            param_prefix="layer",
            label_to_col=(
                FINDS_LOCATION_FILTER_COLS
                if query_id == "finds_arch"
                else LAYER_FILTER_COLS
            ),
            filters=layer_filters,
        )

    # Fragment + ornament field filters (q2 only)
    if frag_filters and query_id == "q2":
        _add_ilike_filters(
            clauses,
            params,
            param_prefix="frag",
            label_to_col={**FRAGMENT_FILTER_COLS, **ORNAMENT_FILTER_COLS},
            filters=frag_filters,
        )

    # Archaeological finds filters
    if frag_filters and query_id == "finds_arch":
        _add_ilike_filters(
            clauses,
            params,
            param_prefix="arch",
            label_to_col=ARCH_FILTER_COLS,
            filters=frag_filters,
        )

    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)

    # Ranking authority: x-only deduplicated totals (the number the single-axis
    # chart shows), shared by both modes so a series never re-inflates the rank.
    if query_id == "q2":
        # Each fragment counts once per bucket (ornament rows fan out the join).
        totals_sql = f"""
            SELECT CAST(x_val AS TEXT) AS x_bucket,
                   COALESCE(SUM(frag_count), 0) AS x_total
            FROM (
                SELECT DISTINCT fragmentid, frag_count, {x_col} AS x_val
                FROM ({subquery_sql}) sub
                {where_sql}
            ) d
            GROUP BY x_val
        """
    else:
        totals_sql = f"""
            SELECT CAST({x_col} AS TEXT) AS x_bucket, COUNT(*) AS x_total
            FROM ({subquery_sql}) sub
            {where_sql}
            GROUP BY {x_col}
        """
    top_sql = """
        top AS (
            SELECT x_bucket, x_total,
                   ROW_NUMBER() OVER (ORDER BY x_total DESC, x_bucket) AS x_rank
            FROM totals
        )
    """

    if s_col is None:
        sql = f"""
            WITH totals AS ({totals_sql}),
            {top_sql}
            SELECT x_bucket AS bucket, x_total AS cnt FROM top
            WHERE x_rank <= :top_n
            ORDER BY x_rank
        """
    else:
        if query_id == "q2":
            agg_sql = f"""
                SELECT CAST(x_val AS TEXT) AS x_bucket,
                       CAST(s_val AS TEXT) AS series_bucket,
                       COALESCE(SUM(frag_count), 0) AS cnt
                FROM (
                    SELECT DISTINCT fragmentid, frag_count,
                           {x_col} AS x_val, {s_col} AS s_val
                    FROM ({subquery_sql}) sub
                    {where_sql}
                ) d
                GROUP BY x_val, s_val
            """
        else:
            agg_sql = f"""
                SELECT CAST({x_col} AS TEXT) AS x_bucket,
                       CAST({s_col} AS TEXT) AS series_bucket,
                       COUNT(*) AS cnt
                FROM ({subquery_sql}) sub
                {where_sql}
                GROUP BY {x_col}, {s_col}
            """
        # Null-safe join: a NULL x value is a real group.
        sql = f"""
            WITH totals AS ({totals_sql}),
            {top_sql},
            agg AS ({agg_sql})
            SELECT a.x_bucket, a.series_bucket, a.cnt
            FROM agg a JOIN top t
              ON (a.x_bucket = t.x_bucket
                  OR (a.x_bucket IS NULL AND t.x_bucket IS NULL))
            WHERE t.x_rank <= :top_n
            ORDER BY t.x_rank, a.cnt DESC, a.series_bucket
        """

    rows = db.execute(text(sql), params).mappings().all()

    if s_col is None:
        return [{"bucket": r["bucket"], "count": int(r["cnt"])} for r in rows]
    return [
        {
            "x_bucket": r["x_bucket"],
            "series_bucket": r["series_bucket"],
            "count": int(r["cnt"]),
        }
        for r in rows
    ]
