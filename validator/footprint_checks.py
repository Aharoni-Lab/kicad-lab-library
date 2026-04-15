"""Footprint-specific validation checks (layers, pads)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from validator.checks import CheckResult
from validator.config import LibraryRules
from validator.sexpr import extract_properties, parse_sexpr


# ---------------------------------------------------------------------------
# FootprintInfo
# ---------------------------------------------------------------------------

@dataclass
class FootprintInfo:
    """Parsed footprint metadata."""
    name: str
    layers: Set[str]
    properties: Dict[str, str]
    pad_numbers: List[str] = field(default_factory=list)
    pad_types: List[str] = field(default_factory=list)
    attribute: Optional[str] = None

    @property
    def pad_count(self) -> int:
        return len(self.pad_numbers)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _collect_layers(node: list) -> Set[str]:
    """Recursively collect all layer references from a footprint S-expression."""
    layers: Set[str] = set()
    for child in node:
        if isinstance(child, list) and len(child) >= 2:
            if child[0] == 'layer':
                # Direct layer reference: (layer "F.Cu")
                layers.add(child[1])
            elif child[0] == 'layers':
                # Pad layers: (layers "F.Cu" "F.Paste" "F.Mask")
                for item in child[1:]:
                    if isinstance(item, str):
                        layers.add(item)
            else:
                # Recurse
                layers.update(_collect_layers(child))
    return layers


def _collect_pads(tree: list) -> tuple[List[str], List[str]]:
    """Collect pad numbers and types in a single pass over the footprint tree."""
    numbers: List[str] = []
    types: List[str] = []
    for child in tree:
        if isinstance(child, list) and len(child) >= 3 and child[0] == 'pad':
            numbers.append(child[1])
            types.append(child[2])
        elif isinstance(child, list) and len(child) >= 2 and child[0] == 'pad':
            numbers.append(child[1])
    return numbers, types


def _extract_attribute(tree: list) -> Optional[str]:
    """Extract footprint attribute (smd, through_hole, etc.) from the tree."""
    for child in tree:
        if isinstance(child, list) and len(child) >= 2 and child[0] == 'attr':
            return child[1]
    return None


def parse_kicad_mod(filepath: str | Path) -> FootprintInfo:
    """Parse a ``.kicad_mod`` file into a :class:`FootprintInfo`.

    Raises :class:`ValueError` on parse errors.
    """
    filepath = Path(filepath)
    text = filepath.read_text(encoding='utf-8')
    tree = parse_sexpr(text)

    # tree: ['footprint', name, ...]
    name = tree[1] if len(tree) >= 2 else ""
    layers = _collect_layers(tree)
    properties = extract_properties(tree)
    pad_numbers, pad_types = _collect_pads(tree)
    attribute = _extract_attribute(tree)

    return FootprintInfo(
        name=name,
        layers=layers,
        properties=properties,
        pad_numbers=pad_numbers,
        pad_types=pad_types,
        attribute=attribute,
    )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_footprint_layers(
    filepath: str | Path,
    rules: LibraryRules,
    *,
    info: Optional[FootprintInfo] = None,
) -> CheckResult:
    """Check that a footprint uses all required layers.

    Uses attribute-aware ``footprint_layer_rules`` when available,
    falling back to the flat ``footprint_required_layers`` list.
    """
    filepath = Path(filepath)
    errors: List[str] = []

    if info is None:
        try:
            info = parse_kicad_mod(filepath)
        except Exception as exc:
            return CheckResult(errors=[f"Failed to parse footprint: {exc}"])

    if rules.footprint_layer_rules is not None:
        # Attribute-aware checking
        required: List[str] = list(rules.footprint_layer_rules.common)
        if info.attribute == 'smd':
            required.extend(rules.footprint_layer_rules.smd)
        elif info.attribute == 'through_hole':
            required.extend(rules.footprint_layer_rules.through_hole)
        for layer in required:
            if layer not in info.layers:
                errors.append(
                    f"Footprint '{info.name}': missing required layer '{layer}'"
                )
    else:
        # Fallback to flat list
        for required_layer in rules.footprint_required_layers:
            if required_layer not in info.layers:
                errors.append(
                    f"Footprint '{info.name}': missing required layer '{required_layer}'"
                )

    return CheckResult(errors=errors)


def check_footprint_pads(
    filepath: str | Path,
    *,
    info: Optional[FootprintInfo] = None,
) -> CheckResult:
    """Check that a footprint has at least one pad."""
    filepath = Path(filepath)
    errors: List[str] = []

    if info is None:
        try:
            info = parse_kicad_mod(filepath)
        except Exception as exc:
            return CheckResult(errors=[f"Failed to parse footprint: {exc}"])

    if info.pad_count == 0:
        errors.append(
            f"Footprint '{info.name}': has no pads"
        )

    return CheckResult(errors=errors)


def check_duplicate_pad_numbers(
    filepath: str | Path,
    *,
    info: Optional[FootprintInfo] = None,
    rules: Optional[LibraryRules] = None,
) -> CheckResult:
    """Check that no two pads share the same pad number (excluding empty strings).

    If *rules* is provided, footprints inside directories listed in
    ``rules.allow_duplicate_pads`` are skipped (e.g. connector libraries
    where multiple shield/ground pads legitimately share a number).
    """
    filepath = Path(filepath)
    errors: List[str] = []

    # Skip check for footprint directories that allow duplicate pads
    if rules and rules.allow_duplicate_pads:
        parent_stem = filepath.parent.stem  # e.g. "AharoniLab_Connector"
        if parent_stem in rules.allow_duplicate_pads:
            return CheckResult()

    if info is None:
        try:
            info = parse_kicad_mod(filepath)
        except Exception as exc:
            return CheckResult(errors=[f"Failed to parse footprint: {exc}"])

    seen: Dict[str, int] = {}
    for num in info.pad_numbers:
        if num == "":
            continue  # skip unnamed pads (e.g. mounting holes)
        seen[num] = seen.get(num, 0) + 1

    for num, count in seen.items():
        if count > 1:
            errors.append(
                f"Footprint '{info.name}': pad number '{num}' is used {count} times"
            )

    return CheckResult(errors=errors)


def check_footprint_properties(
    filepath: str | Path,
    rules: LibraryRules,
    *,
    info: Optional[FootprintInfo] = None,
) -> CheckResult:
    """Validate footprint properties against rules from ``library_rules.yaml``."""
    filepath = Path(filepath)
    errors: List[str] = []

    if info is None:
        try:
            info = parse_kicad_mod(filepath)
        except Exception as exc:
            return CheckResult(errors=[f"Failed to parse footprint: {exc}"])

    for prop_name, rule in rules.global_footprint_properties.items():
        value = info.properties.get(prop_name)

        if rule.required:
            if value is None or value.strip() == '' or value.strip() == '~':
                errors.append(
                    f"Footprint '{info.name}': {prop_name} property is missing or empty"
                )
                continue

        if rule.compiled_pattern is not None and value and value.strip() not in ('', '~'):
            if not rule.compiled_pattern.match(value):
                errors.append(
                    f"Footprint '{info.name}': {prop_name} property must match "
                    f"'{rule.pattern}' (got '{value}')"
                )

    return CheckResult(errors=errors)


def _get_electrical_pad_count(info: FootprintInfo) -> int:
    """Count electrical pads (excluding np_thru_hole)."""
    return sum(1 for t in info.pad_types if t != 'np_thru_hole')
