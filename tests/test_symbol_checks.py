"""Tests for lab-specific symbol property validation.

These tests encode our requirements:
- Every symbol MUST have a Datasheet property with a URL (not empty, not '~')
- Every symbol MUST have a Validated property set to 'Yes' or 'No'
- Malformed files must produce clear errors, not crash
- All validation is YAML-driven via library_rules.yaml
"""
from __future__ import annotations

from validator.checks import (
    check_pin_counts,
    check_reference_prefix,
    check_symbol_flags,
    check_symbol_properties,
    parse_kicad_sym,
)


class TestDatasheetProperty:
    def test_valid_symbol_has_datasheet_url(self, valid_symbol_path, rules):
        """Symbol with a valid Datasheet URL should pass."""
        result = check_symbol_properties(valid_symbol_path, rules)
        assert result.passed

    def test_missing_datasheet_passes(self, invalid_no_datasheet_path, rules):
        """Symbol without Datasheet property should pass (optional)."""
        result = check_symbol_properties(invalid_no_datasheet_path, rules)
        assert result.passed

    def test_empty_datasheet_passes(self, invalid_empty_datasheet_path, rules):
        """Symbol with empty Datasheet should pass (optional)."""
        result = check_symbol_properties(invalid_empty_datasheet_path, rules)
        assert result.passed

    def test_datasheet_url_pattern_enforced(self, tmp_path, rules):
        """Non-URL datasheet should fail pattern check."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "BadDS"'
            '  (property "Reference" "R")'
            '  (property "Value" "BadDS")'
            '  (property "Footprint" "")'
            '  (property "Datasheet" "not-a-url")'
            '  (property "Description" "Test")'
            '  (property "Validated" "No")'
            '  (property "ki_keywords" "test")'
            '))'
        )
        result = check_symbol_properties(sym_file, rules)
        assert not result.passed
        assert any("Datasheet" in e and "must match" in e for e in result.errors)


class TestValidatedProperty:
    def test_validated_yes_passes(self, valid_symbol_path, rules):
        """Symbol with Validated='Yes' should pass."""
        result = check_symbol_properties(valid_symbol_path, rules)
        assert result.passed

    def test_validated_no_passes(self, valid_symbol_unvalidated_path, rules):
        """Symbol with Validated='No' should pass (it's a valid state)."""
        result = check_symbol_properties(valid_symbol_unvalidated_path, rules)
        assert result.passed

    def test_missing_validated_fails(self, invalid_no_validated_path, rules):
        """Symbol without Validated property should fail."""
        result = check_symbol_properties(invalid_no_validated_path, rules)
        assert not result.passed
        assert any("Validated" in e for e in result.errors)

    def test_invalid_validated_value_fails(self, invalid_bad_validated_path, rules):
        """Symbol with Validated='Maybe' should fail."""
        result = check_symbol_properties(invalid_bad_validated_path, rules)
        assert not result.passed

    def test_validated_pattern_enforced(self, tmp_path, rules):
        """Bad Validated value should be caught by regex pattern."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "BadVal"'
            '  (property "Reference" "R")'
            '  (property "Value" "BadVal")'
            '  (property "Footprint" "")'
            '  (property "Datasheet" "https://example.com")'
            '  (property "Description" "Test")'
            '  (property "Validated" "Maybe")'
            '  (property "ki_keywords" "test")'
            '))'
        )
        result = check_symbol_properties(sym_file, rules)
        assert not result.passed
        assert any("Validated" in e for e in result.errors)


class TestReferenceProperty:
    def test_valid_symbol_has_reference(self, valid_symbol_path, rules):
        """Every symbol MUST have a Reference property."""
        result = check_symbol_properties(valid_symbol_path, rules)
        assert result.passed

    def test_missing_reference_fails(self, invalid_no_reference_path, rules):
        """Symbol without Reference property should fail validation."""
        result = check_symbol_properties(invalid_no_reference_path, rules)
        assert not result.passed
        assert any("Reference" in e for e in result.errors)


class TestDescriptionProperty:
    def test_valid_symbol_has_description(self, valid_symbol_path, rules):
        """Every symbol MUST have a Description property."""
        result = check_symbol_properties(valid_symbol_path, rules)
        assert result.passed

    def test_missing_description_fails(self, invalid_no_description_path, rules):
        """Symbol without Description property should fail validation."""
        result = check_symbol_properties(invalid_no_description_path, rules)
        assert not result.passed
        assert any("Description" in e for e in result.errors)


class TestKeywordsProperty:
    def test_valid_symbol_has_keywords(self, valid_symbol_path, rules):
        """Every symbol MUST have a ki_keywords property."""
        result = check_symbol_properties(valid_symbol_path, rules)
        assert result.passed

    def test_missing_keywords_fails(self, invalid_no_keywords_path, rules):
        """Symbol without ki_keywords property should fail validation."""
        result = check_symbol_properties(invalid_no_keywords_path, rules)
        assert not result.passed
        assert any("ki_keywords" in e for e in result.errors)


class TestMissingRequiredProperty:
    def test_missing_required_property_fails(self, tmp_path, rules):
        """Any missing required property should be caught generically."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "Minimal"'
            '  (property "Reference" "R")'
            '  (property "Value" "Minimal")'
            '))'
        )
        result = check_symbol_properties(sym_file, rules)
        assert not result.passed
        # Should report multiple missing properties
        assert len(result.errors) >= 3


