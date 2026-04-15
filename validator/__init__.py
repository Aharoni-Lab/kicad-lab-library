"""Aharoni Lab KiCad library validator package.

Public API re-exports for convenient importing.
"""
from validator.checks import (
    ENV_VAR_PLACEHOLDER,
    CheckResult,
    SymbolInfo,
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
    resolve_table_uri,
)
from validator.config import (
    Category,
    FootprintLayerRules,
    LibraryRules,
    NamingRules,
    PinRange,
    PropertyRule,
    Subcategory,
    SymbolFlagRules,
    load_rules,
)
from validator.footprint_checks import (
    check_duplicate_pad_numbers,
    check_footprint_layers,
    check_footprint_pads,
    check_footprint_properties,
)
from validator.lib_table import LibTableEntry, parse_lib_table, serialize_lib_table
from validator.report import generate_report
from validator.sexpr import extract_properties, parse_sexpr
from validator.table_gen import write_generated_tables

__all__ = [
    "ENV_VAR_PLACEHOLDER",
    "Category",
    "CheckResult",
    "FootprintLayerRules",
    "LibTableEntry",
    "LibraryRules",
    "NamingRules",
    "PinRange",
    "PropertyRule",
    "Subcategory",
    "SymbolFlagRules",
    "SymbolInfo",
    "check_duplicate_pad_numbers",
    "check_duplicate_symbols",
    "check_footprint_layers",
    "check_footprint_pads",
    "check_footprint_properties",
    "check_footprint_references",
    "check_library_tables",
    "check_naming_conventions",
    "check_pin_counts",
    "check_pin_pad_cross_validation",
    "check_reference_prefix",
    "check_symbol_flags",
    "check_symbol_properties",
    "check_uncategorized_files",
    "extract_properties",
    "generate_report",
    "load_rules",
    "parse_kicad_sym",
    "parse_lib_table",
    "parse_sexpr",
    "resolve_table_uri",
    "serialize_lib_table",
    "write_generated_tables",
]
