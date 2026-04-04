"""Analytics repository: predefined queries + safe filtering."""

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
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    layer: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    **_kwargs: Any,  # <-- ДОБАВИ ТОЗИ РЕД ТУК
) -> tuple[str, dict[str, Any]]:
    """Build a safe WHERE clause using only whitelisted filters."""
    clauses: list[str] = []
    params: dict[str, Any] = {}

    # Layer-scoped filters (Йерархия)
    if site:
        clauses.append("l.site = :site")
        params["site"] = site
    if sector:
        clauses.append("l.sector = :sector")
        params["sector"] = sector
    if square:
        clauses.append("l.square = :square")
        params["square"] = square
    if layer:
        clauses.append("l.layer = :layer")
        params["layer"] = layer

    if date_from:
        clauses.append("l.recordenteredon >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("l.recordenteredon <= :date_to")
        params["date_to"] = date_to

    # Free-text: търсене в други полета
    if q:
        params["q"] = f"%{q}%"
        if query_id in ("q1", "q2"):
            clauses.append("(COALESCE(f.inventory,'') ILIKE :q OR COALESCE(f.note,'') ILIKE :q OR COALESCE(f.piecetype,'') ILIKE :q)")
        elif query_id == "finds":
            clauses.append("(COALESCE(fi.description,'') ILIKE :q OR COALESCE(fi.findtype,'') ILIKE :q OR COALESCE(fi.inventory,'') ILIKE :q)")

    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


def _run_sql(db: Session, *, sql: str, params: dict[str, Any], limit: int, offset: int) -> list[RowMapping]:
    sql_paginated = f"{sql} LIMIT :limit OFFSET :offset"
    params2 = dict(params)
    params2["limit"] = limit
    params2["offset"] = offset
    return db.execute(text(sql_paginated), params2).mappings().all()


def _count_sql(db: Session, *, count_sql: str, params: dict[str, Any]) -> int:
    row = db.execute(text(count_sql), params).scalar_one()
    return int(row)


def query_q1_layers_fragments(db: Session, **kwargs) -> AnalyticsResult:
    select_cols = _model_select_list("l_", "l", Tbllayer) + _model_select_list("f_", "f", Tblfragment)
    base = f'SELECT {", ".join(select_cols)} FROM tbllayers l INNER JOIN tblfragments f ON l.layerid = f.locationid'
    where_sql, params = _build_where(query_id="q1", **kwargs)
    sql = f"{base}\n{where_sql}\nORDER BY l.layerid DESC, f.fragmentid DESC"
    count_sql = f"SELECT COUNT(*) FROM ({base}\n{where_sql}) x"
    rows = _run_sql(db, sql=sql, params=params, limit=kwargs.get('limit', 500), offset=kwargs.get('offset', 0))
    total = _count_sql(db, count_sql=count_sql, params=params)
    items = [dict(r) for r in rows]
    columns = list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    return AnalyticsResult(items=items, total=total, columns=columns)


def query_q2_layers_fragments_ornaments(db: Session, **kwargs) -> AnalyticsResult:
    select_cols = _model_select_list("l_", "l", Tbllayer) + _model_select_list("f_", "f", Tblfragment) + _model_select_list("o_", "o", Tblornament)
    base = f'SELECT {", ".join(select_cols)} FROM tbllayers l INNER JOIN tblfragments f ON l.layerid = f.locationid INNER JOIN tblornaments o ON f.fragmentid = o.fragmentid'
    where_sql, params = _build_where(query_id="q2", **kwargs)
    sql = f"{base}\n{where_sql}\nORDER BY l.layerid DESC, f.fragmentid DESC, o.ornamentid DESC"
    count_sql = f"SELECT COUNT(*) FROM ({base}\n{where_sql}) x"
    rows = _run_sql(db, sql=sql, params=params, limit=kwargs.get('limit', 500), offset=kwargs.get('offset', 0))
    total = _count_sql(db, count_sql=count_sql, params=params)
    items = [dict(r) for r in rows]
    columns = list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    return AnalyticsResult(items=items, total=total, columns=columns)


def query_finds(db: Session, **kwargs) -> AnalyticsResult:
    select_cols = _model_select_list("fi_", "fi", Tblfind) + _model_select_list("l_", "l", Tbllayer)
    base = 'SELECT ' + ", ".join(select_cols) + ' FROM tblfinds fi INNER JOIN tbllayers l ON l.layerid = fi.layerid'
    where_sql, params = _build_where(query_id="finds", **kwargs)
    sql = f"{base}\n{where_sql}\nORDER BY fi.findid DESC"
    count_sql = f"SELECT COUNT(*) FROM ({base}\n{where_sql}) x"
    rows = _run_sql(db, sql=sql, params=params, limit=kwargs.get('limit', 500), offset=kwargs.get('offset', 0))
    total = _count_sql(db, count_sql=count_sql, params=params)
    items = [dict(r) for r in rows]
    columns = list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    return AnalyticsResult(items=items, total=total, columns=columns)


def extract_image_urls(items: list[dict[str, Any]]) -> list[str]:
    urls, seen = [], set()
    for r in items:
        for key in ("f_image_url", "fi_image_url"):
            v = r.get(key)
            if isinstance(v, str) and v.strip() and v not in seen:
                seen.add(v); urls.append(v)
    return urls

# Универсална функция с йерархия
def get_distinct_values(db: Session, column_name: str, site=None, sector=None, square=None, **kwargs) -> list[str]:
    """Извлича уникални стойности за филтрите (Вероника)."""
    allowed = {"site", "sector", "square", "layer"}
    if column_name not in allowed:
        return []

    # Базови условия: колоната да не е празна
    clauses = [f"{column_name} IS NOT NULL", f"{column_name} != ''"]
    params = {}

    # Добавяме филтри само ако са избрани
    if site:
        clauses.append("site = :site")
        params["site"] = site
    if sector:
        clauses.append("sector = :sector")
        params["sector"] = sector
    if square:
        clauses.append("square = :square")
        params["square"] = square

    # Сглобяваме заявката
    where_str = " AND ".join(clauses)
    sql = f"SELECT DISTINCT {column_name} FROM tbllayers WHERE {where_str} ORDER BY {column_name} LIMIT 500"
    
    # ТОВА Е ЗА ТЕСТ: ще видиш SQL заявката в терминала си!
    print(f"DEBUG SQL: {sql} | PARAMS: {params}")
    
    try:
        results = db.execute(text(sql), params).all()
        return [str(r[0]) for r in results if r[0]]
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        return []

