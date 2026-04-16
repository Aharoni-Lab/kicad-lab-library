"""Tests for cross-reference validation between symbols and footprints.

These tests ensure:
- If a symbol's Footprint property is non-empty, the referenced footprint
  must exist in the repo as footprints/<LibName>.pretty/<FootprintName>.kicad_mod
- Symbols with empty Footprint are allowed (generic symbols)
"""
from __future__ import annotations

from pathlib import Path

from validator.checks import check_footprint_references, check_pin_pad_cross_validation, parse_kicad_sym


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


class TestPinPadCrossValidation:
    def test_matching_pins_and_pads(self, tmp_path):
        """Symbol with 2 pins and footprint with 2 pads should pass."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "R_10k"'
            '  (property "Reference" "R")'
            '  (property "Value" "10k")'
            '  (property "Footprint" "AharoniLab_Test:R_0805")'
            '  (symbol "R_10k_1_1"'
            '    (pin passive line (at 0 5 270) (length 2.54) (name "1") (number "1"))'
            '    (pin passive line (at 0 -5 90) (length 2.54) (name "2") (number "2"))'
            '  )'
            '))'
        )
        fp_dir = tmp_path / "footprints" / "AharoniLab_Test.pretty"
        fp_dir.mkdir(parents=True)
        (fp_dir / "R_0805.kicad_mod").write_text(
            '(footprint "R_0805"'
            '  (layer "F.Cu")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "2" smd rect (at 1 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_pin_pad_cross_validation(sym_file, tmp_path)
        assert result.passed

    def test_fewer_pins_than_pads_passes(self, tmp_path):
        """Symbol with fewer pins than footprint pads should pass (extra NC/mounting pads)."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "R_10k"'
            '  (property "Reference" "R")'
            '  (property "Value" "10k")'
            '  (property "Footprint" "AharoniLab_Test:R_0805")'
            '  (symbol "R_10k_1_1"'
            '    (pin passive line (at 0 5 270) (length 2.54) (name "1") (number "1"))'
            '    (pin passive line (at 0 -5 90) (length 2.54) (name "2") (number "2"))'
            '  )'
            '))'
        )
        fp_dir = tmp_path / "footprints" / "AharoniLab_Test.pretty"
        fp_dir.mkdir(parents=True)
        (fp_dir / "R_0805.kicad_mod").write_text(
            '(footprint "R_0805"'
            '  (layer "F.Cu")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "2" smd rect (at 1 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "3" smd rect (at 2 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_pin_pad_cross_validation(sym_file, tmp_path)
        assert result.passed

    def test_more_pins_than_pads_fails(self, tmp_path):
        """Symbol with more pins than footprint pads should fail."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "R_10k"'
            '  (property "Reference" "R")'
            '  (property "Value" "10k")'
            '  (property "Footprint" "AharoniLab_Test:R_0805")'
            '  (symbol "R_10k_1_1"'
            '    (pin passive line (at 0 5 270) (length 2.54) (name "1") (number "1"))'
            '    (pin passive line (at 0 -5 90) (length 2.54) (name "2") (number "2"))'
            '    (pin passive line (at 0 -10 90) (length 2.54) (name "3") (number "3"))'
            '  )'
            '))'
        )
        fp_dir = tmp_path / "footprints" / "AharoniLab_Test.pretty"
        fp_dir.mkdir(parents=True)
        (fp_dir / "R_0805.kicad_mod").write_text(
            '(footprint "R_0805"'
            '  (layer "F.Cu")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "2" smd rect (at 1 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_pin_pad_cross_validation(sym_file, tmp_path)
        assert not result.passed
        assert any("3 pins" in e and "2 electrical pads" in e for e in result.errors)

    def test_empty_footprint_skips(self, tmp_path):
        """Symbol with empty footprint should skip cross-validation."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "X"'
            '  (property "Reference" "R")'
            '  (property "Value" "X")'
            '  (property "Footprint" "")'
            '))'
        )
        result = check_pin_pad_cross_validation(sym_file, tmp_path)
        assert result.passed

    def test_missing_footprint_skips(self, tmp_path):
        """Symbol pointing to non-existent footprint should skip (not fail)."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "X"'
            '  (property "Reference" "R")'
            '  (property "Value" "X")'
            '  (property "Footprint" "AharoniLab_Test:Missing")'
            '))'
        )
        (tmp_path / "footprints").mkdir()
        result = check_pin_pad_cross_validation(sym_file, tmp_path)
        assert result.passed

    def test_np_thru_hole_excluded(self, tmp_path):
        """Non-plated through-hole pads should not count as electrical pads."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "J1"'
            '  (property "Reference" "J")'
            '  (property "Value" "J1")'
            '  (property "Footprint" "AharoniLab_Test:J1")'
            '  (symbol "J1_1_1"'
            '    (pin passive line (at 0 5 270) (length 2.54) (name "1") (number "1"))'
            '    (pin passive line (at 0 -5 90) (length 2.54) (name "2") (number "2"))'
            '  )'
            '))'
        )
        fp_dir = tmp_path / "footprints" / "AharoniLab_Test.pretty"
        fp_dir.mkdir(parents=True)
        (fp_dir / "J1.kicad_mod").write_text(
            '(footprint "J1"'
            '  (layer "F.Cu")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "2" smd rect (at 1 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "" np_thru_hole circle (at 2 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_pin_pad_cross_validation(sym_file, tmp_path)
        assert result.passed

    def test_no_footprint_field_skips(self, tmp_path):
        """Symbol without Footprint property should skip."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "X"'
            '  (property "Reference" "R")'
            '  (property "Value" "X")'
            '))'
        )
        result = check_pin_pad_cross_validation(sym_file, tmp_path)
        assert result.passed
