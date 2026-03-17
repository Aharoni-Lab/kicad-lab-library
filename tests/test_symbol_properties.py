"""Tests for lab-specific symbol property validation.

These tests encode our requirements:
- Every symbol MUST have a Datasheet property with a URL (not empty, not '~')
- Every symbol MUST have a Validated property set to 'Yes' or 'No'
- Malformed files must produce clear errors, not crash
"""
from __future__ import annotations

from validate import check_symbol_properties, parse_kicad_sym


class TestDatasheetProperty:
    def test_valid_symbol_has_datasheet_url(self, valid_symbol_path):
        """Every symbol MUST have a Datasheet property with a URL."""
        result = check_symbol_properties(valid_symbol_path)
        assert result.passed

    def test_missing_datasheet_fails(self, invalid_no_datasheet_path):
        """Symbol without Datasheet property should fail validation."""
        result = check_symbol_properties(invalid_no_datasheet_path)
        assert not result.passed
        assert any("Datasheet" in e for e in result.errors)

    def test_empty_datasheet_fails(self, invalid_empty_datasheet_path):
        """Symbol with empty Datasheet should fail validation."""
        result = check_symbol_properties(invalid_empty_datasheet_path)
        assert not result.passed


class TestValidatedProperty:
    def test_validated_yes_passes(self, valid_symbol_path):
        """Symbol with Validated='Yes' should pass."""
        result = check_symbol_properties(valid_symbol_path)
        assert result.passed

    def test_validated_no_passes(self, valid_symbol_unvalidated_path):
        """Symbol with Validated='No' should pass (it's a valid state)."""
        result = check_symbol_properties(valid_symbol_unvalidated_path)
        assert result.passed

    def test_missing_validated_fails(self, invalid_no_validated_path):
        """Symbol without Validated property should fail."""
        result = check_symbol_properties(invalid_no_validated_path)
        assert not result.passed
        assert any("Validated" in e for e in result.errors)

    def test_invalid_validated_value_fails(self, invalid_bad_validated_path):
        """Symbol with Validated='Maybe' should fail."""
        result = check_symbol_properties(invalid_bad_validated_path)
        assert not result.passed


class TestReferenceProperty:
    def test_valid_symbol_has_reference(self, valid_symbol_path):
        """Every symbol MUST have a Reference property."""
        result = check_symbol_properties(valid_symbol_path)
        assert result.passed

    def test_missing_reference_fails(self, invalid_no_reference_path):
        """Symbol without Reference property should fail validation."""
        result = check_symbol_properties(invalid_no_reference_path)
        assert not result.passed
        assert any("Reference" in e for e in result.errors)


class TestDescriptionProperty:
    def test_valid_symbol_has_description(self, valid_symbol_path):
        """Every symbol MUST have a Description property."""
        result = check_symbol_properties(valid_symbol_path)
        assert result.passed

    def test_missing_description_fails(self, invalid_no_description_path):
        """Symbol without Description property should fail validation."""
        result = check_symbol_properties(invalid_no_description_path)
        assert not result.passed
        assert any("Description" in e for e in result.errors)


class TestKeywordsProperty:
    def test_valid_symbol_has_keywords(self, valid_symbol_path):
        """Every symbol MUST have a ki_keywords property."""
        result = check_symbol_properties(valid_symbol_path)
        assert result.passed

    def test_missing_keywords_fails(self, invalid_no_keywords_path):
        """Symbol without ki_keywords property should fail validation."""
        result = check_symbol_properties(invalid_no_keywords_path)
        assert not result.passed
        assert any("ki_keywords" in e for e in result.errors)


class TestSymbolParsing:
    def test_can_parse_valid_symbol(self, valid_symbol_path):
        """Should be able to parse a valid KiCad 9 .kicad_sym file."""
        symbols = parse_kicad_sym(valid_symbol_path)
        assert len(symbols) > 0

    def test_malformed_file_reports_error(self, invalid_malformed_path):
        """Malformed file should produce a clear error, not crash."""
        result = check_symbol_properties(invalid_malformed_path)
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
