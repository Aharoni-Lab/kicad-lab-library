#!/usr/bin/env python3
"""Install the Aharoni Lab KiCad library into KiCad 9's global configuration.

This script:
  1. Locates the KiCad 9 config directory (platform-aware).
  2. Sets the AHARONI_LAB_KICAD_LIB environment variable in kicad_common.json.
  3. Merges symbol and footprint library entries into KiCad's global tables.

Usage:
    python scripts/install.py            # Install
    python scripts/install.py --dry-run  # Preview changes
    python scripts/install.py --uninstall  # Remove
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

from sexpr import parse_sexpr


# ---------------------------------------------------------------------------
# KiCad config detection
# ---------------------------------------------------------------------------

def get_kicad_config_dir() -> Path:
    """Return the KiCad 9 configuration directory for the current platform.

    Raises ``RuntimeError`` if the directory does not exist.
    """
    system = platform.system()
    if system == "Windows":
        appdata = Path.home() / "AppData" / "Roaming"
        # Also honour %APPDATA% when set (it almost always is).
        appdata_env = os.environ.get("APPDATA")
        if appdata_env:
            appdata = Path(appdata_env)
        config_dir = appdata / "kicad" / "9.0"
    elif system == "Darwin":
        config_dir = Path.home() / "Library" / "Preferences" / "kicad" / "9.0"
    elif system == "Linux":
        config_dir = Path.home() / ".config" / "kicad" / "9.0"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    if not config_dir.is_dir():
        raise RuntimeError(
            f"KiCad 9 config directory not found at {config_dir}\n"
            "Please make sure KiCad 9 has been launched at least once."
        )
    return config_dir


# ---------------------------------------------------------------------------
# Repo root detection
# ---------------------------------------------------------------------------

def get_repo_root() -> Path:
    """Walk up from this script's directory until we find ``sym-lib-table``."""
    current = Path(__file__).resolve().parent
    while True:
        if (current / "sym-lib-table").is_file():
            return current
        parent = current.parent
        if parent == current:
            raise RuntimeError(
                "Could not locate repository root (no sym-lib-table found "
                "in any parent directory of the script)."
            )
        current = parent


def _quote(s: str) -> str:
    """Wrap a string in double-quotes."""
    return f'"{s}"'


# ---------------------------------------------------------------------------
# Library entry helpers
# ---------------------------------------------------------------------------

class LibEntry:
    """One ``(lib ...)`` row inside a KiCad library table."""

    __slots__ = ("name", "type", "uri", "options", "descr")

    def __init__(
        self,
        name: str,
        type: str,
        uri: str,
        options: str = "",
        descr: str = "",
    ) -> None:
        self.name = name
        self.type = type
        self.uri = uri
        self.options = options
        self.descr = descr

    def to_sexpr(self) -> str:
        return (
            f'  (lib (name {_quote(self.name)})(type {_quote(self.type)})'
            f'(uri {_quote(self.uri)})(options {_quote(self.options)})'
            f'(descr {_quote(self.descr)}))'
        )


def _extract_field(node: list, field_name: str) -> str:
    """Extract a named field value from a parsed ``(lib ...)`` node."""
    for item in node:
        if isinstance(item, list) and len(item) >= 2 and item[0] == field_name:
            return item[1]
    return ""


def parse_lib_table(text: str) -> list[LibEntry]:
    """Parse a ``sym-lib-table`` or ``fp-lib-table`` file into LibEntry list."""
    root = parse_sexpr(text)
    entries: list[LibEntry] = []
    for item in root:
        if isinstance(item, list) and item and item[0] == "lib":
            entries.append(
                LibEntry(
                    name=_extract_field(item, "name"),
                    type=_extract_field(item, "type"),
                    uri=_extract_field(item, "uri"),
                    options=_extract_field(item, "options"),
                    descr=_extract_field(item, "descr"),
                )
            )
    return entries


def serialize_lib_table(kind: str, entries: list[LibEntry]) -> str:
    """Serialize a list of LibEntry objects back into a KiCad table file."""
    lines = [f"({kind}", "  (version 7)"]
    for entry in entries:
        lines.append(entry.to_sexpr())
    lines.append(")")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# kicad_common.json helpers
# ---------------------------------------------------------------------------

def read_kicad_common(path: Path) -> dict:
    """Read ``kicad_common.json``, returning a dict (empty-ish if missing)."""
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    # Minimal skeleton so the rest of the code can just set keys.
    return {}


def set_env_var(data: dict, var_name: str, var_value: str) -> dict:
    """Set an environment variable inside the kicad_common.json structure."""
    env = data.setdefault("environment", {})
    vars_ = env.setdefault("vars", {})
    vars_[var_name] = var_value
    return data


def remove_env_var(data: dict, var_name: str) -> bool:
    """Remove an environment variable. Returns True if it existed."""
    try:
        del data["environment"]["vars"][var_name]
        return True
    except KeyError:
        return False


