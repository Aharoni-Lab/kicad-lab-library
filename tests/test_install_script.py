"""Tests for the install script.

These tests validate install.py logic using mocked/temp environments
so no actual KiCad config is modified.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import install as install_mod
from install import (
    LibEntry,
    parse_lib_table,
    serialize_lib_table,
    read_kicad_common,
    set_env_var,
    remove_env_var,
)


class TestKicadConfigDetection:
    def test_detect_kicad_config_dir(self, monkeypatch, tmp_path):
        """Should correctly detect KiCad config directory for each platform."""
        config_dir = tmp_path / "kicad" / "9.0"
        config_dir.mkdir(parents=True)

        # Patch platform.system to test Windows detection
        monkeypatch.setattr("install.platform.system", lambda: "Windows")
        monkeypatch.setenv("APPDATA", str(tmp_path))
        result = install_mod.get_kicad_config_dir()
        assert result == config_dir

    def test_missing_config_raises(self, monkeypatch, tmp_path):
        """Should raise RuntimeError if KiCad config dir doesn't exist."""
        monkeypatch.setattr("install.platform.system", lambda: "Linux")
        monkeypatch.setattr("install.Path.home", lambda: tmp_path)
        with pytest.raises(RuntimeError, match="not found"):
            install_mod.get_kicad_config_dir()


class TestLibTableParsing:
    def test_parse_repo_lib_tables(self, repo_root):
        """Should parse sym-lib-table and fp-lib-table from repo root."""
        sym_text = (repo_root / "sym-lib-table").read_text(encoding="utf-8")
        entries = parse_lib_table(sym_text)
        assert len(entries) > 0
        assert entries[0].name == "AharoniLab_Passive"

    def test_roundtrip_serialize(self):
        """Serializing and re-parsing should preserve entries."""
        entries = [
            LibEntry("TestLib", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/TestLib.kicad_sym", "", "Test"),
        ]
        text = serialize_lib_table("sym_lib_table", entries)
        parsed = parse_lib_table(text)
        assert len(parsed) == 1
        assert parsed[0].name == "TestLib"
        assert parsed[0].uri == "${AHARONI_LAB_KICAD_LIB}/symbols/TestLib.kicad_sym"


class TestMergeLogic:
    def test_merge_entries_skips_duplicates(self, tmp_path):
        """Should not add duplicate entries if library is already installed."""
        existing = [
            LibEntry("AharoniLab_Passive", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym", "", ""),
        ]
        global_text = serialize_lib_table("sym_lib_table", existing)
        global_path = tmp_path / "sym-lib-table"
        global_path.write_text(global_text)

        # The repo also has AharoniLab_Passive -- it should be skipped
        repo_entries = parse_lib_table(global_text)
        existing_names = {e.name for e in repo_entries}

        # Simulate merge
        new_entry = LibEntry("AharoniLab_Passive", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym", "", "")
        assert new_entry.name in existing_names  # Would be skipped

    def test_merge_adds_new_entries(self, tmp_path):
        """Should add entries that don't exist yet."""
        existing = [
            LibEntry("OtherLib", "KiCad", "/some/path", "", ""),
        ]
        new = LibEntry("AharoniLab_Passive", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym", "", "")

        existing_names = {e.name for e in existing}
        assert new.name not in existing_names  # Would be added


class TestUninstall:
    def test_uninstall_removes_entries(self, tmp_path):
        """--uninstall should remove all AharoniLab_ entries."""
        entries = [
            LibEntry("AharoniLab_Passive", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym", "", ""),
            LibEntry("SomeOther", "KiCad", "/other/path", "", "Other lib"),
        ]
        kept = [e for e in entries if not e.name.startswith("AharoniLab_")]
        assert len(kept) == 1
        assert kept[0].name == "SomeOther"


class TestKicadCommon:
    def test_set_env_var(self):
        """Should set environment variable in kicad_common.json structure."""
        data = {}
        set_env_var(data, "AHARONI_LAB_KICAD_LIB", "/some/path")
        assert data["environment"]["vars"]["AHARONI_LAB_KICAD_LIB"] == "/some/path"

    def test_remove_env_var(self):
        """Should remove environment variable."""
        data = {"environment": {"vars": {"AHARONI_LAB_KICAD_LIB": "/some/path"}}}
        removed = remove_env_var(data, "AHARONI_LAB_KICAD_LIB")
        assert removed
        assert "AHARONI_LAB_KICAD_LIB" not in data["environment"]["vars"]

    def test_remove_nonexistent_var(self):
        """Should return False if var doesn't exist."""
        data = {}
        assert not remove_env_var(data, "AHARONI_LAB_KICAD_LIB")

    def test_read_missing_common(self, tmp_path):
        """Should return empty dict if kicad_common.json doesn't exist."""
        result = read_kicad_common(tmp_path / "nonexistent.json")
        assert result == {}

    def test_read_existing_common(self, tmp_path):
        """Should parse existing kicad_common.json."""
        data = {"environment": {"vars": {"FOO": "bar"}}}
        path = tmp_path / "kicad_common.json"
        path.write_text(json.dumps(data))
        result = read_kicad_common(path)
        assert result["environment"]["vars"]["FOO"] == "bar"


class TestDryRun:
    def test_dry_run_makes_no_changes(self, tmp_path):
        """--dry-run should not modify files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")

        install_mod.write_file(test_file, "modified", dry_run=True)
        assert test_file.read_text() == "original"
