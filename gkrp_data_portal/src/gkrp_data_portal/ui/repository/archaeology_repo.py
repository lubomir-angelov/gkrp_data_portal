"""Repository helpers for archaeology UI (parity-first, simple queries)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from gkrp_data_portal.models.archaeology import Tbllayer, Tblfragment, Tblornament


@dataclass(frozen=True)
class SearchResult:
    """Generic result used by list pages."""
    items: list
    total: int


def list_layers(db: Session, q: str | None = None, limit: int = 200) -> SearchResult:
    stmt = select(Tbllayer).order_by(desc(Tbllayer.layerid)).limit(limit)
    if q:
        like = f"%{q.strip()}%"
        stmt = (
            select(Tbllayer)
            .where(
                or_(
                    Tbllayer.site.ilike(like),
                    Tbllayer.sector.ilike(like),
                    Tbllayer.square.ilike(like),
                    Tbllayer.layername.ilike(like),
                    Tbllayer.layer.ilike(like),
                    Tbllayer.context.ilike(like),
                )
            )
            .order_by(desc(Tbllayer.layerid))
            .limit(limit)
        )
    items = db.execute(stmt).scalars().all()
    return SearchResult(items=items, total=len(items))


def list_fragments(db: Session, q: str | None = None, limit: int = 300) -> SearchResult:
    stmt = select(Tblfragment).order_by(desc(Tblfragment.fragmentid)).limit(limit)
    if q:
        like = f"%{q.strip()}%"
        stmt = (
            select(Tblfragment)
            .where(
                or_(
                    Tblfragment.inventory.ilike(like),
                    Tblfragment.note.ilike(like),
                    Tblfragment.piecetype.ilike(like),
                    Tblfragment.fragmenttype.ilike(like),
                    Tblfragment.technology.ilike(like),
                )
            )
            .order_by(desc(Tblfragment.fragmentid))
            .limit(limit)
        )
    items = db.execute(stmt).scalars().all()
    return SearchResult(items=items, total=len(items))


def list_ornaments(db: Session, q: str | None = None, limit: int = 400) -> SearchResult:
    stmt = select(Tblornament).order_by(desc(Tblornament.ornamentid)).limit(limit)
    if q:
        like = f"%{q.strip()}%"
        stmt = (
            select(Tblornament)
            .where(
                or_(
                    Tblornament.location.ilike(like),
                    Tblornament.primary_.ilike(like),
                    Tblornament.secondary.ilike(like),
                    Tblornament.tertiary.ilike(like),
                )
            )
            .order_by(desc(Tblornament.ornamentid))
            .limit(limit)
        )
    items = db.execute(stmt).scalars().all()
    return SearchResult(items=items, total=len(items))


def most_recent_layer_id(db: Session) -> Optional[int]:
    stmt = select(Tbllayer.layerid).order_by(desc(Tbllayer.layerid)).limit(1)
    return db.execute(stmt).scalar_one_or_none()


def most_recent_fragment_id(db: Session) -> Optional[int]:
    stmt = select(Tblfragment.fragmentid).order_by(desc(Tblfragment.fragmentid)).limit(1)
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
