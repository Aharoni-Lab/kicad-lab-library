"""Library table auto-generation and verification.

Generates what ``sym-lib-table`` and ``fp-lib-table`` *should* look like
based on on-disk files, then compares against the actual tables.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from validator.checks import ENV_VAR_PLACEHOLDER, CheckResult
from validator.config import LibraryRules
from validator.lib_table import serialize_lib_table  # noqa: F401


def generate_sym_lib_table(
    repo_root: str | Path,
    *,
    rules: Optional[LibraryRules] = None,
) -> str:
    """Generate the expected ``sym-lib-table`` content from symbol files on disk."""
    repo_root = Path(repo_root)
    symbols_dir = repo_root / "symbols"

    lines = ["(sym_lib_table", "  (version 7)"]

    if symbols_dir.is_dir():
        for sym_file in sorted(symbols_dir.glob("*.kicad_sym")):
            name = sym_file.stem
            uri = f"{ENV_VAR_PLACEHOLDER}/symbols/{sym_file.name}"
            descr = ""
            if rules and name in rules.categories:
                cat = rules.categories[name]
                if cat.description:
                    descr = cat.description
            lines.append(
                f'  (lib (name "{name}")(type "KiCad")'
                f'(uri "{uri}")(options "")(descr "{descr}"))'
            )

    lines.append(")")
    return "\n".join(lines) + "\n"


def generate_fp_lib_table(repo_root: str | Path) -> str:
    """Generate the expected ``fp-lib-table`` content from footprint dirs on disk."""
    repo_root = Path(repo_root)
    footprints_dir = repo_root / "footprints"

    lines = ["(fp_lib_table", "  (version 7)"]

    if footprints_dir.is_dir():
        for fp_dir in sorted(footprints_dir.iterdir()):
            if fp_dir.is_dir() and fp_dir.suffix == ".pretty":
                name = fp_dir.stem
                uri = f"{ENV_VAR_PLACEHOLDER}/footprints/{fp_dir.name}"
                lines.append(
                    f'  (lib (name "{name}")(type "KiCad")'
                    f'(uri "{uri}")(options "")(descr ""))'
                )

    lines.append(")")
    return "\n".join(lines) + "\n"


def write_generated_tables(
    repo_root: str | Path,
    *,
    rules: Optional[LibraryRules] = None,
) -> None:
    """Write auto-generated library tables to disk."""
    repo_root = Path(repo_root)
    (repo_root / "sym-lib-table").write_text(
        generate_sym_lib_table(repo_root, rules=rules), encoding="utf-8",
    )
    (repo_root / "fp-lib-table").write_text(
        generate_fp_lib_table(repo_root), encoding="utf-8",
    )


def check_tables_match_generated(
    repo_root: str | Path,
    *,
    rules: Optional[LibraryRules] = None,
) -> CheckResult:
    """Verify that on-disk library tables match what would be generated.

    Reports mismatches rather than overwriting.
    """
    repo_root = Path(repo_root)
    errors: List[str] = []

    # sym-lib-table
    sym_table_path = repo_root / "sym-lib-table"
    expected_sym = generate_sym_lib_table(repo_root, rules=rules)
    if sym_table_path.exists():
        actual_sym = sym_table_path.read_text(encoding="utf-8")
        if _normalize(actual_sym) != _normalize(expected_sym):
            errors.append(
                "sym-lib-table does not match generated content. "
                "Run 'python -m validator --generate-tables' to update."
            )
    else:
        errors.append("sym-lib-table not found at repository root")

    # fp-lib-table
    fp_table_path = repo_root / "fp-lib-table"
    expected_fp = generate_fp_lib_table(repo_root)
    if fp_table_path.exists():
        actual_fp = fp_table_path.read_text(encoding="utf-8")
        if _normalize(actual_fp) != _normalize(expected_fp):
            errors.append(
                "fp-lib-table does not match generated content. "
                "Run 'python -m validator --generate-tables' to update."
            )
    else:
        errors.append("fp-lib-table not found at repository root")

    return CheckResult(errors=errors)


def _normalize(text: str) -> str:
    """Normalize whitespace for comparison (strip trailing, normalize newlines)."""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)
