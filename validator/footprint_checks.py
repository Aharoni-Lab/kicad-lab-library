"""Footprint-specific validation checks (layers, pads)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from validator.checks import CheckResult
from validator.config import LibraryRules
from validator.sexpr import parse_sexpr


# ---------------------------------------------------------------------------
# FootprintInfo
# ---------------------------------------------------------------------------

@dataclass
class FootprintInfo:
    """Parsed footprint metadata."""
    name: str
    layers: Set[str]
    pad_count: int
    properties: Dict[str, str]


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


def _count_pads(tree: list) -> int:
    """Count top-level pad nodes in a footprint tree."""
    count = 0
    for child in tree:
        if isinstance(child, list) and len(child) >= 1 and child[0] == 'pad':
            count += 1
    return count


def _extract_properties(tree: list) -> Dict[str, str]:
    """Extract property name->value from a footprint tree."""
    props: Dict[str, str] = {}
    for child in tree:
        if isinstance(child, list) and len(child) >= 3 and child[0] == 'property':
            props[child[1]] = child[2]
    return props


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
    pad_count = _count_pads(tree)
    properties = _extract_properties(tree)

    return FootprintInfo(
        name=name,
        layers=layers,
        pad_count=pad_count,
        properties=properties,
    )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_footprint_layers(
    filepath: str | Path,
    rules: LibraryRules,
) -> CheckResult:
    """Check that a footprint uses all required layers."""
    filepath = Path(filepath)
    errors: List[str] = []

    try:
        info = parse_kicad_mod(filepath)
    except Exception as exc:
        return CheckResult(errors=[f"Failed to parse footprint: {exc}"])

    for required_layer in rules.footprint_required_layers:
        if required_layer not in info.layers:
            errors.append(
                f"Footprint '{info.name}': missing required layer '{required_layer}'"
            )

    return CheckResult(errors=errors)


def check_footprint_pads(filepath: str | Path) -> CheckResult:
    """Check that a footprint has at least one pad."""
    filepath = Path(filepath)
    errors: List[str] = []

    try:
        info = parse_kicad_mod(filepath)
    except Exception as exc:
        return CheckResult(errors=[f"Failed to parse footprint: {exc}"])

    if info.pad_count == 0:
        errors.append(
            f"Footprint '{info.name}': has no pads"
        )

    return CheckResult(errors=errors)
