"""Archaeology domain ORM models.

These models are translated from the legacy ceramics application and are intended
as the schema source of truth.

Constraints are implemented with CHECK constraints for maintainability in
PostgreSQL.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,  # <-- Option 2: align with backup TIMESTAMP columns
    Identity,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from gkrp_data_portal.db.base import Base
from gkrp_data_portal.models.constants import (
    BAKING_VALUES,
    BOTTOMTYPE_VALUES,
    COLOR_VALUES,
    COVERING_VALUES,
    DISHSIZE_VALUES,
    FRACT_VALUES,
    FRAGMENTTYPE_VALUES,
    HANDLESIZE_VALUES,
    INCLUDESCONC_VALUES,
    INCLUDECONC_VALUES,
    INCLUDESIZE_VALUES,
    INCLUDETYPE_VALUES,
    INCLUDESSIZE_VALUES,
    LAYER_TYPE_VALUES,
    ONEPOT_VALUES,
    OUTLINE_VALUES,
    PIECETYPE_VALUES,
    PRIMARY_ORN_VALUES,
    SECONDARY_ORN_VALUES,
    SURFACE_VALUES,
    TECHNOLOGY_VALUES,
    TERTIARY_ORN_VALUES,
    WALLTHICKNESS_VALUES,
)


def _in_list(values: tuple[str, ...]) -> str:
    """Return a SQL IN-list with quoted literals.

    The ceramics value sets do not contain single quotes, so basic quoting is
    sufficient.
    """
    return ", ".join(f"'{v}'" for v in values)


class Tbllayer(Base):
    """Stratigraphic layer record."""

    __tablename__ = "tbllayers"
    __table_args__ = (
        CheckConstraint(
            f"layertype IN ({_in_list(LAYER_TYPE_VALUES)})",
            name="layertype_allowed",
        ),
        CheckConstraint(
            f"color1 IN ({_in_list(COLOR_VALUES)})",
            name="color1_allowed",
        ),
        CheckConstraint(
            f"color2 IN ({_in_list(COLOR_VALUES)})",
            name="color2_allowed",
        ),
    )

    layerid: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)

    layertype: Mapped[Optional[str]] = mapped_column(Text)
    layername: Mapped[Optional[str]] = mapped_column(Text)

    site: Mapped[Optional[str]] = mapped_column(Text)
    sector: Mapped[Optional[str]] = mapped_column(Text)
    square: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text)
    layer: Mapped[Optional[str]] = mapped_column(Text)
    stratum: Mapped[Optional[str]] = mapped_column(Text)
    parentid: Mapped[Optional[int]] = mapped_column(Integer)
    level: Mapped[Optional[str]] = mapped_column(Text)
    structure: Mapped[Optional[str]] = mapped_column(Text)
    includes: Mapped[Optional[str]] = mapped_column(Text)

    color1: Mapped[Optional[str]] = mapped_column(Text)
    color2: Mapped[Optional[str]] = mapped_column(Text)

    photos: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    drawings: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    handfragments: Mapped[Optional[int]] = mapped_column(Integer)
    wheelfragment: Mapped[Optional[int]] = mapped_column(Integer)

    recordenteredby: Mapped[Optional[str]] = mapped_column(Text)

    # Option 2: backup uses TIMESTAMP (not DATE). Keep CURRENT_TIMESTAMP default.
    recordenteredon: Mapped[object] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    recordcreatedby: Mapped[Optional[str]] = mapped_column(Text)
    recordcreatedon: Mapped[date] = mapped_column(Date, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text)
    akb_num: Mapped[Optional[int]] = mapped_column(Integer)

    fragments: Mapped[list["Tblfragment"]] = relationship(
        "Tblfragment",
        back_populates="layer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Tblfragment(Base):
    """Ceramic fragment record."""

    __tablename__ = "tblfragments"
    __table_args__ = (
        CheckConstraint(
            f"fragmenttype IN ({_in_list(FRAGMENTTYPE_VALUES)})",
            name="fragmenttype_allowed",
        ),
        CheckConstraint(
            f"technology IN ({_in_list(TECHNOLOGY_VALUES)})",
            name="technology_allowed",
        ),
        CheckConstraint(
            f"baking IN ({_in_list(BAKING_VALUES)})",
            name="baking_allowed",
        ),
        CheckConstraint(
            f"fract IN ({_in_list(FRACT_VALUES)})",
            name="fract_allowed",
        ),
        CheckConstraint(
            f"primarycolor IN ({_in_list(COLOR_VALUES)})",
            name="primarycolor_allowed",
        ),
        CheckConstraint(
            f"secondarycolor IN ({_in_list(COLOR_VALUES)})",
            name="secondarycolor_allowed",
        ),
        CheckConstraint(
            f"covering IN ({_in_list(COVERING_VALUES)})",
            name="covering_allowed",
        ),
        CheckConstraint(
            f"includesconc IN ({_in_list(INCLUDESCONC_VALUES)})",
            name="includesconc_allowed",
        ),
        CheckConstraint(
            f"includessize IN ({_in_list(INCLUDESSIZE_VALUES)})",
            name="includessize_allowed",
        ),
        CheckConstraint(
            f"surface IN ({_in_list(SURFACE_VALUES)})",
            name="surface_allowed",
        ),
        CheckConstraint(
            f"onepot IN ({_in_list(ONEPOT_VALUES)})",
            name="onepot_allowed",
        ),
        CheckConstraint(
            f"piecetype IN ({_in_list(PIECETYPE_VALUES)})",
            name="piecetype_allowed",
        ),
        CheckConstraint(
            f"wallthickness IN ({_in_list(WALLTHICKNESS_VALUES)})",
            name="wallthickness_allowed",
        ),
        CheckConstraint(
            f"handlesize IN ({_in_list(HANDLESIZE_VALUES)})",
            name="handlesize_allowed",
        ),
        CheckConstraint(
            f"dishsize IN ({_in_list(DISHSIZE_VALUES)})",
            name="dishsize_allowed",
        ),
        CheckConstraint(
            f"bottomtype IN ({_in_list(BOTTOMTYPE_VALUES)})",
            name="bottomtype_allowed",
        ),
        CheckConstraint(
            f"outline IN ({_in_list(OUTLINE_VALUES)})",
            name="outline_allowed",
        ),
    )

    fragmentid: Mapped[int] = mapped_column(Integer, Identity(start=19304), primary_key=True)

    locationid: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tbllayers.layerid", ondelete="SET NULL"),
        nullable=True,
    )

    fragmenttype: Mapped[Optional[str]] = mapped_column(Text)
    technology: Mapped[Optional[str]] = mapped_column(Text)
    baking: Mapped[Optional[str]] = mapped_column(Text)
    fract: Mapped[Optional[str]] = mapped_column(Text)
    primarycolor: Mapped[Optional[str]] = mapped_column(Text)
    secondarycolor: Mapped[Optional[str]] = mapped_column(Text)
    covering: Mapped[Optional[str]] = mapped_column(Text)
    includesconc: Mapped[Optional[str]] = mapped_column(Text)
    includessize: Mapped[Optional[str]] = mapped_column(Text)
    surface: Mapped[Optional[str]] = mapped_column(Text)

    count: Mapped[int] = mapped_column(Integer, nullable=False)
    onepot: Mapped[Optional[str]] = mapped_column(Text)
    piecetype: Mapped[str] = mapped_column(Text, nullable=False)

    wallthickness: Mapped[Optional[str]] = mapped_column(Text)
    handlesize: Mapped[Optional[str]] = mapped_column(Text)
    handletype: Mapped[Optional[str]] = mapped_column(String(5))

    dishsize: Mapped[Optional[str]] = mapped_column(Text)

    bottomtype: Mapped[Optional[str]] = mapped_column(Text)
    outline: Mapped[Optional[str]] = mapped_column(Text)

    category: Mapped[Optional[str]] = mapped_column(String(5))
    form: Mapped[Optional[str]] = mapped_column(String(5))
    type: Mapped[Optional[int]] = mapped_column(Integer)
    subtype: Mapped[Optional[str]] = mapped_column(String(1))
    variant: Mapped[Optional[int]] = mapped_column(Integer)

    # Option 2: columns present in backup but missing in initial model
    speed: Mapped[Optional[str]] = mapped_column(Text)
    includestype: Mapped[Optional[str]] = mapped_column(Text)

    topsize: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    necksize: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    bodysize: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    bottomsize: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    dishheight: Mapped[Optional[Decimal]] = mapped_column(Numeric)

    decoration: Mapped[Optional[str]] = mapped_column(Text)
    composition: Mapped[Optional[str]] = mapped_column(Text)
    parallels: Mapped[Optional[str]] = mapped_column(Text)

    # Option 2: bytea column present in backup
    image: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    note: Mapped[Optional[str]] = mapped_column(Text)
    inventory: Mapped[Optional[str]] = mapped_column(Text)

    recordenteredby: Mapped[Optional[str]] = mapped_column(Text)

    # Legacy schema uses a string defaulting to CURRENT_TIMESTAMP.
    recordenteredon: Mapped[Optional[str]] = mapped_column(
        String(50),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Added in a later migration.
    image_url: Mapped[Optional[str]] = mapped_column(String(2048))

    layer: Mapped[Optional["Tbllayer"]] = relationship(
        "Tbllayer",
        back_populates="fragments",
    )

    ornaments: Mapped[list["Tblornament"]] = relationship(
        "Tblornament",
        back_populates="fragment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Tbllayerinclude(Base):
    """Inclusions associated with a layer."""

    __tablename__ = "tbllayerincludes"
    __table_args__ = (
        CheckConstraint(
            f"includetype IN ({_in_list(INCLUDETYPE_VALUES)})",
            name="includetype_allowed",
        ),
        CheckConstraint(
            f"includesize IN ({_in_list(INCLUDESIZE_VALUES)})",
            name="includesize_allowed",
        ),
        CheckConstraint(
            f"includeconc IN ({_in_list(INCLUDECONC_VALUES)})",
            name="includeconc_allowed",
        ),
    )

    includeid: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)

    # Option 2: backup allows NULL
    locationid: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tbllayers.layerid", ondelete="CASCADE"),
        nullable=True,
    )

    includetype: Mapped[Optional[str]] = mapped_column(Text)
    includetext: Mapped[Optional[str]] = mapped_column(Text)
    includesize: Mapped[Optional[str]] = mapped_column(Text)
    includeconc: Mapped[Optional[str]] = mapped_column(Text)

    # Option 2: backup uses TIMESTAMP with now()
    recordenteredon: Mapped[object] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
    )


class Tblpok(Base):
    """POK data associated with a layer."""

    __tablename__ = "tblpok"

    pokid: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)

    # Option 2: backup allows NULL
    locationid: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tbllayers.layerid", ondelete="CASCADE"),
        nullable=True,
    )

    type: Mapped[Optional[str]] = mapped_column(Text)
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3))
    sok_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3))

    # Option 2: backup uses TIMESTAMP with now()
    recordenteredon: Mapped[object] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
    )


class Tblornament(Base):
    """Ornament record related to a fragment."""

    __tablename__ = "tblornaments"
    __table_args__ = (
        CheckConstraint(
            f"primary_ IN ({_in_list(PRIMARY_ORN_VALUES)})",
            name="primary_allowed",
        ),
        CheckConstraint(
            f"secondary IN ({_in_list(SECONDARY_ORN_VALUES)})",
            name="secondary_allowed",
        ),
        CheckConstraint(
            f"tertiary IN ({_in_list(TERTIARY_ORN_VALUES)})",
            name="tertiary_allowed",
        ),
    )

    ornamentid: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)

    # Option 2: backup allows NULL
    fragmentid: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tblfragments.fragmentid", ondelete="CASCADE"),
        nullable=True,
    )

    location: Mapped[Optional[str]] = mapped_column(Text)
    relationship_type: Mapped[Optional[str]] = mapped_column("relationship", Text)
    onornament: Mapped[Optional[int]] = mapped_column(Integer)

    # Option 2: columns present in backup but missing in initial model
    color1: Mapped[Optional[str]] = mapped_column(Text)
    color2: Mapped[Optional[str]] = mapped_column(Text)

    encrustcolor1: Mapped[Optional[str]] = mapped_column(String(10))
    encrustcolor2: Mapped[Optional[str]] = mapped_column(String(10))

    primary_: Mapped[Optional[str]] = mapped_column(Text)

    # Option 2: backup indicates varchar(5)
    secondary: Mapped[Optional[str]] = mapped_column(String(5))

    tertiary: Mapped[Optional[str]] = mapped_column(Text)
    quarternary: Mapped[Optional[int]] = mapped_column(Integer)

    # Option 2: backup uses TIMESTAMP with now()
    recordenteredon: Mapped[object] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
    )

    fragment: Mapped[Optional["Tblfragment"]] = relationship(
        "Tblfragment",
        back_populates="ornaments",
    )


class Tblfind(Base):
    """Finds table (находки)."""

    __tablename__ = "tblfinds"

    findid: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)

    layerid: Mapped[int] = mapped_column(ForeignKey("tbllayers.layerid"))
    fragmentid: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tblfragments.fragmentid"),
        nullable=True,
    )
    ornamentid: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tblornaments.ornamentid"),
        nullable=True,
    )

    findtype: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    inventory: Mapped[Optional[str]] = mapped_column(String(50))
    image_url: Mapped[Optional[str]] = mapped_column(String(2048))

    recordenteredby: Mapped[Optional[str]] = mapped_column(String(50))

    # Option 2: use TIMESTAMP with now() (align with analytics-friendly time)
    recordenteredon: Mapped[object] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
    )
