"""Tests for library table auto-generation.

These tests ensure:
- sym-lib-table is generated correctly from symbol files
- fp-lib-table is generated correctly from .pretty dirs
- Empty dirs produce empty tables (header only)
- Generated tables use the environment variable
- Mismatch detection works
"""
from __future__ import annotations

from pathlib import Path

from validator.table_gen import (
    check_tables_match_generated,
    generate_fp_lib_table,
    generate_sym_lib_table,
    write_generated_tables,
)


class TestGenerateSymLibTable:
    def test_generate_from_symbol_files(self, tmp_path):
        """Should generate a sym-lib-table entry for each .kicad_sym file."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        (sym_dir / "AharoniLab_Passive.kicad_sym").write_text("(kicad_symbol_lib)")
        (sym_dir / "AharoniLab_MCU.kicad_sym").write_text("(kicad_symbol_lib)")

        result = generate_sym_lib_table(tmp_path)
        assert "AharoniLab_MCU" in result
        assert "AharoniLab_Passive" in result
        assert "sym_lib_table" in result

    def test_empty_dirs_produce_empty_tables(self, tmp_path):
        """Empty symbols/ should produce a table with only the header."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()

        result = generate_sym_lib_table(tmp_path)
        assert "sym_lib_table" in result
        assert "(lib " not in result

    def test_generated_tables_use_env_var(self, tmp_path):
        """URIs should use ${AHARONI_LAB_KICAD_LIB}."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        (sym_dir / "AharoniLab_Test.kicad_sym").write_text("(kicad_symbol_lib)")

        result = generate_sym_lib_table(tmp_path)
        assert "${AHARONI_LAB_KICAD_LIB}" in result


class TestGenerateFpLibTable:
    def test_generate_from_pretty_dirs(self, tmp_path):
        """Should generate an fp-lib-table entry for each .pretty dir."""
        fp_dir = tmp_path / "footprints"
        fp_dir.mkdir()
        (fp_dir / "AharoniLab_Capacitor_SMD.pretty").mkdir()
        (fp_dir / "AharoniLab_Package_QFP.pretty").mkdir()

        result = generate_fp_lib_table(tmp_path)
        assert "AharoniLab_Capacitor_SMD" in result
        assert "AharoniLab_Package_QFP" in result
        assert "fp_lib_table" in result

    def test_empty_footprints_dir(self, tmp_path):
        """Empty footprints/ should produce a table with only the header."""
        fp_dir = tmp_path / "footprints"
        fp_dir.mkdir()

        result = generate_fp_lib_table(tmp_path)
        assert "fp_lib_table" in result
        assert "(lib " not in result


class TestTablesMatchDisk:
    def test_tables_match_disk_passes(self, tmp_path):
        """Tables that match generated content should pass."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        fp_dir = tmp_path / "footprints"
        fp_dir.mkdir()

        # Write tables that match what would be generated (empty)
        (tmp_path / "sym-lib-table").write_text(generate_sym_lib_table(tmp_path))
        (tmp_path / "fp-lib-table").write_text(generate_fp_lib_table(tmp_path))

        result = check_tables_match_generated(tmp_path)
        assert result.passed

    def test_tables_mismatch_disk_fails(self, tmp_path):
        """Tables that don't match generated content should fail."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        (sym_dir / "AharoniLab_New.kicad_sym").write_text("(kicad_symbol_lib)")
        fp_dir = tmp_path / "footprints"
        fp_dir.mkdir()

        # Write empty tables (missing the new symbol)
        (tmp_path / "sym-lib-table").write_text(
            "(sym_lib_table\n  (version 7)\n)\n"
        )
        (tmp_path / "fp-lib-table").write_text(generate_fp_lib_table(tmp_path))

        result = check_tables_match_generated(tmp_path)
        assert not result.passed
        assert any("sym-lib-table" in e for e in result.errors)

    def test_real_repo_tables_match(self, repo_root, rules):
        """The actual repo tables should match generated content."""
        result = check_tables_match_generated(repo_root, rules=rules)
        assert result.passed, f"Tables don't match: {result.errors}"


class TestWriteGeneratedTables:
    def test_write_generated_tables(self, tmp_path):
        (tmp_path / "symbols").mkdir()
        (tmp_path / "symbols" / "AharoniLab_Test.kicad_sym").write_text("(kicad_symbol_lib)")
        (tmp_path / "footprints").mkdir()
        (tmp_path / "footprints" / "AharoniLab_Test.pretty").mkdir()
        write_generated_tables(tmp_path)
        assert (tmp_path / "sym-lib-table").exists()
        assert "AharoniLab_Test" in (tmp_path / "sym-lib-table").read_text()

    def test_write_generated_tables_overwrites(self, tmp_path):
        (tmp_path / "symbols").mkdir()
        (tmp_path / "footprints").mkdir()
        (tmp_path / "sym-lib-table").write_text("old content")
        (tmp_path / "fp-lib-table").write_text("old content")
        write_generated_tables(tmp_path)
        assert "old content" not in (tmp_path / "sym-lib-table").read_text()


class TestTableDescriptions:
    def test_description_from_rules(self, tmp_path, rules):
        """Generated table should include descriptions from rules."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        (sym_dir / "AharoniLab_Passive.kicad_sym").write_text("(kicad_symbol_lib)")
        result = generate_sym_lib_table(tmp_path, rules=rules)
        assert "Passive components" in result

    def test_no_rules_empty_descr(self, tmp_path):
        """Without rules, descriptions should be empty."""
        sym_dir = tmp_path / "symbols"
        sym_dir.mkdir()
        (sym_dir / "AharoniLab_Passive.kicad_sym").write_text("(kicad_symbol_lib)")
        result = generate_sym_lib_table(tmp_path)
        assert '(descr "")' in result
