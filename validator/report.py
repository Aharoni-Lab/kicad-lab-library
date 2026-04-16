"""Markdown report generation for validation results."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from validator.checks import CheckResult

# Strip absolute paths down to the repo-relative portion.
_PATH_RE = re.compile(r"^.*?(?=symbols[/\\]|footprints[/\\]|3dmodels[/\\])")

# Check tags that appear as "[tag]" suffixes on per-file keys.
_SYMBOL_CHECKS = [
    ("properties", "Props"),
    ("cross-ref", "Cross-ref"),
    ("ref-prefix", "Prefix"),
    ("pin-count", "Pins"),
    ("flags", "Flags"),
    ("pin-pad", "Pin/Pad"),
]

_FOOTPRINT_CHECKS = [
    ("layers", "Layers"),
    ("pads", "Pads"),
    ("dup-pads", "Dup Pads"),
    ("fp-props", "Props"),
]

_STRUCTURE_CHECKS = [
    ("duplicate-symbols", "Duplicate symbols"),
    ("library-tables", "Library tables"),
    ("naming-conventions", "Naming conventions"),
    ("uncategorized-files", "Uncategorized files"),
    ("table-generation", "Table generation"),
]

_THUMB_HEIGHT = 96


def _short_name(name: str) -> str:
    """Shorten absolute paths to repo-relative paths for display."""
    return _PATH_RE.sub("", name).replace("\\", "/")


def _icon(result: CheckResult) -> str:
    return "pass" if result.passed else "FAIL"


def _symbol_icon(result: CheckResult, sym_name: str) -> str:
    """Return per-symbol pass/fail by checking if any errors mention this symbol."""
    if result.passed:
        return "pass"
    # Check if any error message mentions this specific symbol
    for err in result.errors:
        if f"'{sym_name}'" in err:
            return "FAIL"
    return "pass"


def _parse_key(key: str) -> Tuple[str, str]:
    """Split 'path [tag]' into (path, tag).  Plain keys return (key, '')."""
    m = re.match(r"^(.+?) \[(.+)]$", key)
    if m:
        return m.group(1), m.group(2)
    return key, ""


def _find_render(name: str, render_files: List[str]) -> Optional[str]:
    """Find a render SVG that matches a symbol or footprint name."""
    name_lower = name.lower()
    for rf in render_files:
        rf_lower = rf.lower()
        # KiCad CLI names renders like "symbolname_unit1.svg" or "footprintname.svg"
        rf_stem = rf_lower.rsplit(".", 1)[0]
        # Exact match (footprints) or prefix match with _unit suffix (symbols)
        if rf_stem == name_lower or rf_stem.startswith(name_lower + "_unit"):
            return rf
    return None


def _render_cell(
    name: str,
    render_files: List[str],
    renders_url: str,
) -> str:
    """Inline thumbnail linked to the HTML viewer."""
    render = _find_render(name, render_files)
    if render:
        html_page = render.rsplit(".", 1)[0] + ".html"
        return (
            f'<a href="{renders_url}/{html_page}">'
            f'<img src="{renders_url}/{render}" height="{_THUMB_HEIGHT}">'
            f'</a>'
        )
    return ""


def generate_report(
    results: Dict[str, CheckResult],
    *,
    renders_url: Optional[str] = None,
    render_files: Optional[List[str]] = None,
    symbol_names: Optional[Dict[str, List[str]]] = None,
) -> str:
    """Format *results* as a compact Markdown report."""
    all_passed = all(r.passed for r in results.values())
    render_files = render_files or []
    symbol_names = symbol_names or {}
    lines: List[str] = []

    status = "PASS" if all_passed else "FAIL"
    lines.append(f"# Validation Report: {status}")
    lines.append("")

    # Collect per-file results: {short_path: {tag: CheckResult}}
    symbol_files: Dict[str, Dict[str, CheckResult]] = defaultdict(dict)
    footprint_files: Dict[str, Dict[str, CheckResult]] = defaultdict(dict)
    structure_results: Dict[str, CheckResult] = {}
    errors: List[Tuple[str, str]] = []  # (location, error_msg)

    for key, result in results.items():
        path, tag = _parse_key(key)
        short = _short_name(path)

        if tag == "":
            if short.endswith(".kicad_sym"):
                symbol_files[short]["properties"] = result
            elif short.endswith(".kicad_mod"):
                footprint_files[short]["parse"] = result
            else:
                structure_results[short] = result
        elif short.endswith(".kicad_sym"):
            symbol_files[short][tag] = result
        elif short.endswith(".kicad_mod"):
            footprint_files[short][tag] = result

        if not result.passed:
            for err in result.errors:
                label = f"{short} [{tag}]" if tag else short
                errors.append((label, err))

    has_renders = bool(render_files and renders_url)

    # Build mapping: short_path -> [symbol_name, ...]
    # symbol_names keys are absolute paths; normalize to short paths
    sym_names_by_short: Dict[str, List[str]] = {}
    for abs_path, names in symbol_names.items():
        short = _short_name(abs_path)
        sym_names_by_short[short] = names

    # --- Symbol table ---
    if symbol_files:
        lines.append("## Symbols")
        lines.append("")
        header_cols = ["Symbol", "Library"] + [label for _, label in _SYMBOL_CHECKS]
        if has_renders:
            header_cols.append("Preview")
        lines.append("| " + " | ".join(header_cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(header_cols)) + " |")

        for path in sorted(symbol_files):
            checks = symbol_files[path]
            lib_name = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            names = sym_names_by_short.get(path, [])

            if not names:
                # Fallback: one row for the whole file
                cols = [f"`{lib_name}`", f"`{lib_name}`"]
                for tag, _ in _SYMBOL_CHECKS:
                    cols.append(_icon(checks[tag]) if tag in checks else "-")
                if has_renders:
                    cols.append("")
                lines.append("| " + " | ".join(cols) + " |")
            else:
                for sym_name in names:
                    cols = [f"`{sym_name}`", f"`{lib_name}`"]
                    for tag, _ in _SYMBOL_CHECKS:
                        if tag in checks:
                            cols.append(_symbol_icon(checks[tag], sym_name))
                        else:
                            cols.append("-")
                    if has_renders:
                        cols.append(
                            _render_cell(sym_name, render_files, renders_url)
                        )
                    lines.append("| " + " | ".join(cols) + " |")
        lines.append("")

    # --- Footprint table ---
    if footprint_files:
        lines.append("## Footprints")
        lines.append("")
        header_cols = ["Footprint"] + [label for _, label in _FOOTPRINT_CHECKS]
        if has_renders:
            header_cols.append("Preview")
        lines.append("| " + " | ".join(header_cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(header_cols)) + " |")

        for path in sorted(footprint_files):
            checks = footprint_files[path]
            fp_name = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            cols = [f"`{fp_name}`"]
            for tag, _ in _FOOTPRINT_CHECKS:
                cols.append(_icon(checks[tag]) if tag in checks else "-")
            if has_renders:
                cols.append(
                    _render_cell(fp_name, render_files, renders_url)
                )
            lines.append("| " + " | ".join(cols) + " |")
        lines.append("")

    # --- Structure table ---
    struct_items = [
        (label, structure_results[key])
        for key, label in _STRUCTURE_CHECKS
        if key in structure_results
    ]
    if struct_items:
        lines.append("## Structure")
        lines.append("")
        lines.append("| Check | Result |")
        lines.append("| --- | --- |")
        for label, result in struct_items:
            lines.append(f"| {label} | {_icon(result)} |")
        lines.append("")

    # --- Error details ---
    if errors:
        lines.append("<details>")
        lines.append(f"<summary>Errors ({len(errors)})</summary>")
        lines.append("")
        for location, msg in errors:
            lines.append(f"- **{location}**: {msg}")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    return "\n".join(lines)
