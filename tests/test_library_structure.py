"""Tests for directory structure and naming conventions.

These tests ensure:
- Required directories exist
- Flat structure (no nested subdirectories in symbols/)
- AharoniLab_ prefix on all library files
- 3dshapes dirs match .pretty dirs
- No backup or project files committed
- No duplicate symbol names across library files
"""
from __future__ import annotations

from validate import check_duplicate_symbols


class TestDirectoryStructure:
    def test_symbols_dir_exists(self, repo_root):
        """symbols/ directory must exist."""
        assert (repo_root / "symbols").is_dir()

    def test_footprints_dir_exists(self, repo_root):
        """footprints/ directory must exist."""
        assert (repo_root / "footprints").is_dir()

    def test_no_nested_symbol_dirs(self, repo_root):
        """symbols/ should be flat -- no subdirectories."""
        for item in (repo_root / "symbols").iterdir():
            assert item.is_file(), f"Unexpected subdirectory in symbols/: {item.name}"

    def test_sym_files_have_prefix(self, repo_root):
        """All .kicad_sym files must start with 'AharoniLab_'."""
        for f in (repo_root / "symbols").glob("*.kicad_sym"):
            assert f.stem.startswith("AharoniLab_"), f"{f.name} missing AharoniLab_ prefix"

    def test_pretty_dirs_have_prefix(self, repo_root):
        """All .pretty directories must start with 'AharoniLab_'."""
        for d in (repo_root / "footprints").iterdir():
            if d.suffix == ".pretty":
                assert d.stem.startswith("AharoniLab_"), (
                    f"{d.name} missing AharoniLab_ prefix"
                )

    def test_3dshapes_match_pretty_dirs(self, repo_root):
        """Every .3dshapes directory should have a matching .pretty directory."""
        models_dir = repo_root / "3dmodels"
        if models_dir.exists():
            for d in models_dir.iterdir():
                if d.suffix == ".3dshapes":
                    matching_pretty = repo_root / "footprints" / (d.stem + ".pretty")
                    assert matching_pretty.exists(), (
                        f"3D model dir {d.name} has no matching .pretty dir"
                    )

    def test_no_backup_files(self, repo_root):
        """No KiCad backup files should be committed."""
        for pattern in ["**/*.bak", "**/*-bak", "**/*~", "**/_autosave-*"]:
            matches = [
                p for p in repo_root.glob(pattern)
                if ".git" not in str(p) and ".claude" not in str(p)
            ]
            assert len(matches) == 0, f"Backup file found: {matches}"

    def test_no_kicad_project_files(self, repo_root):
        """No KiCad project files should be in the repo."""
        for ext in [".kicad_pro", ".kicad_prl", ".kicad_pcb", ".kicad_sch"]:
            matches = [
                p for p in repo_root.glob(f"**/*{ext}")
                if ".git" not in str(p)
            ]
            assert len(matches) == 0, f"Project file found: {matches}"


class TestDuplicateSymbols:
    def test_no_duplicate_symbols_in_repo(self, repo_root):
        """No two .kicad_sym files should define the same symbol name."""
        result = check_duplicate_symbols(repo_root)
        assert result.passed, f"Duplicate symbols found: {result.errors}"

    def test_duplicate_detection(self, tmp_path):
        """Should detect when two files define the same symbol."""
        symbols_dir = tmp_path / "symbols"
        symbols_dir.mkdir()

        # Two files with the same symbol name
        for name in ["AharoniLab_A.kicad_sym", "AharoniLab_B.kicad_sym"]:
            (symbols_dir / name).write_text(
                '(kicad_symbol_lib (version 20241209)'
                ' (symbol "DuplicatePart"'
                '  (property "Reference" "U")'
                '  (property "Value" "DuplicatePart")'
                ' ))'
            )

        result = check_duplicate_symbols(tmp_path)
        assert not result.passed
        assert any("DuplicatePart" in e for e in result.errors)
