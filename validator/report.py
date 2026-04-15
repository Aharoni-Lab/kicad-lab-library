"""Markdown report generation for validation results."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Tuple

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


def _short_name(name: str) -> str:
    """Shorten absolute paths to repo-relative paths for display."""
    return _PATH_RE.sub("", name).replace("\\", "/")


def _icon(result: CheckResult) -> str:
    return "pass" if result.passed else "FAIL"


def _parse_key(key: str) -> Tuple[str, str]:
    """Split 'path [tag]' into (path, tag).  Plain keys return (key, '')."""
    m = re.match(r"^(.+?) \[(.+)]$", key)
    if m:
        return m.group(1), m.group(2)
    return key, ""


def generate_report(results: Dict[str, CheckResult]) -> str:
    """Format *results* as a compact Markdown report."""
    all_passed = all(r.passed for r in results.values())
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
                # Symbol property check (no tag)
                symbol_files[short]["properties"] = result
            elif short.endswith(".kicad_mod"):
                # Footprint parse error (no tag)
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

    # --- Symbol table ---
    if symbol_files:
        lines.append("## Symbols")
        lines.append("")
        header_cols = ["File"] + [label for _, label in _SYMBOL_CHECKS]
        lines.append("| " + " | ".join(header_cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(header_cols)) + " |")

        for path in sorted(symbol_files):
            checks = symbol_files[path]
            filename = path.rsplit("/", 1)[-1]
            cols = [f"`{filename}`"]
            for tag, _ in _SYMBOL_CHECKS:
                if tag in checks:
                    cols.append(_icon(checks[tag]))
                else:
                    cols.append("-")
            lines.append("| " + " | ".join(cols) + " |")
        lines.append("")

    # --- Footprint table ---
    if footprint_files:
        lines.append("## Footprints")
        lines.append("")
        header_cols = ["File"] + [label for _, label in _FOOTPRINT_CHECKS]
        lines.append("| " + " | ".join(header_cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(header_cols)) + " |")

        for path in sorted(footprint_files):
            checks = footprint_files[path]
            filename = path.rsplit("/", 1)[-1]
            cols = [f"`{filename}`"]
            for tag, _ in _FOOTPRINT_CHECKS:
                if tag in checks:
                    cols.append(_icon(checks[tag]))
                else:
                    cols.append("-")
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
