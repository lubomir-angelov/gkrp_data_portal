"""Database base classes and metadata.

This module defines the SQLAlchemy DeclarativeBase used by all ORM models.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.schema import MetaData


_NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base class for ORM models."""

    metadata = MetaData(naming_convention=_NAMING_CONVENTION)
