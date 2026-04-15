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

# Ensure repo root is on sys.path so validator package is importable
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from validator.lib_table import LibTableEntry, parse_lib_table, serialize_lib_table


# ---------------------------------------------------------------------------
# KiCad config detection
# ---------------------------------------------------------------------------

KICAD_VERSIONS = ["10.0", "9.0"]


def _get_kicad_base_dir(system: str) -> Path:
    """Return the platform-specific KiCad config base directory."""
    if system == "Windows":
        appdata = Path.home() / "AppData" / "Roaming"
        appdata_env = os.environ.get("APPDATA")
        if appdata_env:
            appdata = Path(appdata_env)
        return appdata / "kicad"
    elif system == "Darwin":
        return Path.home() / "Library" / "Preferences" / "kicad"
    elif system == "Linux":
        return Path.home() / ".config" / "kicad"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def get_kicad_config_dirs() -> list[Path]:
    """Return all KiCad configuration directories found on this system.

    Checks for KiCad versions in order (newest first).  Returns a list
    of existing config directories.  Raises ``RuntimeError`` if none
    are found.
    """
    system = platform.system()
    base = _get_kicad_base_dir(system)
    found = [base / v for v in KICAD_VERSIONS if (base / v).is_dir()]
    if not found:
        tried = ", ".join(str(base / v) for v in KICAD_VERSIONS)
        raise RuntimeError(
            f"No KiCad config directory found.\n"
            f"Looked for: {tried}\n"
            "Please make sure KiCad has been launched at least once."
        )
    return found


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
    if env.get("vars") is None:
        env["vars"] = {}
    env["vars"][var_name] = var_value
    return data


def remove_env_var(data: dict, var_name: str) -> bool:
    """Remove an environment variable. Returns True if it existed."""
    try:
        del data["environment"]["vars"][var_name]
        return True
    except (KeyError, TypeError):
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

        kept: list[LibTableEntry] = []
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
    parser.add_argument("--dry-run", action="store_true",
        help="Preview changes without modifying any files.")
    parser.add_argument("--uninstall", action="store_true",
        help="Remove all AharoniLab entries and the environment variable.")
    args = parser.parse_args(argv)

    try:
        config_dirs = get_kicad_config_dirs()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    for config_dir in config_dirs:
        version = config_dir.name
        print(f"{'='*60}")
        print(f"KiCad {version}")
        print(f"{'='*60}")
        print()

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
