"""Tests for library table consistency.

These tests ensure:
- Every .kicad_sym file has a matching sym-lib-table entry and vice versa
- Every .pretty dir has a matching fp-lib-table entry and vice versa
- All URIs use ${AHARONI_LAB_KICAD_LIB}, no absolute paths
"""
from __future__ import annotations

from pathlib import Path

from validator.checks import ENV_VAR_PLACEHOLDER, parse_lib_table, resolve_table_uri


class TestSymLibTableConsistency:
    def test_every_sym_file_has_table_entry(self, repo_root):
        """Every .kicad_sym file in symbols/ must have a matching entry in sym-lib-table."""
        sym_files = list((repo_root / "symbols").glob("*.kicad_sym"))
        table_entries = parse_lib_table(repo_root / "sym-lib-table")
        entry_names = {e.name for e in table_entries}
        for sym_file in sym_files:
            lib_name = sym_file.stem
            assert lib_name in entry_names, f"{sym_file.name} missing from sym-lib-table"

    def test_every_table_entry_has_sym_file(self, repo_root):
        """Every entry in sym-lib-table must point to an existing .kicad_sym file."""
        table_entries = parse_lib_table(repo_root / "sym-lib-table")
        for entry in table_entries:
            sym_path = resolve_table_uri(entry.uri, repo_root)
            assert sym_path.exists(), (
                f"sym-lib-table entry '{entry.name}' points to non-existent {sym_path}"
            )

    def test_table_uses_env_variable(self, repo_root):
        """All URIs in sym-lib-table must use ${AHARONI_LAB_KICAD_LIB}."""
        table_entries = parse_lib_table(repo_root / "sym-lib-table")
        for entry in table_entries:
            assert ENV_VAR_PLACEHOLDER in entry.uri, (
                f"Entry '{entry.name}' does not use ${{AHARONI_LAB_KICAD_LIB}}"
            )


class TestFpLibTableConsistency:
    def test_every_pretty_dir_has_table_entry(self, repo_root):
        """Every .pretty directory in footprints/ must have a matching entry in fp-lib-table."""
        pretty_dirs = [
            d for d in (repo_root / "footprints").iterdir()
            if d.is_dir() and d.suffix == ".pretty"
        ]
        table_entries = parse_lib_table(repo_root / "fp-lib-table")
        entry_names = {e.name for e in table_entries}
        for pretty_dir in pretty_dirs:
            lib_name = pretty_dir.stem
            assert lib_name in entry_names, (
                f"{pretty_dir.name} missing from fp-lib-table"
            )

    def test_every_fp_table_entry_has_pretty_dir(self, repo_root):
        """Every entry in fp-lib-table must point to an existing .pretty directory."""
        table_entries = parse_lib_table(repo_root / "fp-lib-table")
        for entry in table_entries:
            fp_path = resolve_table_uri(entry.uri, repo_root)
            assert fp_path.exists() and fp_path.is_dir(), (
                f"fp-lib-table entry '{entry.name}' points to non-existent {fp_path}"
            )

    def test_fp_table_uses_env_variable(self, repo_root):
        """All URIs must use ${AHARONI_LAB_KICAD_LIB}."""
        table_entries = parse_lib_table(repo_root / "fp-lib-table")
        for entry in table_entries:
            assert ENV_VAR_PLACEHOLDER in entry.uri, (
                f"Entry '{entry.name}' does not use ${{AHARONI_LAB_KICAD_LIB}}"
            )


class TestTableCheckMessages:
    def test_bad_uri_error_names_the_env_var(self, tmp_path):
        """The error for a URI not using the env var must print
        ${AHARONI_LAB_KICAD_LIB}, not a doubled-brace artifact."""
        from validator.checks import check_library_tables
        (tmp_path / "symbols").mkdir()
        (tmp_path / "sym-lib-table").write_text(
            '(sym_lib_table (version 7) '
            '(lib (name "X")(type "KiCad")(uri "/absolute/path")(options "")(descr "")))'
        )
        (tmp_path / "fp-lib-table").write_text('(fp_lib_table (version 7))')
        result = check_library_tables(tmp_path)
        assert not result.passed
        uri_errors = [e for e in result.errors if "does not use" in e]
        assert uri_errors
        assert all("${AHARONI_LAB_KICAD_LIB}" in e for e in uri_errors)
        assert all("{{" not in e for e in uri_errors)
