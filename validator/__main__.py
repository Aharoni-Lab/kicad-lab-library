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
    check_naming_conventions,
    check_pin_counts,
    check_pin_pad_cross_validation,
    check_reference_prefix,
    check_symbol_flags,
    check_symbol_properties,
    check_uncategorized_files,
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


def _run_footprint_checks(
    fp_files: List[Path], rules, results: Dict[str, CheckResult], *, quiet: bool,
) -> None:
    """Run all footprint checks on the given files."""
    from validator.footprint_checks import (
        check_duplicate_pad_numbers, check_footprint_layers,
        check_footprint_pads, check_footprint_properties,
        parse_kicad_mod,
    )
    for fp_file in fp_files:
        try:
            fp_info = parse_kicad_mod(fp_file)
        except Exception as exc:
            err_result = CheckResult(
                errors=[f"Failed to parse footprint: {exc}"],
            )
            results[f"{fp_file}"] = err_result
            if not quiet:
                _print_result(str(fp_file), err_result)
            continue

        for check_fn, tag in [
            (lambda f, i: check_footprint_layers(f, rules, info=i), "layers"),
            (lambda f, i: check_footprint_pads(f, info=i), "pads"),
            (lambda f, i: check_duplicate_pad_numbers(f, info=i, rules=rules), "dup-pads"),
            (lambda f, i: check_footprint_properties(f, rules, info=i), "fp-props"),
        ]:
            result = check_fn(fp_file, fp_info)
            results[f"{fp_file} [{tag}]"] = result
            if not quiet:
                _print_result(f"{fp_file} [{tag}]", result)


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
        '--footprint-files',
        nargs='*',
        default=[],
        help="One or more .kicad_mod files to validate.",
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
        help="Run footprint layer/pad validation on all footprints.",
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help="Output a Markdown report. Runs structure checks (tables, "
             "naming, duplicates) globally. Symbol and footprint checks "
             "run on files passed via positional args / --footprint-files, "
             "or on everything if --all / --check-footprints is also set.",
    )
    parser.add_argument(
        '--config',
        default=None,
        help="Path to library_rules.yaml (default: auto-detect from repo root).",
    )
    parser.add_argument('--check-generated-tables', action='store_true',
        help="Check that library tables match auto-generated content.")
    parser.add_argument('--generate-tables', action='store_true',
        help="Write auto-generated library tables to disk.")
    parser.add_argument('--renders-url', default=None,
        help="Base URL for rendered SVG previews (used in --report).")
    parser.add_argument('--renders-dir', default=None,
        help="Local directory containing rendered SVGs (used in --report).")

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

    # Collect symbol files to check
    files_to_check: List[Path] = []
    if args.files:
        files_to_check.extend(Path(f) for f in args.files)

    if args.check_all:
        symbols_dir = repo_root / 'symbols'
        if symbols_dir.is_dir():
            files_to_check.extend(sorted(symbols_dir.glob('*.kicad_sym')))

    # Run symbol property checks and cross-reference checks
    all_parsed: Dict[Path, list] = {}  # accumulate for duplicate check
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

        all_parsed[fpath] = symbols

        result = check_symbol_properties(fpath, rules, symbols=symbols)
        results[str(fpath)] = result
        if not args.report:
            _print_result(str(fpath), result)

        # Cross-reference check (footprint references)
        xref_key = f"{fpath} [cross-ref]"
        xref_result = check_footprint_references(fpath, repo_root, symbols=symbols)
        results[xref_key] = xref_result
        if not args.report:
            _print_result(xref_key, xref_result)

        # Reference prefix check
        prefix_key = f"{fpath} [ref-prefix]"
        prefix_result = check_reference_prefix(fpath, rules, symbols=symbols)
        results[prefix_key] = prefix_result
        if not args.report:
            _print_result(prefix_key, prefix_result)

        # Pin count check
        pin_key = f"{fpath} [pin-count]"
        pin_result = check_pin_counts(fpath, rules, symbols=symbols)
        results[pin_key] = pin_result
        if not args.report:
            _print_result(pin_key, pin_result)

        # Symbol flags check
        flags_key = f"{fpath} [flags]"
        flags_result = check_symbol_flags(fpath, rules, symbols=symbols)
        results[flags_key] = flags_result
        if not args.report:
            _print_result(flags_key, flags_result)

        # Pin/pad cross-validation
        pp_key = f"{fpath} [pin-pad]"
        pp_result = check_pin_pad_cross_validation(fpath, repo_root, symbols=symbols)
        results[pp_key] = pp_result
        if not args.report:
            _print_result(pp_key, pp_result)

    # Run duplicate symbol check (always global)
    if args.check_all or args.report:
        dup_result = check_duplicate_symbols(
            repo_root, parsed_symbols=all_parsed or None,
        )
        results['duplicate-symbols'] = dup_result
        if not args.report:
            _print_result('duplicate-symbols', dup_result)

    # Run table consistency check (always global)
    if args.check_tables or args.report:
        table_result = check_library_tables(repo_root)
        results['library-tables'] = table_result
        if not args.report:
            _print_result('library-tables', table_result)

    # Run naming convention checks (always global)
    if args.check_all or args.report:
        naming_result = check_naming_conventions(repo_root, rules)
        results['naming-conventions'] = naming_result
        if not args.report:
            _print_result('naming-conventions', naming_result)

    # Run uncategorized file checks (always global)
    if args.check_all or args.report:
        uncat_result = check_uncategorized_files(repo_root, rules)
        results['uncategorized-files'] = uncat_result
        if not args.report:
            _print_result('uncategorized-files', uncat_result)

    # Run footprint checks — specific files or all
    fp_files: List[Path] = [Path(f) for f in args.footprint_files]
    if args.check_footprints:
        footprints_dir = repo_root / 'footprints'
        if footprints_dir.is_dir():
            for pretty_dir in sorted(footprints_dir.iterdir()):
                if pretty_dir.is_dir() and pretty_dir.suffix == '.pretty':
                    fp_files.extend(sorted(pretty_dir.glob('*.kicad_mod')))

    if fp_files:
        _run_footprint_checks(fp_files, rules, results, quiet=args.report)

    # Run table generation check (always global)
    if args.check_generated_tables or args.report:
        from validator.table_gen import check_tables_match_generated
        gen_result = check_tables_match_generated(repo_root, rules=rules)
        results['table-generation'] = gen_result
        if not args.report:
            _print_result('table-generation', gen_result)

    if args.generate_tables:
        from validator.table_gen import write_generated_tables
        write_generated_tables(repo_root, rules=rules)
        print("Library tables written to disk.")

    # Report mode
    if args.report:
        # Collect available render files
        render_files: List[str] = []
        if args.renders_dir:
            renders_path = Path(args.renders_dir)
            if renders_path.is_dir():
                render_files = [f.name for f in sorted(renders_path.glob('*.svg'))]
        # Build symbol names per file for per-symbol rows
        symbol_names: Dict[str, List[str]] = {}
        for fpath, syms in all_parsed.items():
            symbol_names[str(fpath)] = [s.name for s in syms]
        print(generate_report(
            results,
            renders_url=args.renders_url,
            render_files=render_files,
            symbol_names=symbol_names,
        ))

    # Exit code
    if not results:
        # Nothing was checked -- show help
        parser.print_help()
        return 0

    return 0 if all(r.passed for r in results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