class TestTildeHandling:
    def test_tilde_description_fails(self, tmp_path, rules):
        """Symbol with Description='~' should fail."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "TildeDesc"'
            '  (property "Reference" "R")(property "Value" "TildeDesc")'
            '  (property "Footprint" "")(property "Datasheet" "https://example.com")'
            '  (property "Description" "~")(property "Validated" "No")'
            '  (property "ki_keywords" "test")))')
        result = check_symbol_properties(sym_file, rules)
        assert not result.passed
        assert any("Description" in e for e in result.errors)

    def test_tilde_validated_fails(self, tmp_path, rules):
        """Symbol with Validated='~' should fail."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "TildeVal"'
            '  (property "Reference" "R")(property "Value" "TildeVal")'
            '  (property "Footprint" "")(property "Datasheet" "https://example.com")'
            '  (property "Description" "Test")(property "Validated" "~")'
            '  (property "ki_keywords" "test")))')
        result = check_symbol_properties(sym_file, rules)
        assert not result.passed

    def test_tilde_datasheet_passes(self, tmp_path, rules):
        """Datasheet='~' should pass (treated as empty, optional)."""
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "TildeDS"'
            '  (property "Reference" "R")(property "Value" "TildeDS")'
            '  (property "Footprint" "")(property "Datasheet" "~")'
            '  (property "Description" "Test")(property "Validated" "No")'
            '  (property "ki_keywords" "test")))')
        result = check_symbol_properties(sym_file, rules)
        assert result.passed


class TestManufacturerMPN:
    def test_symbol_without_mpn_passes(self, tmp_path, rules):
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "NoMPN" (property "Reference" "R")(property "Value" "NoMPN")(property "Footprint" "")(property "Datasheet" "https://example.com")(property "Description" "Test")(property "Validated" "No")(property "ki_keywords" "test")))')
        result = check_symbol_properties(sym_file, rules)
        assert result.passed

    def test_symbol_with_placeholder_mpn_fails(self, tmp_path, rules):
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "BadMPN" (property "Reference" "R")(property "Value" "BadMPN")(property "Footprint" "")(property "Datasheet" "https://example.com")(property "Description" "Test")(property "Validated" "No")(property "ki_keywords" "test")(property "MPN" "TBD")))')
        result = check_symbol_properties(sym_file, rules)
        assert not result.passed
        assert any("MPN" in e for e in result.errors)

    def test_symbol_with_na_mpn_fails(self, tmp_path, rules):
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "NAMPN" (property "Reference" "R")(property "Value" "NAMPN")(property "Footprint" "")(property "Datasheet" "https://example.com")(property "Description" "Test")(property "Validated" "No")(property "ki_keywords" "test")(property "MPN" "N/A")))')
        result = check_symbol_properties(sym_file, rules)
        assert not result.passed

    def test_symbol_with_valid_mpn_passes(self, tmp_path, rules):
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "GoodMPN" (property "Reference" "R")(property "Value" "GoodMPN")(property "Footprint" "")(property "Datasheet" "https://example.com")(property "Description" "Test")(property "Validated" "No")(property "ki_keywords" "test")(property "Manufacturer" "TI")(property "MPN" "LM1117-3.3")))')
        result = check_symbol_properties(sym_file, rules)
        assert result.passed