# ---------------------------------------------------------------------------
# File I/O with backup
# ---------------------------------------------------------------------------

def _backup(path: Path) -> None:
    """Create a ``.bak`` copy of *path* if it exists."""
    if path.is_file():
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)


def write_file(path: Path, content: str, *, dry_run: bool) -> None:
    """Write *content* to *path*, creating a backup first."""
    if dry_run:
        return
    _backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Install logic
# ---------------------------------------------------------------------------

ENV_VAR_NAME = "AHARONI_LAB_KICAD_LIB"
AHARONI_PREFIX = "AharoniLab_"


def install(config_dir: Path, repo_root: Path, *, dry_run: bool) -> None:
    """Run the full installation sequence."""
    prefix = "[DRY RUN] " if dry_run else ""

    # -- 1. Environment variable ----------------------------------------
    common_path = config_dir / "kicad_common.json"
    common = read_kicad_common(common_path)
    repo_root_str = str(repo_root).replace("\\", "/")
    set_env_var(common, ENV_VAR_NAME, repo_root_str)
    write_file(common_path, json.dumps(common, indent=2) + "\n", dry_run=dry_run)
    print(f"{prefix}Config directory : {config_dir}")
    print(f"{prefix}Set {ENV_VAR_NAME} = {repo_root_str}")
    print()

    # -- 2. Library tables ----------------------------------------------
    for table_file, kind in [
        ("sym-lib-table", "sym_lib_table"),
        ("fp-lib-table", "fp_lib_table"),
    ]:
        repo_table_path = repo_root / table_file
        if not repo_table_path.is_file():
            print(f"{prefix}{table_file}: not found in repo, skipping.")
            continue

        repo_entries = parse_lib_table(repo_table_path.read_text(encoding="utf-8"))

        global_table_path = config_dir / table_file
        if global_table_path.is_file():
            global_entries = parse_lib_table(
                global_table_path.read_text(encoding="utf-8")
            )
        else:
            global_entries = []

        existing_names = {e.name for e in global_entries}

        added: list[str] = []
        skipped: list[str] = []
        for entry in repo_entries:
            if entry.name in existing_names:
                skipped.append(entry.name)
            else:
                global_entries.append(entry)
                added.append(entry.name)

        content = serialize_lib_table(kind, global_entries)
        write_file(global_table_path, content, dry_run=dry_run)

        print(f"{prefix}{table_file}:")
        if added:
            for name in added:
                print(f"  + {name}")
        if skipped:
            for name in skipped:
                print(f"  ~ {name} (already present, skipped)")
        if not added and not skipped:
            print("  (no entries in repo table)")
        print()


# ---------------------------------------------------------------------------
# Uninstall logic
# ---------------------------------------------------------------------------

def uninstall(config_dir: Path, *, dry_run: bool) -> None:
    """Remove all AharoniLab entries and the environment variable."""
    prefix = "[DRY RUN] " if dry_run else ""

    # -- 1. Environment variable ----------------------------------------
    common_path = config_dir / "kicad_common.json"
    if common_path.is_file():
        common = read_kicad_common(common_path)
        removed = remove_env_var(common, ENV_VAR_NAME)
        if removed:
            write_file(
                common_path,
                json.dumps(common, indent=2) + "\n",
                dry_run=dry_run,
            )
            print(f"{prefix}Removed {ENV_VAR_NAME} from {common_path}")
        else:
            print(f"{prefix}{ENV_VAR_NAME} was not set in {common_path}")
    else:
        print(f"{prefix}{common_path} does not exist, nothing to do.")
    print()

    # -- 2. Library tables ----------------------------------------------
    for table_file, kind in [
        ("sym-lib-table", "sym_lib_table"),
        ("fp-lib-table", "fp_lib_table"),
    ]:
        global_table_path = config_dir / table_file
        if not global_table_path.is_file():
            print(f"{prefix}{table_file}: not found, skipping.")
            continue

        global_entries = parse_lib_table(
            global_table_path.read_text(encoding="utf-8")
        )

        kept: list[LibEntry] = []
        removed_names: list[str] = []
        for entry in global_entries:
            if entry.name.startswith(AHARONI_PREFIX):
                removed_names.append(entry.name)
            else:
                kept.append(entry)

        if removed_names:
            content = serialize_lib_table(kind, kept)
            write_file(global_table_path, content, dry_run=dry_run)
            print(f"{prefix}{table_file}:")
            for name in removed_names:
                print(f"  - {name}")
        else:
            print(f"{prefix}{table_file}: no AharoniLab entries found.")
        print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Install or remove the Aharoni Lab KiCad library.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files.",
    )
    group.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove all AharoniLab entries and the environment variable.",
    )
    args = parser.parse_args(argv)

    try:
        config_dir = get_kicad_config_dir()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.uninstall:
        uninstall(config_dir, dry_run=args.dry_run)
    else:
        try:
            repo_root = get_repo_root()
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        install(config_dir, repo_root, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
