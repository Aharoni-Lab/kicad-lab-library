"""Aharoni Lab KiCad library validator package.

Public API re-exports for convenient importing.
"""
from validator.checks import (
    ENV_VAR_PLACEHOLDER,
    CheckResult,
    LibTableEntry,
    SymbolInfo,
    check_duplicate_symbols,
    check_footprint_references,
    check_library_tables,
    check_pin_counts,
    check_reference_prefix,
    check_symbol_properties,
    parse_kicad_sym,
    parse_lib_table,
    resolve_table_uri,
)
from validator.config import (
    Category,
    LibraryRules,
    NamingRules,
    PinRange,
    PropertyRule,
    Subcategory,
    load_rules,
)
from validator.report import generate_report
from validator.sexpr import parse_sexpr

__all__ = [
    "ENV_VAR_PLACEHOLDER",
    "Category",
    "CheckResult",
    "LibTableEntry",
    "LibraryRules",
    "NamingRules",
    "PinRange",
    "PropertyRule",
    "Subcategory",
    "SymbolInfo",
    "check_duplicate_symbols",
    "check_footprint_references",
    "check_library_tables",
    "check_pin_counts",
    "check_reference_prefix",
    "check_symbol_properties",
    "generate_report",
    "load_rules",
    "parse_kicad_sym",
    "parse_lib_table",
    "parse_sexpr",
    "resolve_table_uri",
]
