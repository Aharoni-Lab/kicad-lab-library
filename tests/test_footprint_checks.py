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
    check_duplicate_pad_numbers,
    check_footprint_layers,
    check_footprint_pads,
    check_footprint_properties,
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


class TestDuplicatePadNumbers:
    def test_unique_pads_pass(self, tmp_path):
        fp_file = tmp_path / "good.kicad_mod"
        fp_file.write_text(
            '(footprint "Good"'
            '  (layer "F.Cu")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "2" smd rect (at 1 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_duplicate_pad_numbers(fp_file)
        assert result.passed

    def test_duplicate_pads_fail(self, tmp_path):
        fp_file = tmp_path / "bad.kicad_mod"
        fp_file.write_text(
            '(footprint "Bad"'
            '  (layer "F.Cu")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "1" smd rect (at 1 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_duplicate_pad_numbers(fp_file)
        assert not result.passed
        assert any("pad number '1'" in e for e in result.errors)

    def test_empty_pad_numbers_ignored(self, tmp_path):
        fp_file = tmp_path / "mount.kicad_mod"
        fp_file.write_text(
            '(footprint "Mount"'
            '  (layer "F.Cu")'
            '  (pad "" np_thru_hole circle (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "" np_thru_hole circle (at 1 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_duplicate_pad_numbers(fp_file)
        assert result.passed

    def test_duplicate_pads_allowed_for_connector_dir(self, tmp_path):
        """Duplicate pads in connector libraries should pass when configured."""
        from validator.config import LibraryRules
        connector_dir = tmp_path / "AharoniLab_Connector.pretty"
        connector_dir.mkdir()
        fp_file = connector_dir / "Coax.kicad_mod"
        fp_file.write_text(
            '(footprint "Coax"'
            '  (layer "F.Cu")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "1" smd rect (at 1 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "2" smd rect (at 0 1) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        rules = LibraryRules(allow_duplicate_pads=["AharoniLab_Connector"])
        result = check_duplicate_pad_numbers(fp_file, rules=rules)
        assert result.passed

    def test_duplicate_pads_still_fail_for_non_allowed_dir(self, tmp_path):
        """Duplicate pads in non-allowed dirs should still fail."""
        from validator.config import LibraryRules
        pkg_dir = tmp_path / "AharoniLab_Package_DFN_QFN.pretty"
        pkg_dir.mkdir()
        fp_file = pkg_dir / "bad.kicad_mod"
        fp_file.write_text(
            '(footprint "Bad"'
            '  (layer "F.Cu")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            '  (pad "1" smd rect (at 1 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        rules = LibraryRules(allow_duplicate_pads=["AharoniLab_Connector"])
        result = check_duplicate_pad_numbers(fp_file, rules=rules)
        assert not result.passed


class TestFootprintProperties:
    def test_valid_footprint_properties_pass(self, tmp_path, rules):
        fp_file = tmp_path / "good.kicad_mod"
        fp_file.write_text(
            '(footprint "Good"'
            '  (layer "F.Cu")'
            '  (property "Reference" "REF**")'
            '  (property "Value" "Good")'
            '  (property "Validated" "No")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_properties(fp_file, rules)
        assert result.passed

    def test_missing_reference_fails(self, tmp_path, rules):
        fp_file = tmp_path / "bad.kicad_mod"
        fp_file.write_text(
            '(footprint "Bad"'
            '  (layer "F.Cu")'
            '  (property "Value" "Bad")'
            '  (property "Validated" "No")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_properties(fp_file, rules)
        assert not result.passed
        assert any("Reference" in e for e in result.errors)

    def test_bad_validated_pattern_fails(self, tmp_path, rules):
        fp_file = tmp_path / "bad.kicad_mod"
        fp_file.write_text(
            '(footprint "Bad"'
            '  (layer "F.Cu")'
            '  (property "Reference" "REF**")'
            '  (property "Value" "Bad")'
            '  (property "Validated" "Maybe")'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_properties(fp_file, rules)
        assert not result.passed
        assert any("Validated" in e for e in result.errors)

    def test_no_fp_property_rules_passes(self, tmp_path):
        from validator.config import LibraryRules
        fp_file = tmp_path / "any.kicad_mod"
        fp_file.write_text('(footprint "Any" (layer "F.Cu"))')
        result = check_footprint_properties(fp_file, LibraryRules())
        assert result.passed


class TestAttributeAwareLayers:
    def test_smd_needs_front_copper(self, tmp_path, rules):
        fp_file = tmp_path / "smd.kicad_mod"
        fp_file.write_text(
            '(footprint "SMD"'
            '  (attr smd)'
            '  (layer "F.Cu")'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.CrtYd"))'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.Fab"))'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_layers(fp_file, rules)
        assert result.passed

    def test_through_hole_needs_back_copper(self, tmp_path, rules):
        fp_file = tmp_path / "th.kicad_mod"
        fp_file.write_text(
            '(footprint "TH"'
            '  (attr through_hole)'
            '  (layer "F.Cu")'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.CrtYd"))'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.Fab"))'
            '  (pad "1" thru_hole rect (at 0 0) (size 1 1) (layers "F.Cu" "B.Cu"))'
            ')'
        )
        result = check_footprint_layers(fp_file, rules)
        assert result.passed

    def test_through_hole_missing_back_copper_fails(self, tmp_path, rules):
        fp_file = tmp_path / "th_bad.kicad_mod"
        fp_file.write_text(
            '(footprint "THBad"'
            '  (attr through_hole)'
            '  (layer "F.Cu")'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.CrtYd"))'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.Fab"))'
            '  (pad "1" thru_hole rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_layers(fp_file, rules)
        assert not result.passed
        assert any("B.Cu" in e for e in result.errors)

    def test_unknown_attr_only_common(self, tmp_path, rules):
        fp_file = tmp_path / "unk.kicad_mod"
        fp_file.write_text(
            '(footprint "Unk"'
            '  (layer "F.Cu")'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.CrtYd"))'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.Fab"))'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_layers(fp_file, rules)
        assert result.passed

    def test_fallback_to_flat_list(self, tmp_path):
        from validator.config import LibraryRules
        rules_no_layer_rules = LibraryRules(
            footprint_required_layers=["F.Cu", "F.CrtYd"],
        )
        fp_file = tmp_path / "fb.kicad_mod"
        fp_file.write_text(
            '(footprint "FB"'
            '  (layer "F.Cu")'
            '  (fp_line (start 0 0) (end 1 1) (layer "F.CrtYd"))'
            '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu"))'
            ')'
        )
        result = check_footprint_layers(fp_file, rules_no_layer_rules)
        assert result.passed
