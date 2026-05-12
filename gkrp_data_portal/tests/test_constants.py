"""Tests for gkrp_data_portal.models.constants."""

from __future__ import annotations

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
    USER_ROLE_VALUES,
    WALLTHICKNESS_VALUES,
)


class TestConstants:
    def test_user_role_values_contains_expected_roles(self):
        assert "admin" in USER_ROLE_VALUES
        assert "user" in USER_ROLE_VALUES

    def test_layer_type_values_contains_expected(self):
        assert "механичен" in LAYER_TYPE_VALUES
        assert "контекст" in LAYER_TYPE_VALUES
        assert "" in LAYER_TYPE_VALUES

    def test_color_values_contains_expected(self):
        assert "бял" in COLOR_VALUES
        assert "червен" in COLOR_VALUES
        assert "" in COLOR_VALUES

    def test_fragmenttype_values(self):
        assert "1" in FRAGMENTTYPE_VALUES
        assert "2" in FRAGMENTTYPE_VALUES
        assert "" in FRAGMENTTYPE_VALUES

    def test_technology_values(self):
        assert "1" in TECHNOLOGY_VALUES
        assert "2" in TECHNOLOGY_VALUES
        assert "2А" in TECHNOLOGY_VALUES
        assert "2Б" in TECHNOLOGY_VALUES

    def test_baking_values(self):
        assert "Р" in BAKING_VALUES
        assert "Н" in BAKING_VALUES

    def test_fract_values(self):
        assert "1" in FRACT_VALUES
        assert "3" in FRACT_VALUES

    def test_covering_values(self):
        assert "да" in COVERING_VALUES
        assert "не" in COVERING_VALUES
        assert "Ф1" in COVERING_VALUES
        assert "Ф2" in COVERING_VALUES

    def test_includesconc_values(self):
        assert "+" in INCLUDESCONC_VALUES
        assert "-" in INCLUDESCONC_VALUES

    def test_includessize_values(self):
        assert "М" in INCLUDESSIZE_VALUES
        assert "С" in INCLUDESSIZE_VALUES
        assert "Г" in INCLUDESSIZE_VALUES

    def test_surface_values(self):
        assert "А" in SURFACE_VALUES
        assert "Б" in SURFACE_VALUES
        assert "В" in SURFACE_VALUES
        assert "В1" in SURFACE_VALUES
        assert "В2" in SURFACE_VALUES

    def test_onepot_values(self):
        assert "да" in ONEPOT_VALUES
        assert "не" in ONEPOT_VALUES

    def test_piecetype_values(self):
        assert "устие" in PIECETYPE_VALUES
        assert "стена" in PIECETYPE_VALUES
        assert "дръжка" in PIECETYPE_VALUES
        assert "дъно" in PIECETYPE_VALUES

    def test_wallthickness_values(self):
        assert "М" in WALLTHICKNESS_VALUES
        assert "С" in WALLTHICKNESS_VALUES

    def test_handlesize_values(self):
        assert "М" in HANDLESIZE_VALUES

    def test_dishsize_values(self):
        assert "М" in DISHSIZE_VALUES

    def test_bottomtype_values(self):
        assert "А" in BOTTOMTYPE_VALUES
        assert "А1" in BOTTOMTYPE_VALUES
        assert "Б2" in BOTTOMTYPE_VALUES

    def test_outline_values(self):
        assert "1" in OUTLINE_VALUES
        assert "3" in OUTLINE_VALUES

    def test_includetype_values(self):
        assert "антропогенен" in INCLUDETYPE_VALUES
        assert "естествен" in INCLUDETYPE_VALUES

    def test_includesize_values(self):
        assert "малки" in INCLUDESIZE_VALUES
        assert "големи" in INCLUDESIZE_VALUES

    def test_includeconc_values(self):
        assert "ниска" in INCLUDECONC_VALUES
        assert "висока" in INCLUDECONC_VALUES

    def test_primary_orn_values(self):
        assert "А" in PRIMARY_ORN_VALUES
        assert "В" in PRIMARY_ORN_VALUES
        assert "" in PRIMARY_ORN_VALUES

    def test_secondary_orn_values(self):
        assert "I" in SECONDARY_ORN_VALUES
        assert "XVII" in SECONDARY_ORN_VALUES
        assert "" in SECONDARY_ORN_VALUES

    def test_tertiary_orn_values(self):
        assert "А" in TERTIARY_ORN_VALUES
        assert "А1" in TERTIARY_ORN_VALUES
        assert "Б2" in TERTIARY_ORN_VALUES
        assert "" in TERTIARY_ORN_VALUES

    def test_all_value_sets_are_tuples(self):
        assert isinstance(USER_ROLE_VALUES, tuple)
        assert isinstance(LAYER_TYPE_VALUES, tuple)
        assert isinstance(COLOR_VALUES, tuple)

    def test_all_value_sets_contain_empty_string(self):
        assert "" in LAYER_TYPE_VALUES
        assert "" in COLOR_VALUES
        assert "" in FRAGMENTTYPE_VALUES
        assert "" in TECHNOLOGY_VALUES
        assert "" in BAKING_VALUES
        assert "" in FRACT_VALUES
        assert "" in COVERING_VALUES
        assert "" in INCLUDESCONC_VALUES
        assert "" in INCLUDESSIZE_VALUES
        assert "" in SURFACE_VALUES
        assert "" in ONEPOT_VALUES
        assert "" in WALLTHICKNESS_VALUES
        assert "" in HANDLESIZE_VALUES
        assert "" in DISHSIZE_VALUES
        assert "" in BOTTOMTYPE_VALUES
        assert "" in OUTLINE_VALUES
        assert "" in INCLUDETYPE_VALUES
        assert "" in INCLUDESIZE_VALUES
        assert "" in INCLUDECONC_VALUES
        assert "" in PRIMARY_ORN_VALUES
        assert "" in SECONDARY_ORN_VALUES
        assert "" in TERTIARY_ORN_VALUES
