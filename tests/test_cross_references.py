"""Tests for cross-reference validation between symbols and footprints.

These tests ensure:
- If a symbol's Footprint property is non-empty, the referenced footprint
  must exist in the repo as footprints/<LibName>.pretty/<FootprintName>.kicad_mod
- Symbols with empty Footprint are allowed (generic symbols)
"""
from __future__ import annotations

from pathlib import Path

from validate import check_footprint_references, parse_kicad_sym


class TestFootprintCrossReference:
    def test_empty_footprint_is_allowed(self, fixtures_dir):
        """Symbols with empty Footprint should pass (generic symbols)."""
        result = check_footprint_references(
            fixtures_dir / "valid_symbol.kicad_sym",
            fixtures_dir.parent,  # repo_root (won't matter since footprint is empty)
        )
        assert result.passed

    def test_valid_footprint_reference(self, tmp_path):
        """Symbol referencing an existing footprint should pass."""
        # Create a minimal symbol file with a footprint reference
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        sym_file = sym_dir / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "C_100nF"'
            '  (property "Reference" "C")'
            '  (property "Value" "100nF")'
            '  (property "Footprint" "AharoniLab_Capacitor_SMD:C_0805_2012Metric")'
            '  (property "Datasheet" "https://example.com")'
            '  (property "Description" "Cap")'
            '  (property "Validated" "No")'
            '  (property "ki_keywords" "cap")'
            '))'
        )
        # Create the referenced footprint
        fp_dir = tmp_path / "footprints" / "AharoniLab_Capacitor_SMD.pretty"
        fp_dir.mkdir(parents=True)
        (fp_dir / "C_0805_2012Metric.kicad_mod").write_text("(footprint)")

        result = check_footprint_references(sym_file, tmp_path)
        assert result.passed

    def test_missing_footprint_fails(self, tmp_path):
        """Symbol referencing a non-existent footprint should fail."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        sym_file = sym_dir / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "C_100nF"'
            '  (property "Reference" "C")'
            '  (property "Value" "100nF")'
            '  (property "Footprint" "AharoniLab_Capacitor_SMD:C_0805_2012Metric")'
            '  (property "Datasheet" "https://example.com")'
            '  (property "Description" "Cap")'
            '  (property "Validated" "No")'
            '  (property "ki_keywords" "cap")'
            '))'
        )
        # Don't create the footprint directory
        (tmp_path / "footprints").mkdir()

        result = check_footprint_references(sym_file, tmp_path)
        assert not result.passed
        assert any("C_0805_2012Metric" in e for e in result.errors)

    def test_missing_footprint_library_fails(self, tmp_path):
        """Symbol referencing a non-existent footprint library should fail."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        sym_file = sym_dir / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "C_100nF"'
            '  (property "Reference" "C")'
            '  (property "Value" "100nF")'
            '  (property "Footprint" "AharoniLab_NoSuchLib:SomePart")'
            '  (property "Datasheet" "https://example.com")'
            '  (property "Description" "Cap")'
            '  (property "Validated" "No")'
            '  (property "ki_keywords" "cap")'
            '))'
        )
        (tmp_path / "footprints").mkdir()

        result = check_footprint_references(sym_file, tmp_path)
        assert not result.passed

    def test_invalid_footprint_format_fails(self, tmp_path):
        """Footprint value without colon separator should fail."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        sym_file = sym_dir / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "C_100nF"'
            '  (property "Reference" "C")'
            '  (property "Value" "100nF")'
            '  (property "Footprint" "NoColonHere")'
            '  (property "Datasheet" "https://example.com")'
            '  (property "Description" "Cap")'
            '  (property "Validated" "No")'
            '  (property "ki_keywords" "cap")'
            '))'
        )
        (tmp_path / "footprints").mkdir()

        result = check_footprint_references(sym_file, tmp_path)
        assert not result.passed
        assert any("format" in e.lower() for e in result.errors)
