"""Analytics repository: predefined queries + safe filtering.

Implements the two predefined queries (layers+fragments; layers+fragments+ornaments)
and a third selector for finds (tblfinds).

All result columns are prefixed to avoid collisions:
- l_<col> for tbllayers
- f_<col> for tblfragments
- o_<col> for tblornaments
- fi_<col> for tblfinds
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from gkrp_data_portal.models.archaeology import Tbllayer, Tblfragment, Tblornament, Tblfind


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


def _build_where(
    *,
    query_id: str,
    site: Optional[str],
    sector: Optional[str],
    square: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    q: Optional[str],
) -> tuple[str, dict[str, Any]]:
    """Build a safe WHERE clause using only whitelisted filters."""
    clauses: list[str] = []
    params: dict[str, Any] = {}

    # Layer-scoped filters (always safe; all queries include l alias)
    if site:
        clauses.append("l.site ILIKE :site")
        params["site"] = f"%{site}%"
    if sector:
        clauses.append("l.sector ILIKE :sector")
        params["sector"] = f"%{sector}%"
    if square:
        clauses.append("l.square ILIKE :square")
        params["square"] = f"%{square}%"

    if date_from:
        clauses.append("l.recordenteredon >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("l.recordenteredon <= :date_to")
        params["date_to"] = date_to

    # Free-text: differs slightly by query (which aliases exist)
    if q:
        params["q"] = f"%{q}%"
        if query_id in ("q1", "q2"):
            clauses.append(
                "(COALESCE(f.inventory,'') ILIKE :q OR COALESCE(f.note,'') ILIKE :q OR COALESCE(f.piecetype,'') ILIKE :q)"
            )
        elif query_id == "finds":
            clauses.append(
                "(COALESCE(fi.description,'') ILIKE :q OR COALESCE(fi.findtype,'') ILIKE :q OR COALESCE(fi.inventory,'') ILIKE :q)"
            )

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


def query_q1_layers_fragments(
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
) -> AnalyticsResult:
    """Filter #1: tbllayers INNER JOIN tblfragments."""
    select_cols = (
        _model_select_list("l_", "l", Tbllayer)
        + _model_select_list("f_", "f", Tblfragment)
    )
    base = f"""
    SELECT
      {", ".join(select_cols)}
    FROM tbllayers l
    INNER JOIN tblfragments f ON l.layerid = f.locationid
    """

    where_sql, params = _build_where(
        query_id="q1",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )

    sql = f"{base}\n{where_sql}\nORDER BY l.layerid DESC, f.fragmentid DESC"
    count_sql = f"SELECT COUNT(*) FROM ({base}\n{where_sql}) x"

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=params)

    items = [dict(r) for r in rows]
    columns = list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    return AnalyticsResult(items=items, total=total, columns=columns)


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
) -> AnalyticsResult:
    """Filter #2: tbllayers INNER JOIN tblfragments INNER JOIN tblornaments."""
    select_cols = (
        _model_select_list("l_", "l", Tbllayer)
        + _model_select_list("f_", "f", Tblfragment)
        + _model_select_list("o_", "o", Tblornament)
    )
    base = f"""
    SELECT
      {", ".join(select_cols)}
    FROM tbllayers l
    INNER JOIN tblfragments f ON l.layerid = f.locationid
    INNER JOIN tblornaments o ON f.fragmentid = o.fragmentid
    """

    where_sql, params = _build_where(
        query_id="q2",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )

    sql = f"{base}\n{where_sql}\nORDER BY l.layerid DESC, f.fragmentid DESC, o.ornamentid DESC"
    count_sql = f"SELECT COUNT(*) FROM ({base}\n{where_sql}) x"

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=params)

    items = [dict(r) for r in rows]
    columns = list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
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
) -> AnalyticsResult:
    """Finds selector: tblfinds tied to layers/fragments/ornaments (left joins)."""
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
    )

    sql = f"{base}\n{where_sql}\nORDER BY fi.findid DESC"
    count_sql = f"SELECT COUNT(*) FROM ({base}\n{where_sql}) x"

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=params)

    items = [dict(r) for r in rows]
    columns = list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    return AnalyticsResult(items=items, total=total, columns=columns)


def extract_image_urls(items: list[dict[str, Any]]) -> list[str]:
    """Collect unique image URLs from fragments/finds columns if present."""
    urls: list[str] = []
    seen: set[str] = set()

    for r in items:
        for key in ("f_image_url", "fi_image_url"):
            v = r.get(key)
            if isinstance(v, str) and v.strip():
                if v not in seen:
                    seen.add(v)
                    urls.append(v)

    return urls