class TestSymbolParsing:
    def test_can_parse_valid_symbol(self, valid_symbol_path):
        """Should be able to parse a valid .kicad_sym file."""
        symbols = parse_kicad_sym(valid_symbol_path)
        assert len(symbols) > 0

    def test_malformed_file_reports_error(self, invalid_malformed_path, rules):
        """Malformed file should produce a clear error, not crash."""
        result = check_symbol_properties(invalid_malformed_path, rules)
        assert not result.passed
        assert any(
            "parse" in e.lower() or "format" in e.lower()
            for e in result.errors
        )

    def test_extracts_all_symbol_names(self, valid_symbol_path):
        """Should extract names of all symbols in a library file."""
        symbols = parse_kicad_sym(valid_symbol_path)
        for sym in symbols:
            assert sym.name

    def test_multi_symbol_library(self, valid_symbol_path):
        """Should parse symbols from a multi-symbol library file."""
        symbols = parse_kicad_sym(valid_symbol_path)
        assert len(symbols) >= 1
        for sym in symbols:
            assert sym.name

    def test_pin_count_extracted(self, valid_symbol_path):
        """Should count pins in parsed symbols."""
        symbols = parse_kicad_sym(valid_symbol_path)
        # TestResistor has 2 pins in its child symbol
        assert symbols[0].pin_count == 2


class TestReferencePrefix:
    def test_correct_reference_prefix_passes(self, tmp_path, rules):
        """Symbol with correct reference prefix for its category should pass."""
        sym_file = tmp_path / "AharoniLab_Connector.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "USB_C"'
            '  (property "Reference" "J")'
            '  (property "Value" "USB_C")'
            '))'
        )
        result = check_reference_prefix(sym_file, rules)
        assert result.passed

    def test_wrong_reference_prefix_fails(self, tmp_path, rules):
        """Symbol with wrong reference prefix should fail."""
        sym_file = tmp_path / "AharoniLab_Connector.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "BadConn"'
            '  (property "Reference" "R")'
            '  (property "Value" "BadConn")'
            '))'
        )
        result = check_reference_prefix(sym_file, rules)
        assert not result.passed
        assert any("Reference prefix" in e for e in result.errors)

    def test_subcategory_prefix_matching(self, tmp_path, rules):
        """Passive library should match R/C/L subcategory prefixes."""
        sym_file = tmp_path / "AharoniLab_Passive.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209)'
            '  (symbol "R_10k"'
            '    (property "Reference" "R")'
            '    (property "Value" "10k")'
            '  )'
            '  (symbol "C_100nF"'
            '    (property "Reference" "C")'
            '    (property "Value" "100nF")'
            '  )'
            ')'
        )
        result = check_reference_prefix(sym_file, rules)
        assert result.passed

    def test_unknown_category_skips(self, tmp_path, rules):
        """Files not in categories should be skipped (no errors)."""
        sym_file = tmp_path / "AharoniLab_Unknown.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "X"'
            '  (property "Reference" "X")'
            '  (property "Value" "X")'
            '))'
        )
        result = check_reference_prefix(sym_file, rules)
        assert result.passed


