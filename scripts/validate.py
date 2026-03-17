#!/usr/bin/env python3
"""Core validation script for the Aharoni Lab KiCad library.

Standalone (stdlib only). Validates symbol properties, library table
consistency, and generates markdown reports.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

from sexpr import parse_sexpr


# ---------------------------------------------------------------------------
# Symbol file helpers
# ---------------------------------------------------------------------------

class SymbolInfo(NamedTuple):
    """Lightweight container for a parsed KiCad symbol."""
    name: str
    properties: Dict[str, str]


def _extract_properties(sexpr_node: list) -> Dict[str, str]:
    """Return a dict of property name -> value from a symbol S-expression node."""
    props: Dict[str, str] = {}
    for child in sexpr_node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == 'property':
            props[child[1]] = child[2]
    return props


def parse_kicad_sym(filepath: str | Path) -> List[SymbolInfo]:
    """Parse a ``.kicad_sym`` file and return a list of :class:`SymbolInfo`.

    Only *top-level* symbols are returned (sub-symbols like ``C_0_1``
    are skipped).
    """
    filepath = Path(filepath)
    text = filepath.read_text(encoding='utf-8')
    tree = parse_sexpr(text)

    # tree should be ['kicad_symbol_lib', ... , ['symbol', name, ...], ...]
    symbols: List[SymbolInfo] = []
    # Collect top-level symbol names first so we can identify children.
    top_names: List[str] = []
    symbol_nodes: List[list] = []
    for node in tree:
        if isinstance(node, list) and len(node) >= 2 and node[0] == 'symbol':
            top_names.append(node[1])
            symbol_nodes.append(node)

    # A child symbol's name starts with a parent name + "_" and ends
    # with digit(s)_digit(s).  Build a set of children to exclude.
    children: set = set()
    for name in top_names:
        for other in top_names:
            if other == name:
                continue
            if other.startswith(name + '_'):
                suffix = other[len(name) + 1:]
                parts = suffix.split('_')
                if all(p.isdigit() for p in parts):
                    children.add(other)

    for node in symbol_nodes:
        name = node[1]
        if name in children:
            continue
        props = _extract_properties(node)
        symbols.append(SymbolInfo(name=name, properties=props))

    return symbols


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Outcome of a single validation check."""
    errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Symbol property checks
# ---------------------------------------------------------------------------

def check_symbol_properties(
    filepath: str | Path,
    *,
    symbols: Optional[List[SymbolInfo]] = None,
) -> CheckResult:
    """Validate lab-specific property requirements for a ``.kicad_sym`` file.

    Rules checked for every symbol:
    * ``Reference`` must exist and be non-empty.
    * ``Description`` must exist and be non-empty.
    * ``ki_keywords`` must exist and be non-empty.
    * ``Datasheet`` must exist and be non-empty and not ``~``.
    * ``Validated`` must exist and equal ``"Yes"`` or ``"No"``.

    Pass pre-parsed *symbols* to avoid re-reading the file.
    """
    filepath = Path(filepath)
    errors: List[str] = []

    if symbols is None:
        try:
            symbols = parse_kicad_sym(filepath)
        except Exception as exc:
            return CheckResult(
                errors=[f"Failed to parse file (format/parse error): {exc}"],
            )

    for sym in symbols:
        # Reference check
        ref = sym.properties.get('Reference')
        if ref is None or ref.strip() == '':
            errors.append(
                f"Symbol '{sym.name}': Reference property is missing or empty"
            )

        # Description check
        desc = sym.properties.get('Description')
        if desc is None or desc.strip() == '':
            errors.append(
                f"Symbol '{sym.name}': Description property is missing or empty"
            )

        # ki_keywords check
        kw = sym.properties.get('ki_keywords')
        if kw is None or kw.strip() == '':
            errors.append(
                f"Symbol '{sym.name}': ki_keywords property is missing or empty"
            )

        # Datasheet check
        ds = sym.properties.get('Datasheet')
        if ds is None or ds.strip() == '' or ds.strip() == '~':
            errors.append(
                f"Symbol '{sym.name}': Datasheet property is missing or empty"
            )

        # Validated check
        val = sym.properties.get('Validated')
        if val is None or val not in ('Yes', 'No'):
            errors.append(
                f"Symbol '{sym.name}': Validated property must be 'Yes' or 'No'"
                + (f" (got '{val}')" if val is not None else " (missing)")
            )

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Duplicate symbol detection
# ---------------------------------------------------------------------------

def check_duplicate_symbols(repo_root: str | Path) -> CheckResult:
    """Check that no two ``.kicad_sym`` files define the same symbol name."""
    repo_root = Path(repo_root)
    symbols_dir = repo_root / 'symbols'
    errors: List[str] = []

    if not symbols_dir.is_dir():
        return CheckResult()

    seen: Dict[str, str] = {}  # symbol_name -> filename
    for sym_file in sorted(symbols_dir.glob('*.kicad_sym')):
        try:
            symbols = parse_kicad_sym(sym_file)
        except Exception:
            continue  # parse errors are caught by check_symbol_properties
        for sym in symbols:
            if sym.name in seen:
                errors.append(
                    f"Duplicate symbol '{sym.name}' found in "
                    f"'{sym_file.name}' and '{seen[sym.name]}'"
                )
            else:
                seen[sym.name] = sym_file.name

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Footprint cross-reference check
# ---------------------------------------------------------------------------

