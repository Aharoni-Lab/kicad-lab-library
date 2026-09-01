"""Tests for check_library_tables — the function behind ``--check-tables``.

This is what CI actually runs; previously only its behavior was
re-implemented in test assertions without ever calling it.
"""
from __future__ import annotations

from validator.checks import check_library_tables


def _write_tables(tmp_path, sym_entries="", fp_entries=""):
    (tmp_path / "sym-lib-table").write_text(
        f'(sym_lib_table (version 7) {sym_entries})'
    )
    (tmp_path / "fp-lib-table").write_text(
        f'(fp_lib_table (version 7) {fp_entries})'
    )


def _entry(name, uri):
    return f'(lib (name "{name}")(type "KiCad")(uri "{uri}")(options "")(descr ""))'


class TestCheckLibraryTables:
    def test_consistent_repo_passes(self, tmp_path):
        (tmp_path / "symbols").mkdir()
        (tmp_path / "symbols" / "AharoniLab_Test.kicad_sym").write_text("(kicad_symbol_lib)")
        (tmp_path / "footprints" / "AharoniLab_Test.pretty").mkdir(parents=True)
        _write_tables(
            tmp_path,
            _entry("AharoniLab_Test", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Test.kicad_sym"),
            _entry("AharoniLab_Test", "${AHARONI_LAB_KICAD_LIB}/footprints/AharoniLab_Test.pretty"),
        )
        assert check_library_tables(tmp_path).passed

    def test_real_repo_passes(self, repo_root):
        assert check_library_tables(repo_root).passed

    def test_symbol_file_without_entry_fails(self, tmp_path):
        (tmp_path / "symbols").mkdir()
        (tmp_path / "symbols" / "AharoniLab_Orphan.kicad_sym").write_text("(kicad_symbol_lib)")
        _write_tables(tmp_path)
        result = check_library_tables(tmp_path)
        assert not result.passed
        assert any("AharoniLab_Orphan" in e and "no sym-lib-table entry" in e
                   for e in result.errors)

    def test_footprint_dir_without_entry_fails(self, tmp_path):
        (tmp_path / "symbols").mkdir()
        (tmp_path / "footprints" / "AharoniLab_Orphan.pretty").mkdir(parents=True)
        _write_tables(tmp_path)
        result = check_library_tables(tmp_path)
        assert not result.passed
        assert any("no fp-lib-table entry" in e for e in result.errors)

    def test_absolute_uri_fails(self, tmp_path):
        (tmp_path / "symbols").mkdir()
        _write_tables(tmp_path, _entry("X", "/absolute/path.kicad_sym"))
        result = check_library_tables(tmp_path)
        assert not result.passed
        assert any("does not use" in e for e in result.errors)

    def test_missing_target_fails(self, tmp_path):
        (tmp_path / "symbols").mkdir()
        _write_tables(
            tmp_path,
            _entry("Ghost", "${AHARONI_LAB_KICAD_LIB}/symbols/Ghost.kicad_sym"),
        )
        result = check_library_tables(tmp_path)
        assert not result.passed
        assert any("target does not exist" in e for e in result.errors)

    def test_missing_tables_fail(self, tmp_path):
        result = check_library_tables(tmp_path)
        assert not result.passed
        assert any("sym-lib-table not found" in e for e in result.errors)
        assert any("fp-lib-table not found" in e for e in result.errors)
