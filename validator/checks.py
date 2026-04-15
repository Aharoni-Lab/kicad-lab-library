"""Validation checks for KiCad library files.

All check functions return a :class:`CheckResult`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from validator.config import LibraryRules
from validator.lib_table import LibTableEntry, parse_lib_table
from validator.sexpr import extract_properties, parse_sexpr


# ---------------------------------------------------------------------------
# Symbol file helpers
# ---------------------------------------------------------------------------

@dataclass
class SymbolInfo:
    """Lightweight container for a parsed KiCad symbol."""
    name: str
    properties: Dict[str, str]
    pin_count: int = 0
    in_bom: Optional[bool] = None
    on_board: Optional[bool] = None


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


def _extract_flags(node: list) -> Dict[str, bool]:
    """Extract boolean flags like ``(in_bom yes)`` from a symbol node."""
    flags: Dict[str, bool] = {}
    for child in node:
        if isinstance(child, list) and len(child) == 2:
            if child[0] in ('in_bom', 'on_board'):
                flags[child[0]] = child[1] == 'yes'
    return flags


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
        props = extract_properties(node)
        pin_count = _count_pins(node)
        flags = _extract_flags(node)
        symbols.append(SymbolInfo(
            name=name,
            properties=props,
            pin_count=pin_count,
            in_bom=flags.get('in_bom'),
            on_board=flags.get('on_board'),
        ))

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
      (``~`` is treated as empty for any property).
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
                if value is None or value.strip() in ('', '~'):
                    errors.append(
                        f"Symbol '{sym.name}': {prop_name} property is missing or empty"
                    )
                    continue

            # Pattern check (only if value is present and non-empty)
            if rule.compiled_pattern is not None and value and value.strip() not in ('', '~'):
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
# Symbol flag checks (in_bom, on_board)
# ---------------------------------------------------------------------------

def check_symbol_flags(
    filepath: str | Path,
    rules: LibraryRules,
    *,
    symbols: Optional[List[SymbolInfo]] = None,
) -> CheckResult:
    """Check that symbol in_bom/on_board flags match rules.

    Uses ``rules.symbol_flags`` for global defaults, with per-category
    overrides via ``category.flags``.
    """
    filepath = Path(filepath)
    errors: List[str] = []

    if rules.symbol_flags is None:
        return CheckResult()

    if symbols is None:
        try:
            symbols = parse_kicad_sym(filepath)
        except Exception as exc:
            return CheckResult(
                errors=[f"Failed to parse file (format/parse error): {exc}"],
            )

    stem = filepath.stem
    category = rules.categories.get(stem)

    for sym in symbols:
        # Determine expected flags (category override > global)
        expected_in_bom = rules.symbol_flags.in_bom
        expected_on_board = rules.symbol_flags.on_board
        if category and category.flags:
            if category.flags.in_bom is not None:
                expected_in_bom = category.flags.in_bom
            if category.flags.on_board is not None:
                expected_on_board = category.flags.on_board

        if expected_in_bom is not None and sym.in_bom is not None:
            if sym.in_bom != expected_in_bom:
                errors.append(
                    f"Symbol '{sym.name}': in_bom is {str(sym.in_bom).lower()}, "
                    f"expected {str(expected_in_bom).lower()}"
                )
        if expected_on_board is not None and sym.on_board is not None:
            if sym.on_board != expected_on_board:
                errors.append(
                    f"Symbol '{sym.name}': on_board is {str(sym.on_board).lower()}, "
                    f"expected {str(expected_on_board).lower()}"
                )

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Duplicate symbol detection
# ---------------------------------------------------------------------------

def check_duplicate_symbols(
    repo_root: str | Path,
    *,
    parsed_symbols: Optional[Dict[Path, List[SymbolInfo]]] = None,
) -> CheckResult:
    """Check that no two ``.kicad_sym`` files define the same symbol name.

    If *parsed_symbols* is provided (a mapping of filepath to parsed symbols),
    those are used directly to avoid re-parsing files.
    """
    repo_root = Path(repo_root)
    symbols_dir = repo_root / 'symbols'
    errors: List[str] = []

    if not symbols_dir.is_dir():
        return CheckResult()

    seen: Dict[str, str] = {}  # symbol_name -> filename

    if parsed_symbols is not None:
        # Use pre-parsed data
        for sym_file, symbols in sorted(parsed_symbols.items(), key=lambda t: t[0]):
            for sym in symbols:
                if sym.name in seen:
                    errors.append(
                        f"Duplicate symbol '{sym.name}' found in "
                        f"'{sym_file.name}' and '{seen[sym.name]}'"
                    )
                else:
                    seen[sym.name] = sym_file.name
    else:
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
# Footprint helpers
# ---------------------------------------------------------------------------

def _resolve_footprint_path(fp_ref: str, repo_root: Path) -> Path:
    """Resolve ``LibName:FootprintName`` to a filesystem path."""
    lib_name, fp_name = fp_ref.split(':', 1)
    return repo_root / 'footprints' / f'{lib_name}.pretty' / f'{fp_name}.kicad_mod'


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

        fp_path = _resolve_footprint_path(fp, repo_root)
        if not fp_path.exists():
            errors.append(
                f"Symbol '{sym.name}': Footprint '{fp}' not found "
                f"(expected {fp_path.relative_to(repo_root)})"
            )

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Pin/pad cross-validation
# ---------------------------------------------------------------------------

def check_pin_pad_cross_validation(
    filepath: str | Path,
    repo_root: str | Path,
    *,
    symbols: Optional[List[SymbolInfo]] = None,
) -> CheckResult:
    """Cross-validate symbol pin counts against footprint pad counts.

    For each symbol whose Footprint property points to an existing ``.kicad_mod``,
    compare the number of electrical pins with the number of electrical pads.
    """
    from validator.footprint_checks import parse_kicad_mod, _get_electrical_pad_count

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
        if not fp or ':' not in fp:
            continue

        fp_path = _resolve_footprint_path(fp, repo_root)
        if not fp_path.exists():
            continue  # Missing footprints are caught by check_footprint_references

        try:
            fp_info = parse_kicad_mod(fp_path)
        except Exception:
            continue

        electrical_pads = _get_electrical_pad_count(fp_info)
        if electrical_pads == 0:
            continue  # No electrical pads to compare

        if sym.pin_count != electrical_pads:
            errors.append(
                f"Symbol '{sym.name}': has {sym.pin_count} pins but footprint "
                f"'{fp}' has {electrical_pads} electrical pads"
            )

    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Naming convention checks
# ---------------------------------------------------------------------------

def check_naming_conventions(
    repo_root: str | Path,
    rules: LibraryRules,
) -> CheckResult:
    """Check that symbol files and footprint dirs follow naming conventions from rules."""
    repo_root = Path(repo_root)
    errors: List[str] = []
    if rules.naming is None:
        return CheckResult()
    if rules.naming.symbol_file_pattern:
        pattern = re.compile(rules.naming.symbol_file_pattern)
        symbols_dir = repo_root / 'symbols'
        if symbols_dir.is_dir():
            for sym_file in sorted(symbols_dir.glob('*.kicad_sym')):
                if not pattern.match(sym_file.name):
                    errors.append(f"Symbol file '{sym_file.name}' does not match naming pattern '{rules.naming.symbol_file_pattern}'")
    if rules.naming.footprint_dir_pattern:
        pattern = re.compile(rules.naming.footprint_dir_pattern)
        footprints_dir = repo_root / 'footprints'
        if footprints_dir.is_dir():
            for fp_dir in sorted(footprints_dir.iterdir()):
                if fp_dir.is_dir() and fp_dir.suffix == '.pretty':
                    if not pattern.match(fp_dir.name):
                        errors.append(f"Footprint dir '{fp_dir.name}' does not match naming pattern '{rules.naming.footprint_dir_pattern}'")
    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Uncategorized file checks
# ---------------------------------------------------------------------------

def check_uncategorized_files(
    repo_root: str | Path,
    rules: LibraryRules,
) -> CheckResult:
    """Check that all symbol files have a corresponding category in rules."""
    repo_root = Path(repo_root)
    errors: List[str] = []
    symbols_dir = repo_root / 'symbols'
    if symbols_dir.is_dir():
        for sym_file in sorted(symbols_dir.glob('*.kicad_sym')):
            stem = sym_file.stem
            if stem not in rules.categories:
                errors.append(f"Symbol file '{sym_file.name}' has no category defined in library_rules.yaml (stem '{stem}' not found in categories)")
    return CheckResult(errors=errors)


# ---------------------------------------------------------------------------
# Library-table helpers
# ---------------------------------------------------------------------------

ENV_VAR_PLACEHOLDER = '${AHARONI_LAB_KICAD_LIB}'


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