class TestPinCounts:
    def test_resistor_two_pins_passes(self, tmp_path, rules):
        """Resistor with 2 pins should pass."""
        sym_file = tmp_path / "AharoniLab_Passive.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "R_10k"'
            '  (property "Reference" "R")'
            '  (property "Value" "10k")'
            '  (symbol "R_10k_1_1"'
            '    (pin passive line (at 0 5 270) (length 2.54) (name "1") (number "1"))'
            '    (pin passive line (at 0 -5 90) (length 2.54) (name "2") (number "2"))'
            '  )'
            '))'
        )
        result = check_pin_counts(sym_file, rules)
        assert result.passed

    def test_too_few_pins_fails(self, tmp_path, rules):
        """Symbol with fewer pins than minimum should fail."""
        sym_file = tmp_path / "AharoniLab_Connector.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "BadConn"'
            '  (property "Reference" "J")'
            '  (property "Value" "BadConn")'
            '  (symbol "BadConn_1_1"'
            '    (pin passive line (at 0 0 0) (length 2.54) (name "1") (number "1"))'
            '  )'
            '))'
        )
        result = check_pin_counts(sym_file, rules)
        assert not result.passed
        assert any("minimum" in e for e in result.errors)

    def test_too_many_pins_fails(self, tmp_path, rules):
        """Symbol with more pins than maximum should fail."""
        sym_file = tmp_path / "AharoniLab_Passive.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "R_bad"'
            '  (property "Reference" "R")'
            '  (property "Value" "R_bad")'
            '  (symbol "R_bad_1_1"'
            '    (pin passive line (at 0 5 270) (length 2.54) (name "1") (number "1"))'
            '    (pin passive line (at 0 0 0) (length 2.54) (name "2") (number "2"))'
            '    (pin passive line (at 0 -5 90) (length 2.54) (name "3") (number "3"))'
            '  )'
            '))'
        )
        result = check_pin_counts(sym_file, rules)
        assert not result.passed
        assert any("maximum" in e for e in result.errors)

    def test_no_pin_rules_skips_check(self, tmp_path, rules):
        """Category without pin config should skip pin count check."""
        sym_file = tmp_path / "AharoniLab_Unknown.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "X"'
            '  (property "Reference" "X")'
            '  (property "Value" "X")'
            '))'
        )
        result = check_pin_counts(sym_file, rules)
        assert result.passed

    def test_diode_three_pins_allowed(self, tmp_path, rules):
        """Diode subcategory should allow up to 3 pins."""
        sym_file = tmp_path / "AharoniLab_Passive.kicad_sym"
        sym_file.write_text(
            '(kicad_symbol_lib (version 20241209) (symbol "D_Zener"'
            '  (property "Reference" "D")'
            '  (property "Value" "D_Zener")'
            '  (symbol "D_Zener_1_1"'
            '    (pin passive line (at 0 5 270) (length 2.54) (name "A") (number "1"))'
            '    (pin passive line (at 0 0 0) (length 2.54) (name "K") (number "2"))'
            '    (pin passive line (at 0 -5 90) (length 2.54) (name "C") (number "3"))'
            '  )'
            '))'
        )
        result = check_pin_counts(sym_file, rules)
        assert result.passed


class TestSymbolFlags:
    def test_correct_flags_pass(self, tmp_path, rules):
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "Good" (in_bom yes) (on_board yes) (property "Reference" "R")(property "Value" "Good")))')
        assert check_symbol_flags(sym_file, rules).passed

    def test_wrong_in_bom_fails(self, tmp_path, rules):
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "Bad" (in_bom no) (on_board yes) (property "Reference" "R")(property "Value" "Bad")))')
        result = check_symbol_flags(sym_file, rules)
        assert not result.passed
        assert any("in_bom" in e for e in result.errors)

    def test_wrong_on_board_fails(self, tmp_path, rules):
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "Bad" (in_bom yes) (on_board no) (property "Reference" "R")(property "Value" "Bad")))')
        result = check_symbol_flags(sym_file, rules)
        assert not result.passed

    def test_missing_flags_skip(self, tmp_path, rules):
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "NoFlags" (property "Reference" "R")(property "Value" "NoFlags")))')
        assert check_symbol_flags(sym_file, rules).passed

    def test_no_flag_rules_passes(self, tmp_path):
        from validator.config import LibraryRules
        sym_file = tmp_path / "AharoniLab_Test.kicad_sym"
        sym_file.write_text('(kicad_symbol_lib (version 20241209) (symbol "X" (in_bom no) (property "Reference" "R")(property "Value" "X")))')
        assert check_symbol_flags(sym_file, LibraryRules()).passed
