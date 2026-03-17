"""Validation checks for KiCad library files.

All check functions return a :class:`CheckResult`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

from validator.config import LibraryRules
from validator.sexpr import parse_sexpr


# ---------------------------------------------------------------------------
# Symbol file helpers
# ---------------------------------------------------------------------------

class SymbolInfo(NamedTuple):
    """Lightweight container for a parsed KiCad symbol."""
    name: str
    properties: Dict[str, str]
    pin_count: int = 0


def _extract_properties(sexpr_node: list) -> Dict[str, str]:
    """Return a dict of property name -> value from a symbol S-expression node."""
    props: Dict[str, str] = {}
    for child in sexpr_node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == 'property':
            props[child[1]] = child[2]
    return props


def _count_pins(sexpr_node: list) -> int:
    """Count the number of ``pin`` nodes in a symbol and all its child symbols."""
    count = 0
    for child in sexpr_node:
        if isinstance(child, list) and len(child) >= 1:
            if child[0] == 'pin':
                count += 1
            # Recurse into child symbols (e.g. TestResistor_1_1)
            elif child[0] == 'symbol':
                count += _count_pins(child)
    return count


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
        pin_count = _count_pins(node)
        symbols.append(SymbolInfo(name=name, properties=props, pin_count=pin_count))

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
# Symbol property checks (YAML-driven)
# ---------------------------------------------------------------------------

def check_symbol_properties(
    filepath: str | Path,
    rules: LibraryRules,
    *,
    symbols: Optional[List[SymbolInfo]] = None,
) -> CheckResult:
    """Validate symbol properties against rules from ``library_rules.yaml``.

    Every property in ``rules.global_symbol_properties`` is checked:
    - If ``required`` is True, the property must exist and be non-empty
      (also rejects ``~`` for Datasheet).
    - If ``pattern`` is set, the value must match the regex.
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
        for prop_name, rule in rules.global_symbol_properties.items():
            value = sym.properties.get(prop_name)

            if rule.required:
                if value is None or value.strip() == '':
                    errors.append(
                        f"Symbol '{sym.name}': {prop_name} property is missing or empty"
                    )
                    continue
                # Special case: Datasheet '~' means empty in KiCad
                if prop_name == 'Datasheet' and value.strip() == '~':
                    errors.append(
                        f"Symbol '{sym.name}': {prop_name} property is missing or empty"
                    )
                    continue

            # Pattern check (only if value is present and non-empty)
            if rule.compiled_pattern is not None and value and value.strip():
                if not rule.compiled_pattern.match(value):
                    errors.append(
                        f"Symbol '{sym.name}': {prop_name} property must match "
                        f"'{rule.pattern}' (got '{value}')"
                    )

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Reference prefix checks
# ---------------------------------------------------------------------------

def check_reference_prefix(
    filepath: str | Path,
    rules: LibraryRules,
    *,
    symbols: Optional[List[SymbolInfo]] = None,
) -> CheckResult:
    """Check that symbol Reference prefixes match category rules.

    For categories with subcategories, the symbol is matched by its
    Reference prefix against subcategory rules.
    """
    filepath = Path(filepath)
    errors: List[str] = []

    # Determine category from filename stem
    stem = filepath.stem
    category = rules.categories.get(stem)
    if category is None:
        return CheckResult()  # No rules for this file

    if symbols is None:
        try:
            symbols = parse_kicad_sym(filepath)
        except Exception as exc:
            return CheckResult(
                errors=[f"Failed to parse file (format/parse error): {exc}"],
            )

    for sym in symbols:
        ref = sym.properties.get('Reference', '')

        if category.subcategories:
            # Check if ref matches any subcategory prefix
            matched = False
            for sub_name, sub in category.subcategories.items():
                if sub.reference_prefix and ref == sub.reference_prefix:
                    matched = True
                    break
            if not matched:
                valid_prefixes = [
                    s.reference_prefix
                    for s in category.subcategories.values()
                    if s.reference_prefix
                ]
                errors.append(
                    f"Symbol '{sym.name}': Reference prefix '{ref}' does not match "
                    f"any subcategory in {stem} (expected one of {valid_prefixes})"
                )
        elif category.reference_prefix:
            if ref != category.reference_prefix:
                errors.append(
                    f"Symbol '{sym.name}': Reference prefix '{ref}' does not match "
                    f"expected '{category.reference_prefix}' for {stem}"
                )

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Pin count checks
# ---------------------------------------------------------------------------

def check_pin_counts(
    filepath: str | Path,
    rules: LibraryRules,
    *,
    symbols: Optional[List[SymbolInfo]] = None,
) -> CheckResult:
    """Check that symbol pin counts are within allowed ranges.

    Uses category/subcategory rules from ``library_rules.yaml``.
    """
    filepath = Path(filepath)
    errors: List[str] = []

    stem = filepath.stem
    category = rules.categories.get(stem)
    if category is None:
        return CheckResult()

    if symbols is None:
        try:
            symbols = parse_kicad_sym(filepath)
        except Exception as exc:
            return CheckResult(
                errors=[f"Failed to parse file (format/parse error): {exc}"],
            )

    for sym in symbols:
        ref = sym.properties.get('Reference', '')
        pin_range = None

        if category.subcategories:
            # Find matching subcategory by reference prefix
            for sub_name, sub in category.subcategories.items():
                if sub.reference_prefix and ref == sub.reference_prefix:
                    pin_range = sub.pins
                    break
        else:
            pin_range = category.pins

        if pin_range is None:
            continue

        if pin_range.min is not None and sym.pin_count < pin_range.min:
            errors.append(
                f"Symbol '{sym.name}': has {sym.pin_count} pins, "
                f"minimum is {pin_range.min}"
            )
        if pin_range.max is not None and sym.pin_count > pin_range.max:
            errors.append(
                f"Symbol '{sym.name}': has {sym.pin_count} pins, "
                f"maximum is {pin_range.max}"
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
