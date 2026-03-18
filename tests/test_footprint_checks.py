"""Tests for footprint-specific validation checks.

These tests ensure:
- Footprints are parsed correctly (layers, pads, properties)
- Required layers (F.Cu, F.CrtYd, F.Fab) are validated
- Footprints must have at least one pad
"""
from __future__ import annotations

from pathlib import Path

from validator.footprint_checks import (
    FootprintInfo,
    check_footprint_layers,
    check_footprint_pads,
    parse_kicad_mod,
)


class TestParseFootprint:
    def test_parse_valid_footprint(self, fixtures_dir):
        """Should parse a valid footprint and extract layers and pads."""
        info = parse_kicad_mod(fixtures_dir / "valid_footprint.kicad_mod")
        assert info.name == "TestSMD_0805"
        assert "F.Cu" in info.layers
        assert "F.CrtYd" in info.layers
        assert "F.Fab" in info.layers
        assert info.pad_count == 2

    def test_pad_count(self, fixtures_dir):
        """Should count pads correctly."""
        info = parse_kicad_mod(fixtures_dir / "valid_footprint.kicad_mod")
        assert info.pad_count == 2


class TestFootprintRequiredLayers:
    def test_footprint_has_required_layers_passes(self, fixtures_dir, rules):
        """Footprint with all required layers should pass."""
        result = check_footprint_layers(
            fixtures_dir / "valid_footprint.kicad_mod", rules
        )
        assert result.passed

    def test_footprint_missing_courtyard_fails(self, tmp_path, rules):
        """Footprint missing F.CrtYd should fail."""
        fp_file = tmp_path / "bad.kicad_mod"
        fp_file.write_text(
            '(footprint "NoCrtYd"'
            '  (layer "F.Cu")'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.Fab"))'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_layers(fp_file, rules)
        assert not result.passed
        assert any("F.CrtYd" in e for e in result.errors)

    def test_footprint_missing_fab_fails(self, tmp_path, rules):
        """Footprint missing F.Fab should fail."""
        fp_file = tmp_path / "bad.kicad_mod"
        fp_file.write_text(
            '(footprint "NoFab"'
            '  (layer "F.Cu")'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.CrtYd"))'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_layers(fp_file, rules)
        assert not result.passed
        assert any("F.Fab" in e for e in result.errors)


class TestFootprintPads:
    def test_footprint_has_pads(self, fixtures_dir):
        """Valid footprint should have pads."""
        result = check_footprint_pads(fixtures_dir / "valid_footprint.kicad_mod")
        assert result.passed

    def test_footprint_no_pads_fails(self, tmp_path):
        """Footprint without pads should fail."""
        fp_file = tmp_path / "no_pads.kicad_mod"
        fp_file.write_text(
            '(footprint "NoPads"'
            '  (layer "F.Cu")'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.Fab"))'
            ')'
        )
        result = check_footprint_pads(fp_file)
        assert not result.passed
        assert any("no pads" in e for e in result.errors)