def check_footprint_references(
    filepath: str | Path,
    repo_root: str | Path,
    *,
    symbols: Optional[List[SymbolInfo]] = None,
) -> CheckResult:
    """Validate that non-empty Footprint properties reference existing footprints.

    Footprint format is ``LibName:FootprintName`` which maps to
    ``footprints/LibName.pretty/FootprintName.kicad_mod``.

    Pass pre-parsed *symbols* to avoid re-reading the file.
    """
    filepath = Path(filepath)
    repo_root = Path(repo_root)
    errors: List[str] = []

    if symbols is None:
        try:
            symbols = parse_kicad_sym(filepath)
        except Exception as exc:
            return CheckResult(
                errors=[f"Failed to parse file (format/parse error): {exc}"],
            )

    for sym in symbols:
        fp = sym.properties.get('Footprint', '')
        if not fp or fp.strip() == '':
            continue  # Empty footprint is allowed for generic symbols

        if ':' not in fp:
            errors.append(
                f"Symbol '{sym.name}': Footprint '{fp}' has invalid format "
                f"(expected 'LibName:FootprintName')"
            )
            continue

        lib_name, fp_name = fp.split(':', 1)
        fp_path = repo_root / 'footprints' / f'{lib_name}.pretty' / f'{fp_name}.kicad_mod'
        if not fp_path.exists():
            errors.append(
                f"Symbol '{sym.name}': Footprint '{fp}' not found "
                f"(expected {fp_path.relative_to(repo_root)})"
            )

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Library-table helpers
# ---------------------------------------------------------------------------

ENV_VAR_PLACEHOLDER = '${AHARONI_LAB_KICAD_LIB}'

class LibTableEntry(NamedTuple):
    """A single entry from a KiCad library table file."""
    name: str
    type: str
    uri: str
    options: str
    descr: str


def parse_lib_table(filepath: str | Path) -> List[LibTableEntry]:
    """Parse a KiCad library table (sym-lib-table / fp-lib-table).

    Returns a list of :class:`LibTableEntry`.
    """
    filepath = Path(filepath)
    text = filepath.read_text(encoding='utf-8')
    tree = parse_sexpr(text)

    entries: List[LibTableEntry] = []
    for node in tree:
        if not isinstance(node, list):
            continue
        if node[0] != 'lib':
            continue

        # Each lib node: ['lib', ['name', 'X'], ['type', 'Y'], ...]
        fields: Dict[str, str] = {}
        for child in node[1:]:
            if isinstance(child, list) and len(child) == 2:
                fields[child[0]] = child[1]

        entries.append(LibTableEntry(
            name=fields.get('name', ''),
            type=fields.get('type', ''),
            uri=fields.get('uri', ''),
            options=fields.get('options', ''),
            descr=fields.get('descr', ''),
        ))

    return entries


def resolve_table_uri(uri: str, repo_root: str | Path) -> Path:
    """Replace ``${AHARONI_LAB_KICAD_LIB}`` in *uri* with *repo_root*."""
    repo_root = Path(repo_root)
    resolved = uri.replace(ENV_VAR_PLACEHOLDER, str(repo_root))
    return Path(resolved)


# ---------------------------------------------------------------------------
# Library-table consistency check
# ---------------------------------------------------------------------------

