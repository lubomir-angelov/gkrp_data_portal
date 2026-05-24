"""Repository helpers for archaeology UI (parity-first, simple queries)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Text, desc, or_, select, text as sqlalchemy_text
from sqlalchemy.orm import Session

from gkrp_data_portal.models.archaeology import Find, Tbllayer, Tblfragment, Tblornament


@dataclass(frozen=True)
class SearchResult:
    """Generic result used by list pages."""

    items: list
    total: int


def column_distinct(db: Session, model, column_name: str) -> list[str]:
    col = getattr(model, column_name)
    stmt = select(col).distinct().where(col.isnot(None)).order_by(col)
    return [str(r) for r in db.execute(stmt).scalars().all() if r is not None]


def _apply_filters(stmt, model, filters: dict[str, list[str]] | None):
    if not filters:
        return stmt
    for col_name, vals in filters.items():
        if vals:
            col = getattr(model, col_name)
            stmt = stmt.where(col.cast(Text).in_([str(v) for v in vals]))
    return stmt


def list_layers(
    db: Session,
    q: str | None = None,
    limit: int = 200,
    filters: dict[str, list[str]] | None = None,
) -> SearchResult:
    stmt = select(Tbllayer)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Tbllayer.site.ilike(like),
                Tbllayer.sector.ilike(like),
                Tbllayer.square.ilike(like),
                Tbllayer.layername.ilike(like),
                Tbllayer.layer.ilike(like),
                Tbllayer.context.ilike(like),
                Tbllayer.layertype.ilike(like),
                Tbllayer.level.ilike(like),
                Tbllayer.structure.ilike(like),
                Tbllayer.color1.ilike(like),
                Tbllayer.color2.ilike(like),
            )
        )
    stmt = _apply_filters(stmt, Tbllayer, filters)
    stmt = stmt.order_by(desc(Tbllayer.layerid)).limit(limit)
    items = db.execute(stmt).scalars().all()
    return SearchResult(items=items, total=len(items))


def list_fragments(
    db: Session,
    q: str | None = None,
    limit: int = 300,
    filters: dict[str, list[str]] | None = None,
) -> SearchResult:
    stmt = select(Tblfragment)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Tblfragment.inventory.ilike(like),
                Tblfragment.note.ilike(like),
                Tblfragment.piecetype.cast(Text).ilike(like),
                Tblfragment.fragmenttype.cast(Text).ilike(like),
                Tblfragment.technology.cast(Text).ilike(like),
                Tblfragment.baking.cast(Text).ilike(like),
                Tblfragment.primarycolor.cast(Text).ilike(like),
                Tblfragment.secondarycolor.cast(Text).ilike(like),
                Tblfragment.image_url.ilike(like),
            )
        )
    stmt = _apply_filters(stmt, Tblfragment, filters)
    stmt = stmt.order_by(desc(Tblfragment.fragmentid)).limit(limit)
    items = db.execute(stmt).scalars().all()
    return SearchResult(items=items, total=len(items))


def list_ornaments(
    db: Session,
    q: str | None = None,
    limit: int = 400,
    filters: dict[str, list[str]] | None = None,
) -> SearchResult:
    stmt = select(Tblornament)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Tblornament.location.ilike(like),
                Tblornament.primary_.cast(Text).ilike(like),
                Tblornament.secondary.cast(Text).ilike(like),
                Tblornament.tertiary.cast(Text).ilike(like),
                Tblornament.color1.cast(Text).ilike(like),
                Tblornament.color2.cast(Text).ilike(like),
                Tblornament.encrustcolor1.cast(Text).ilike(like),
                Tblornament.encrustcolor2.cast(Text).ilike(like),
            )
        )
    stmt = _apply_filters(stmt, Tblornament, filters)
    stmt = stmt.order_by(desc(Tblornament.ornamentid)).limit(limit)
    items = db.execute(stmt).scalars().all()
    return SearchResult(items=items, total=len(items))


def most_recent_layer_id(db: Session) -> Optional[int]:
    stmt = select(Tbllayer.layerid).order_by(desc(Tbllayer.layerid)).limit(1)
    return db.execute(stmt).scalar_one_or_none()


def most_recent_fragment_id(db: Session) -> Optional[int]:
    stmt = (
        select(Tblfragment.fragmentid).order_by(desc(Tblfragment.fragmentid)).limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def layer_choices(db: Session, limit: int = 200) -> list[tuple[int, str]]:
    """Return list of (layerid, label) for dropdown."""
    stmt = select(Tbllayer).order_by(desc(Tbllayer.layerid)).limit(limit)
    items = db.execute(stmt).scalars().all()
    out: list[tuple[int, str]] = []
    for r in items:
        label = f"{r.layerid} | {r.site or ''}/{r.sector or ''}/{r.square or ''} | {r.layername or r.layer or ''}"
        out.append((r.layerid, label))
    return out


def fragment_choices(db: Session, limit: int = 300) -> list[tuple[int, str]]:
    stmt = select(Tblfragment).order_by(desc(Tblfragment.fragmentid)).limit(limit)
    items = db.execute(stmt).scalars().all()
    out: list[tuple[int, str]] = []
    for r in items:
        label = f"{r.fragmentid} | loc={r.locationid or ''} | {r.piecetype or ''} | {r.inventory or ''}"
        out.append((r.fragmentid, label))
    return out


def list_finds(
    db: Session,
    q: str | None = None,
    limit: int = 300,
    filters: dict[str, list[str]] | None = None,
) -> SearchResult:
    stmt = select(Find)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Find.description.ilike(like),
                Find.find_type.ilike(like),
                Find.material.ilike(like),
                Find.inv_no.cast(sqlalchemy_text).ilike(like),
                Find.coin.ilike(like),
                Find.mint.ilike(like),
                Find.denomination.ilike(like),
                Find.context.ilike(like),
                Find.depth_m.ilike(like),
                Find.coord_north_m.ilike(like),
                Find.coord_east_m.ilike(like),
                Find.photo.ilike(like),
                Find.drw_link.ilike(like),
            )
        )
    stmt = _apply_filters(stmt, Find, filters)
    stmt = stmt.order_by(desc(Find.findid)).limit(limit)
    items = db.execute(stmt).scalars().all()
    return SearchResult(items=items, total=len(items))
