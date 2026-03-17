"""Tests for YAML configuration loading.

These tests ensure:
- Valid config loads into correct dataclass fields
- Invalid regex patterns raise ValueError
- Missing required sections raise ValueError
- Optional fields have sensible defaults
- Categories with and without subcategories parse correctly
"""
from __future__ import annotations

import textwrap

import pytest
import yaml

from validator.config import (
    Category,
    LibraryRules,
    PinRange,
    PropertyRule,
    Subcategory,
    load_rules,
)


class TestLoadValidConfig:
    def test_load_valid_config(self, rules):
        """Should load library_rules.yaml into LibraryRules dataclass."""
        assert isinstance(rules, LibraryRules)
        assert rules.prefix == "AharoniLab_"
        assert rules.env_var == "AHARONI_LAB_KICAD_LIB"

    def test_global_properties_loaded(self, rules):
        """Global symbol properties should be populated from YAML."""
        assert "Reference" in rules.global_symbol_properties
        assert "Datasheet" in rules.global_symbol_properties
        assert "Validated" in rules.global_symbol_properties
        assert "ki_keywords" in rules.global_symbol_properties

    def test_datasheet_has_pattern(self, rules):
        """Datasheet property should have a URL pattern."""
        ds = rules.global_symbol_properties["Datasheet"]
        assert ds.pattern is not None
        assert ds.compiled_pattern is not None

    def test_validated_has_pattern(self, rules):
        """Validated property should have a Yes/No pattern."""
        val = rules.global_symbol_properties["Validated"]
        assert val.pattern == "^(Yes|No)$"

    def test_footprint_not_required(self, rules):
        """Footprint property should be optional (required=false)."""
        fp = rules.global_symbol_properties["Footprint"]
        assert fp.required is False

    def test_footprint_required_layers(self, rules):
        """Should load footprint required layers list."""
        assert "F.Cu" in rules.footprint_required_layers
        assert "F.CrtYd" in rules.footprint_required_layers
        assert "F.Fab" in rules.footprint_required_layers

    def test_naming_rules(self, rules):
        """Should load naming convention patterns."""
        assert rules.naming is not None
        assert rules.naming.symbol_file_pattern is not None
        assert rules.naming.footprint_dir_pattern is not None


class TestRegexPatterns:
    def test_valid_pattern_compiles(self):
        """Valid regex pattern should compile without error."""
        rule = PropertyRule(pattern="^(Yes|No)$")
        assert rule.compiled_pattern is not None

    def test_invalid_pattern_raises(self):
        """Invalid regex pattern should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid regex"):
            PropertyRule(pattern="[invalid")

    def test_no_pattern_gives_none(self):
        """PropertyRule without pattern should have None compiled_pattern."""
        rule = PropertyRule()
        assert rule.compiled_pattern is None


class TestMissingRequiredSection:
    def test_missing_global_symbol_properties(self, tmp_path):
        """Missing global_symbol_properties section should raise ValueError."""
        config = tmp_path / "bad.yaml"
        config.write_text("library:\n  prefix: Test\n")
        with pytest.raises(ValueError, match="global_symbol_properties"):
            load_rules(config)

    def test_empty_file_raises(self, tmp_path):
        """Empty YAML file should raise ValueError."""
        config = tmp_path / "empty.yaml"
        config.write_text("")
        with pytest.raises(ValueError):
            load_rules(config)


class TestDefaultValues:
    def test_property_rule_defaults(self):
        """PropertyRule should default to required=True, pattern=None."""
        rule = PropertyRule()
        assert rule.required is True
        assert rule.pattern is None

    def test_pin_range_defaults(self):
        """PinRange should default to None for both min and max."""
        pr = PinRange()
        assert pr.min is None
        assert pr.max is None


class TestCategoryWithSubcategories:
    def test_passive_has_subcategories(self, rules):
        """AharoniLab_Passive should have subcategories (R, C, L, D)."""
        passive = rules.categories["AharoniLab_Passive"]
        assert passive.subcategories is not None
        assert "resistor" in passive.subcategories
        assert "capacitor" in passive.subcategories
        assert "inductor" in passive.subcategories
        assert "diode" in passive.subcategories

    def test_subcategory_has_prefix_and_pins(self, rules):
        """Subcategories should have reference_prefix and pin ranges."""
        resistor = rules.categories["AharoniLab_Passive"].subcategories["resistor"]
        assert resistor.reference_prefix == "R"
        assert resistor.pins is not None
        assert resistor.pins.min == 2
        assert resistor.pins.max == 2

    def test_diode_allows_three_pins(self, rules):
        """Diode subcategory should allow up to 3 pins."""
        diode = rules.categories["AharoniLab_Passive"].subcategories["diode"]
        assert diode.pins.max == 3


class TestCategoryWithoutSubcategories:
    def test_connector_is_simple(self, rules):
        """AharoniLab_Connector should be a simple category (no subcategories)."""
        conn = rules.categories["AharoniLab_Connector"]
        assert conn.subcategories is None
        assert conn.reference_prefix == "J"
        assert conn.pins is not None
        assert conn.pins.min == 2
        assert conn.pins.max is None

    def test_mcu_has_minimum_pins(self, rules):
        """AharoniLab_MCU should require at least 8 pins."""
        mcu = rules.categories["AharoniLab_MCU"]
        assert mcu.reference_prefix == "U"
        assert mcu.pins.min == 8
