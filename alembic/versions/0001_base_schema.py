"""Base schema (legacy ceramics tables).

Revision ID: 0001_base_schema
Revises: 
Create Date: 2026-01-18

This revision creates the initial database schema based on the legacy ceramics
application, excluding later extensions (auth, image URLs, finds).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

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


# revision identifiers, used by Alembic.
revision = "0001_base_schema"
down_revision = None
branch_labels = None
depends_on = None


def _in_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    # --- tbllayers ---
    op.create_table(
        "tbllayers",
        sa.Column("layerid", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("layertype", sa.Text(), nullable=True),
        sa.Column("layername", sa.Text(), nullable=True),
        sa.Column("site", sa.Text(), nullable=True),
        sa.Column("sector", sa.Text(), nullable=True),
        sa.Column("square", sa.Text(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("layer", sa.Text(), nullable=True),
        sa.Column("stratum", sa.Text(), nullable=True),
        sa.Column("parentid", sa.Integer(), nullable=True),
        sa.Column("level", sa.Text(), nullable=True),
        sa.Column("structure", sa.Text(), nullable=True),
        sa.Column("includes", sa.Text(), nullable=True),
        sa.Column("color1", sa.Text(), nullable=True),
        sa.Column("color2", sa.Text(), nullable=True),
        sa.Column("photos", sa.LargeBinary(), nullable=True),
        sa.Column("drawings", sa.LargeBinary(), nullable=True),
        sa.Column("handfragments", sa.Integer(), nullable=True),
        sa.Column("wheelfragment", sa.Integer(), nullable=True),
        sa.Column("recordenteredby", sa.Text(), nullable=True),
        sa.Column(
            "recordenteredon",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("recordcreatedby", sa.Text(), nullable=True),
        sa.Column("recordcreatedon", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("akb_num", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            f"layertype IN ({_in_list(LAYER_TYPE_VALUES)})",
            name="layertype_allowed",
        ),
        sa.CheckConstraint(
            f"color1 IN ({_in_list(COLOR_VALUES)})",
            name="color1_allowed",
        ),
        sa.CheckConstraint(
            f"color2 IN ({_in_list(COLOR_VALUES)})",
            name="color2_allowed",
        ),
    )

    # --- tblfragments ---
    op.create_table(
        "tblfragments",
        sa.Column(
            "fragmentid",
            sa.Integer(),
            sa.Identity(start=19304),
            primary_key=True,
        ),
        sa.Column(
            "locationid",
            sa.Integer(),
            sa.ForeignKey("tbllayers.layerid", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("fragmenttype", sa.Text(), nullable=True),
        sa.Column("technology", sa.Text(), nullable=True),
        sa.Column("baking", sa.Text(), nullable=True),
        sa.Column("fract", sa.Text(), nullable=True),
        sa.Column("primarycolor", sa.Text(), nullable=True),
        sa.Column("secondarycolor", sa.Text(), nullable=True),
        sa.Column("covering", sa.Text(), nullable=True),
        sa.Column("includesconc", sa.Text(), nullable=True),
        sa.Column("includessize", sa.Text(), nullable=True),
        sa.Column("surface", sa.Text(), nullable=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("onepot", sa.Text(), nullable=True),
        sa.Column("piecetype", sa.Text(), nullable=False),
        sa.Column("wallthickness", sa.Text(), nullable=True),
        sa.Column("handlesize", sa.Text(), nullable=True),
        sa.Column("handletype", sa.String(length=5), nullable=True),
        sa.Column("dishsize", sa.Text(), nullable=True),
        sa.Column("bottomtype", sa.Text(), nullable=True),
        sa.Column("outline", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=5), nullable=True),
        sa.Column("form", sa.String(length=5), nullable=True),
        sa.Column("type", sa.Integer(), nullable=True),
        sa.Column("subtype", sa.String(length=1), nullable=True),
        sa.Column("variant", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("inventory", sa.Text(), nullable=True),
        sa.Column("recordenteredby", sa.Text(), nullable=True),
        sa.Column(
            "recordenteredon",
            sa.String(length=50),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.CheckConstraint(
            f"fragmenttype IN ({_in_list(FRAGMENTTYPE_VALUES)})",
            name="fragmenttype_allowed",
        ),
        sa.CheckConstraint(
            f"technology IN ({_in_list(TECHNOLOGY_VALUES)})",
            name="technology_allowed",
        ),
        sa.CheckConstraint(
            f"baking IN ({_in_list(BAKING_VALUES)})",
            name="baking_allowed",
        ),
        sa.CheckConstraint(
            f"fract IN ({_in_list(FRACT_VALUES)})",
            name="fract_allowed",
        ),
        sa.CheckConstraint(
            f"primarycolor IN ({_in_list(COLOR_VALUES)})",
            name="primarycolor_allowed",
        ),
        sa.CheckConstraint(
            f"secondarycolor IN ({_in_list(COLOR_VALUES)})",
            name="secondarycolor_allowed",
        ),
        sa.CheckConstraint(
            f"covering IN ({_in_list(COVERING_VALUES)})",
            name="covering_allowed",
        ),
        sa.CheckConstraint(
            f"includesconc IN ({_in_list(INCLUDESCONC_VALUES)})",
            name="includesconc_allowed",
        ),
        sa.CheckConstraint(
            f"includessize IN ({_in_list(INCLUDESSIZE_VALUES)})",
            name="includessize_allowed",
        ),
        sa.CheckConstraint(
            f"surface IN ({_in_list(SURFACE_VALUES)})",
            name="surface_allowed",
        ),
        sa.CheckConstraint(
            f"onepot IN ({_in_list(ONEPOT_VALUES)})",
            name="onepot_allowed",
        ),
        sa.CheckConstraint(
            f"piecetype IN ({_in_list(PIECETYPE_VALUES)})",
            name="piecetype_allowed",
        ),
        sa.CheckConstraint(
            f"wallthickness IN ({_in_list(WALLTHICKNESS_VALUES)})",
            name="wallthickness_allowed",
        ),
        sa.CheckConstraint(
            f"handlesize IN ({_in_list(HANDLESIZE_VALUES)})",
            name="handlesize_allowed",
        ),
        sa.CheckConstraint(
            f"dishsize IN ({_in_list(DISHSIZE_VALUES)})",
            name="dishsize_allowed",
        ),
        sa.CheckConstraint(
            f"bottomtype IN ({_in_list(BOTTOMTYPE_VALUES)})",
            name="bottomtype_allowed",
        ),
        sa.CheckConstraint(
            f"outline IN ({_in_list(OUTLINE_VALUES)})",
            name="outline_allowed",
        ),
    )

    # --- tbllayerincludes ---
    op.create_table(
        "tbllayerincludes",
        sa.Column("includeid", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "locationid",
            sa.Integer(),
            sa.ForeignKey("tbllayers.layerid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("includetype", sa.Text(), nullable=True),
        sa.Column("includetext", sa.Text(), nullable=True),
        sa.Column("includesize", sa.Text(), nullable=True),
        sa.Column("includeconc", sa.Text(), nullable=True),
        sa.Column(
            "recordenteredon",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            f"includetype IN ({_in_list(INCLUDETYPE_VALUES)})",
            name="includetype_allowed",
        ),
        sa.CheckConstraint(
            f"includesize IN ({_in_list(INCLUDESIZE_VALUES)})",
            name="includesize_allowed",
        ),
        sa.CheckConstraint(
            f"includeconc IN ({_in_list(INCLUDECONC_VALUES)})",
            name="includeconc_allowed",
        ),
    )

    # --- tblpok ---
    op.create_table(
        "tblpok",
        sa.Column("pokid", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "locationid",
            sa.Integer(),
            sa.ForeignKey("tbllayers.layerid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Numeric(6, 3), nullable=True),
        sa.Column("sok_weight", sa.Numeric(6, 3), nullable=True),
        sa.Column(
            "recordenteredon",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # --- tblornaments ---
    op.create_table(
        "tblornaments",
        sa.Column("ornamentid", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "fragmentid",
            sa.Integer(),
            sa.ForeignKey("tblfragments.fragmentid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("relationship", sa.Text(), nullable=True),
        sa.Column("onornament", sa.Integer(), nullable=True),
        sa.Column("encrustcolor1", sa.String(length=10), nullable=True),
        sa.Column("encrustcolor2", sa.String(length=10), nullable=True),
        sa.Column("primary_", sa.Text(), nullable=True),
        sa.Column("secondary", sa.Text(), nullable=True),
        sa.Column("tertiary", sa.Text(), nullable=True),
        sa.Column("quarternary", sa.Integer(), nullable=True),
        sa.Column(
            "recordenteredon",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            f"primary_ IN ({_in_list(PRIMARY_ORN_VALUES)})",
            name="primary_allowed",
        ),
        sa.CheckConstraint(
            f"secondary IN ({_in_list(SECONDARY_ORN_VALUES)})",
            name="secondary_allowed",
        ),
        sa.CheckConstraint(
            f"tertiary IN ({_in_list(TERTIARY_ORN_VALUES)})",
            name="tertiary_allowed",
        ),
    )

    # --- tblregistered (legacy) ---
    op.create_table(
        "tblregistered",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("username", sa.String(length=25), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )


def downgrade() -> None:
    op.drop_table("tblregistered")
    op.drop_table("tblornaments")
    op.drop_table("tblpok")
    op.drop_table("tbllayerincludes")
    op.drop_table("tblfragments")
    op.drop_table("tbllayers")
