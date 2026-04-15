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
    read_kicad_common,
    set_env_var,
    remove_env_var,
)
from validator.lib_table import LibTableEntry, parse_lib_table, serialize_lib_table


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
        """Should parse sym-lib-table from repo root without error."""
        sym_text = (repo_root / "sym-lib-table").read_text(encoding="utf-8")
        entries = parse_lib_table(sym_text)
        assert isinstance(entries, list)

    def test_roundtrip_serialize(self):
        """Serializing and re-parsing should preserve entries."""
        entries = [
            LibTableEntry("TestLib", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/TestLib.kicad_sym", "", "Test"),
        ]
        text = serialize_lib_table("sym_lib_table", entries)
        parsed = parse_lib_table(text)
        assert len(parsed) == 1
        assert parsed[0].name == "TestLib"
        assert parsed[0].uri == "${AHARONI_LAB_KICAD_LIB}/symbols/TestLib.kicad_sym"


class TestMergeLogic:
    def test_install_skips_duplicates(self, tmp_path, monkeypatch):
        """Should not add duplicate entries if library is already installed."""
        # Set up a fake KiCad config dir with an existing table
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        existing = [
            LibTableEntry("AharoniLab_Passive", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym", "", "Passive"),
        ]
        global_text = serialize_lib_table("sym_lib_table", existing)
        (config_dir / "sym-lib-table").write_text(global_text)

        # Set up a fake repo with the same entry
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "sym-lib-table").write_text(global_text)
        # fp-lib-table not in repo, so it will be skipped
        (repo_dir / "symbols").mkdir()

        install_mod.install(config_dir, repo_dir, dry_run=False)

        result = parse_lib_table((config_dir / "sym-lib-table").read_text())
        assert len(result) == 1
        assert result[0].name == "AharoniLab_Passive"

    def test_install_adds_new_entries(self, tmp_path):
        """Should add entries that don't exist yet."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        existing = [
            LibTableEntry("OtherLib", "KiCad", "/some/path", "", ""),
        ]
        (config_dir / "sym-lib-table").write_text(
            serialize_lib_table("sym_lib_table", existing)
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        new_entries = [
            LibTableEntry("AharoniLab_Passive", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym", "", "Passive"),
        ]
        (repo_dir / "sym-lib-table").write_text(
            serialize_lib_table("sym_lib_table", new_entries)
        )

        install_mod.install(config_dir, repo_dir, dry_run=False)

        result = parse_lib_table((config_dir / "sym-lib-table").read_text())
        names = {e.name for e in result}
        assert "OtherLib" in names
        assert "AharoniLab_Passive" in names


class TestUninstall:
    def test_uninstall_removes_aharoni_entries(self, tmp_path):
        """--uninstall should remove all AharoniLab_ entries and keep others."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        entries = [
            LibTableEntry("AharoniLab_Passive", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym", "", ""),
            LibTableEntry("SomeOther", "KiCad", "/other/path", "", "Other lib"),
        ]
        (config_dir / "sym-lib-table").write_text(
            serialize_lib_table("sym_lib_table", entries)
        )
        # kicad_common.json with env var
        common = {"environment": {"vars": {"AHARONI_LAB_KICAD_LIB": "/some/path"}}}
        (config_dir / "kicad_common.json").write_text(json.dumps(common))

        install_mod.uninstall(config_dir, dry_run=False)

        result = parse_lib_table((config_dir / "sym-lib-table").read_text())
        assert len(result) == 1
        assert result[0].name == "SomeOther"


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

    def test_set_env_var_null_vars(self):
        """Should handle KiCad's null vars field (written as 'vars': null)."""
        data = {"environment": {"vars": None}}
        set_env_var(data, "AHARONI_LAB_KICAD_LIB", "/some/path")
        assert data["environment"]["vars"]["AHARONI_LAB_KICAD_LIB"] == "/some/path"

    def test_remove_nonexistent_var(self):
        """Should return False if var doesn't exist."""
        data = {}
        assert not remove_env_var(data, "AHARONI_LAB_KICAD_LIB")

    def test_remove_var_null_vars(self):
        """Should return False if vars is null."""
        data = {"environment": {"vars": None}}
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


class TestDryRunUninstall:
    def test_dry_run_uninstall_makes_no_changes(self, tmp_path):
        from validator.lib_table import LibTableEntry, serialize_lib_table
        import json
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        entries = [LibTableEntry("AharoniLab_Passive", "KiCad", "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym", "", "")]
        original_content = serialize_lib_table("sym_lib_table", entries)
        (config_dir / "sym-lib-table").write_text(original_content)
        common = {"environment": {"vars": {"AHARONI_LAB_KICAD_LIB": "/some/path"}}}
        (config_dir / "kicad_common.json").write_text(json.dumps(common))
        import install as install_mod
        install_mod.uninstall(config_dir, dry_run=True)
        assert (config_dir / "sym-lib-table").read_text() == original_content
        assert "AHARONI_LAB_KICAD_LIB" in (config_dir / "kicad_common.json").read_text()
