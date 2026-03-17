"""CLI entry point for the validator: ``python -m validator``."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

from validator.checks import (
    CheckResult,
    check_duplicate_symbols,
    check_footprint_references,
    check_library_tables,
    check_pin_counts,
    check_reference_prefix,
    check_symbol_properties,
    parse_kicad_sym,
)
from validator.config import load_rules
from validator.report import generate_report


# ---------------------------------------------------------------------------
# Repo-root discovery
# ---------------------------------------------------------------------------

def _find_repo_root() -> Path:
    """Walk up from CWD until ``sym-lib-table`` is found."""
    current = Path.cwd().resolve()
    while True:
        if (current / 'sym-lib-table').exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
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
        '--check-footprints',
        action='store_true',
        help="Run footprint layer/pad validation.",
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help="Output a Markdown report (implies --all and --check-tables).",
    )
    parser.add_argument(
        '--config',
        default=None,
        help="Path to library_rules.yaml (default: auto-detect from repo root).",
    )
    parser.add_argument(
        '--generate-tables',
        action='store_true',
        help="Generate library tables and check they match on-disk versions.",
    )

    args = parser.parse_args(argv)
    repo_root = _find_repo_root()

    # Load rules
    config_path = Path(args.config) if args.config else repo_root / 'library_rules.yaml'
    if config_path.exists():
        rules = load_rules(config_path)
    else:
        print(f"Warning: config not found at {config_path}, using defaults",
              file=sys.stderr)
        from validator.config import LibraryRules, PropertyRule
        rules = LibraryRules()

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
        # Parse once, reuse for all checks
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

        result = check_symbol_properties(fpath, rules, symbols=symbols)
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

        # Reference prefix check
        prefix_result = check_reference_prefix(fpath, rules, symbols=symbols)
        if not prefix_result.passed:
            prefix_key = f"{fpath} [ref-prefix]"
            results[prefix_key] = prefix_result
            if not args.report:
                _print_result(prefix_key, prefix_result)

        # Pin count check
        pin_result = check_pin_counts(fpath, rules, symbols=symbols)
        if not pin_result.passed:
            pin_key = f"{fpath} [pin-count]"
            results[pin_key] = pin_result
            if not args.report:
                _print_result(pin_key, pin_result)

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

    # Run footprint checks
    if args.check_footprints:
        from validator.footprint_checks import check_footprint_layers, check_footprint_pads
        footprints_dir = repo_root / 'footprints'
        if footprints_dir.is_dir():
            for pretty_dir in sorted(footprints_dir.iterdir()):
                if pretty_dir.is_dir() and pretty_dir.suffix == '.pretty':
                    for fp_file in sorted(pretty_dir.glob('*.kicad_mod')):
                        layer_result = check_footprint_layers(fp_file, rules)
                        if not layer_result.passed:
                            results[f"{fp_file} [layers]"] = layer_result
                            if not args.report:
                                _print_result(f"{fp_file} [layers]", layer_result)

                        pad_result = check_footprint_pads(fp_file)
                        if not pad_result.passed:
                            results[f"{fp_file} [pads]"] = pad_result
                            if not args.report:
                                _print_result(f"{fp_file} [pads]", pad_result)

    # Run table generation check
    if args.generate_tables:
        from validator.table_gen import check_tables_match_generated
        gen_result = check_tables_match_generated(repo_root)
        results['table-generation'] = gen_result
        if not args.report:
            _print_result('table-generation', gen_result)

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
