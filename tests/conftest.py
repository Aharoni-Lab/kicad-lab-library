"""Shared fixtures for kicad-lab-library tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from validator.config import load_rules

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root directory."""
    return REPO_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def rules(repo_root):
    """Load the real library_rules.yaml from repo root."""
    return load_rules(repo_root / "library_rules.yaml")


@pytest.fixture
def valid_symbol_path() -> Path:
    return FIXTURES_DIR / "valid_symbol.kicad_sym"


@pytest.fixture
def valid_symbol_unvalidated_path() -> Path:
    return FIXTURES_DIR / "valid_symbol_unvalidated.kicad_sym"


@pytest.fixture
def invalid_no_datasheet_path() -> Path:
    return FIXTURES_DIR / "invalid_no_datasheet.kicad_sym"


@pytest.fixture
def invalid_empty_datasheet_path() -> Path:
    return FIXTURES_DIR / "invalid_empty_datasheet.kicad_sym"


@pytest.fixture
def invalid_no_validated_path() -> Path:
    return FIXTURES_DIR / "invalid_no_validated.kicad_sym"


@pytest.fixture
def invalid_bad_validated_path() -> Path:
    return FIXTURES_DIR / "invalid_bad_validated.kicad_sym"


@pytest.fixture
def invalid_malformed_path() -> Path:
    return FIXTURES_DIR / "invalid_malformed.kicad_sym"


@pytest.fixture
def invalid_no_reference_path() -> Path:
    return FIXTURES_DIR / "invalid_no_reference.kicad_sym"


@pytest.fixture
def invalid_no_description_path() -> Path:
    return FIXTURES_DIR / "invalid_no_description.kicad_sym"


@pytest.fixture
def invalid_no_keywords_path() -> Path:
    return FIXTURES_DIR / "invalid_no_keywords.kicad_sym"


# ---------------------------------------------------------------------------
# Factories for building KiCad files and minimal repos in tests
# ---------------------------------------------------------------------------

def make_symbol(name: str, props: dict, pins: int = 0) -> str:
    """Return the text of one ``(symbol ...)`` node."""
    parts = [f'(symbol "{name}"']
    for key, value in props.items():
        parts.append(f'  (property "{key}" "{value}" (at 0 0 0))')
    if pins:
        pin_nodes = " ".join(
            f'(pin passive line (at 0 {i} 0) (length 2.54) '
            f'(name "~") (number "{i + 1}"))'
            for i in range(pins)
        )
        parts.append(f'  (symbol "{name}_1_1" {pin_nodes})')
    parts.append(')')
    return "\n".join(parts)


def make_symbol_lib(*symbols: str) -> str:
    """Wrap symbol nodes in a KiCad 10 symbol library skeleton."""
    body = "\n".join(symbols)
    return (
        '(kicad_symbol_lib\n'
        '  (version 20251024)\n'
        '  (generator "kicad_symbol_editor")\n'
        '  (generator_version "10.0")\n'
        f'{body}\n'
        ')\n'
    )


MINIMAL_RULES_YAML = """\
library:
  prefix: "AharoniLab_"
  env_var: "AHARONI_LAB_KICAD_LIB"

global_symbol_properties:
  Reference:
    required: true
  Validated:
    required: true
    pattern: "^(Yes|No)$"

categories:
  AharoniLab_Test:
    description: "Test components"
"""

GOOD_SYMBOL_PROPS = {
    "Reference": "U",
    "Value": "GoodPart",
    "Validated": "No",
}


@pytest.fixture
def tmp_repo(tmp_path):
    """A minimal self-consistent repo: one symbol library, rules, tables."""
    from validator.config import load_rules as _load_rules
    from validator.table_gen import write_generated_tables

    (tmp_path / "symbols").mkdir()
    (tmp_path / "footprints").mkdir()
    (tmp_path / "symbols" / "AharoniLab_Test.kicad_sym").write_text(
        make_symbol_lib(make_symbol("GoodPart", GOOD_SYMBOL_PROPS))
    )
    (tmp_path / "library_rules.yaml").write_text(MINIMAL_RULES_YAML)
    rules = _load_rules(tmp_path / "library_rules.yaml")
    write_generated_tables(tmp_path, rules=rules)
    return tmp_path
