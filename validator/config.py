"""YAML configuration loader for library validation rules.

Loads ``library_rules.yaml`` into stdlib dataclasses. PyYAML is the only
external dependency.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PropertyRule:
    """Validation rule for a single symbol property."""
    required: bool = True
    pattern: Optional[str] = None
    _compiled: Optional[re.Pattern] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.pattern is not None:
            try:
                self._compiled = re.compile(self.pattern)
            except re.error as exc:
                raise ValueError(
                    f"Invalid regex pattern {self.pattern!r}: {exc}"
                ) from exc

    @property
    def compiled_pattern(self) -> Optional[re.Pattern]:
        return self._compiled


@dataclass
class PinRange:
    """Allowed pin count range."""
    min: Optional[int] = None
    max: Optional[int] = None


@dataclass
class Subcategory:
    """Rules for a subcategory within a library file (e.g. resistor in Passive)."""
    reference_prefix: Optional[str] = None
    pins: Optional[PinRange] = None


@dataclass
class SymbolFlagRules:
    """Expected in_bom / on_board flag values."""
    in_bom: Optional[bool] = None
    on_board: Optional[bool] = None


@dataclass
class Category:
    """Rules for a single library file (keyed by filename stem)."""
    reference_prefix: Optional[str] = None
    pins: Optional[PinRange] = None
    subcategories: Optional[Dict[str, Subcategory]] = None
    flags: Optional[SymbolFlagRules] = None
    description: Optional[str] = None


@dataclass
class NamingRules:
    """Naming convention patterns."""
    symbol_file_pattern: Optional[str] = None
    footprint_dir_pattern: Optional[str] = None


@dataclass
class FootprintLayerRules:
    """Attribute-aware layer requirements for footprints."""
    common: List[str] = field(default_factory=list)
    smd: List[str] = field(default_factory=list)
    through_hole: List[str] = field(default_factory=list)


@dataclass
class LibraryRules:
    """Top-level configuration loaded from library_rules.yaml."""
    prefix: str = "AharoniLab_"
    env_var: str = "AHARONI_LAB_KICAD_LIB"
    global_symbol_properties: Dict[str, PropertyRule] = field(default_factory=dict)
    categories: Dict[str, Category] = field(default_factory=dict)
    footprint_required_layers: List[str] = field(default_factory=list)
    naming: Optional[NamingRules] = None
    symbol_flags: Optional[SymbolFlagRules] = None
    global_footprint_properties: Dict[str, PropertyRule] = field(default_factory=dict)
    footprint_layer_rules: Optional[FootprintLayerRules] = None
    allow_duplicate_pads: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _parse_pin_range(data: dict) -> PinRange:
    """Parse a pin range dict like ``{min: 2, max: 2}``."""
    return PinRange(
        min=data.get("min"),
        max=data.get("max"),
    )


def _parse_subcategory(data: dict) -> Subcategory:
    """Parse a subcategory dict."""
    pins = None
    if "pins" in data:
        pins = _parse_pin_range(data["pins"])
    return Subcategory(
        reference_prefix=data.get("reference_prefix"),
        pins=pins,
    )


def _parse_category(data: dict) -> Category:
    """Parse a category dict."""
    pins = None
    if "pins" in data:
        pins = _parse_pin_range(data["pins"])

    subcategories = None
    if "subcategories" in data:
        subcategories = {
            name: _parse_subcategory(sub)
            for name, sub in data["subcategories"].items()
        }

    flags = None
    if "flags" in data:
        fd = data["flags"]
        flags = SymbolFlagRules(
            in_bom=fd.get("in_bom"),
            on_board=fd.get("on_board"),
        )

    return Category(
        reference_prefix=data.get("reference_prefix"),
        pins=pins,
        subcategories=subcategories,
        flags=flags,
        description=data.get("description"),
    )


def load_rules(path: str | Path) -> LibraryRules:
    """Load and validate a ``library_rules.yaml`` file.

    Raises ``ValueError`` on missing required sections or invalid data.
    """
    path = Path(path)
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError(f"Expected a YAML mapping at top level, got {type(raw).__name__}")

    # --- library section ---
    lib_section = raw.get("library", {})
    prefix = lib_section.get("prefix", "AharoniLab_")
    env_var = lib_section.get("env_var", "AHARONI_LAB_KICAD_LIB")

    # --- global_symbol_properties (required) ---
    gsp_raw = raw.get("global_symbol_properties")
    if gsp_raw is None:
        raise ValueError("Missing required section: global_symbol_properties")

    global_props: Dict[str, PropertyRule] = {}
    for prop_name, prop_data in gsp_raw.items():
        if prop_data is None:
            prop_data = {}
        global_props[prop_name] = PropertyRule(
            required=prop_data.get("required", True),
            pattern=prop_data.get("pattern"),
        )

    # --- categories ---
    categories: Dict[str, Category] = {}
    for cat_name, cat_data in raw.get("categories", {}).items():
        if cat_data is None:
            cat_data = {}
        categories[cat_name] = _parse_category(cat_data)

    # --- footprint_required_layers ---
    fp_layers: List[str] = raw.get("footprint_required_layers", [])

    # --- naming ---
    naming = None
    naming_raw = raw.get("naming")
    if naming_raw:
        naming = NamingRules(
            symbol_file_pattern=naming_raw.get("symbol_file_pattern"),
            footprint_dir_pattern=naming_raw.get("footprint_dir_pattern"),
        )

    # --- symbol_flags ---
    symbol_flags = None
    sf_raw = raw.get("symbol_flags")
    if sf_raw:
        symbol_flags = SymbolFlagRules(
            in_bom=sf_raw.get("in_bom"),
            on_board=sf_raw.get("on_board"),
        )

    # --- global_footprint_properties ---
    gfp_raw = raw.get("global_footprint_properties", {})
    global_fp_props: Dict[str, PropertyRule] = {}
    if gfp_raw:
        for prop_name, prop_data in gfp_raw.items():
            if prop_data is None:
                prop_data = {}
            global_fp_props[prop_name] = PropertyRule(
                required=prop_data.get("required", True),
                pattern=prop_data.get("pattern"),
            )

    # --- footprint_layer_rules ---
    footprint_layer_rules = None
    flr_raw = raw.get("footprint_layer_rules")
    if flr_raw:
        footprint_layer_rules = FootprintLayerRules(
            common=flr_raw.get("common", []),
            smd=flr_raw.get("smd", []),
            through_hole=flr_raw.get("through_hole", []),
        )

    # --- allow_duplicate_pads ---
    allow_duplicate_pads: List[str] = raw.get("allow_duplicate_pads", [])

    return LibraryRules(
        prefix=prefix,
        env_var=env_var,
        global_symbol_properties=global_props,
        categories=categories,
        footprint_required_layers=fp_layers,
        naming=naming,
        symbol_flags=symbol_flags,
        global_footprint_properties=global_fp_props,
        footprint_layer_rules=footprint_layer_rules,
        allow_duplicate_pads=allow_duplicate_pads,
    )