def check_library_tables(repo_root: str | Path) -> CheckResult:
    """Check that library tables and on-disk files are consistent.

    Checks performed:
    1. Every ``.kicad_sym`` in ``symbols/`` has a ``sym-lib-table`` entry.
    2. Every ``.pretty`` dir in ``footprints/`` has a ``fp-lib-table`` entry.
    3. All table URIs use ``${AHARONI_LAB_KICAD_LIB}``.
    4. All table entries point to files/directories that actually exist.
    """
    repo_root = Path(repo_root)
    errors: List[str] = []

    # --- sym-lib-table ---
    sym_table_path = repo_root / 'sym-lib-table'
    if sym_table_path.exists():
        sym_entries = parse_lib_table(sym_table_path)
        sym_entry_names = {e.name for e in sym_entries}

        # 1. Every .kicad_sym has a table entry
        symbols_dir = repo_root / 'symbols'
        if symbols_dir.is_dir():
            for sym_file in sorted(symbols_dir.glob('*.kicad_sym')):
                stem = sym_file.stem
                if stem not in sym_entry_names:
                    errors.append(
                        f"Symbol file '{sym_file.name}' has no sym-lib-table entry"
                    )

        # 3 & 4. URI checks
        for entry in sym_entries:
            if ENV_VAR_PLACEHOLDER not in entry.uri:
                errors.append(
                    f"sym-lib-table entry '{entry.name}': URI does not use "
                    "${{AHARONI_LAB_KICAD_LIB}}"
                )
            resolved = resolve_table_uri(entry.uri, repo_root)
            if not resolved.exists():
                errors.append(
                    f"sym-lib-table entry '{entry.name}': target does not exist "
                    f"({resolved})"
                )
    else:
        errors.append("sym-lib-table not found at repository root")

    # --- fp-lib-table ---
    fp_table_path = repo_root / 'fp-lib-table'
    if fp_table_path.exists():
        fp_entries = parse_lib_table(fp_table_path)
        fp_entry_names = {e.name for e in fp_entries}

        # 2. Every .pretty dir has a table entry
        footprints_dir = repo_root / 'footprints'
        if footprints_dir.is_dir():
            for fp_dir in sorted(footprints_dir.iterdir()):
                if fp_dir.is_dir() and fp_dir.suffix == '.pretty':
                    stem = fp_dir.stem
                    if stem not in fp_entry_names:
                        errors.append(
                            f"Footprint dir '{fp_dir.name}' has no fp-lib-table entry"
                        )

        # 3 & 4. URI checks
        for entry in fp_entries:
            if ENV_VAR_PLACEHOLDER not in entry.uri:
                errors.append(
                    f"fp-lib-table entry '{entry.name}': URI does not use "
                    "${{AHARONI_LAB_KICAD_LIB}}"
                )
            resolved = resolve_table_uri(entry.uri, repo_root)
            if not resolved.exists():
                errors.append(
                    f"fp-lib-table entry '{entry.name}': target does not exist "
                    f"({resolved})"
                )
    else:
        errors.append("fp-lib-table not found at repository root")

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(results: Dict[str, CheckResult]) -> str:
    """Format *results* as a Markdown report.

    Parameters
    ----------
    results:
        Mapping of check name / filename to its :class:`CheckResult`.
    """
    all_passed = all(r.passed for r in results.values())
    lines: List[str] = []

    if all_passed:
        lines.append("# Validation Report: PASS")
    else:
        lines.append("# Validation Report: FAIL")

    lines.append("")

    for name, result in results.items():
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"## {name}: {status}")
        if result.errors:
            lines.append("")
            for err in result.errors:
                lines.append(f"- {err}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Repo-root discovery
# ---------------------------------------------------------------------------

def _find_repo_root() -> Path:
    """Walk up from the script directory until ``sym-lib-table`` is found."""
    current = Path(__file__).resolve().parent
    while True:
        if (current / 'sym-lib-table').exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Fallback: assume we're already at the root
    return Path.cwd()


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _print_result(label: str, result: CheckResult) -> None:
    """Print a single check result in PASS/FAIL format."""
    if result.passed:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        for err in result.errors:
            print(f"  - {err}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Aharoni Lab KiCad library files.",
    )
    parser.add_argument(
        'files',
        nargs='*',
        help="One or more .kicad_sym files to validate.",
    )
    parser.add_argument(
        '--all',
        action='store_true',
        dest='check_all',
        help="Check all .kicad_sym files in the symbols/ directory.",
    )
    parser.add_argument(
        '--check-tables',
        action='store_true',
        help="Check library table consistency.",
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help="Output a Markdown report (implies --all and --check-tables).",
    )

    args = parser.parse_args(argv)
    repo_root = _find_repo_root()

    results: Dict[str, CheckResult] = {}

    # Collect files to check
    files_to_check: List[Path] = []
    if args.files:
        files_to_check.extend(Path(f) for f in args.files)

    if args.check_all or args.report:
        symbols_dir = repo_root / 'symbols'
        if symbols_dir.is_dir():
            files_to_check.extend(sorted(symbols_dir.glob('*.kicad_sym')))

    # Run symbol property checks and cross-reference checks
    for fpath in files_to_check:
        # Parse once, reuse for both checks
        try:
            symbols = parse_kicad_sym(fpath)
        except Exception as exc:
            result = CheckResult(
                errors=[f"Failed to parse file (format/parse error): {exc}"],
            )
            results[str(fpath)] = result
            if not args.report:
                _print_result(str(fpath), result)
            continue

        result = check_symbol_properties(fpath, symbols=symbols)
        results[str(fpath)] = result
        if not args.report:
            _print_result(str(fpath), result)

        # Cross-reference check (footprint references)
        xref_result = check_footprint_references(fpath, repo_root, symbols=symbols)
        if not xref_result.passed:
            xref_key = f"{fpath} [cross-ref]"
            results[xref_key] = xref_result
            if not args.report:
                _print_result(xref_key, xref_result)

    # Run duplicate symbol check
    if args.check_all or args.report:
        dup_result = check_duplicate_symbols(repo_root)
        results['duplicate-symbols'] = dup_result
        if not args.report:
            _print_result('duplicate-symbols', dup_result)

    # Run table consistency check
    if args.check_tables or args.report:
        table_result = check_library_tables(repo_root)
        results['library-tables'] = table_result
        if not args.report:
            _print_result('library-tables', table_result)

    # Report mode
    if args.report:
        print(generate_report(results))

    # Exit code
    if not results:
        # Nothing was checked -- show help
        parser.print_help()
        return 0

    return 0 if all(r.passed for r in results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
