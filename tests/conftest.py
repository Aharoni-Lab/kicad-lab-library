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
