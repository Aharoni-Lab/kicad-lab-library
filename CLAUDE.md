# CLAUDE.md - Project Guide for Claude Code

## Repository Purpose

Shared KiCad 9 component library for the Aharoni Lab (UCLA). Contains symbols, footprints, and 3D models with CI validation on every PR.

## Structure

```
symbols/                  # Flat directory of .kicad_sym files
footprints/               # .pretty directories (one per package family)
3dmodels/                 # .3dshapes directories (mirror footprint dirs)
validator/                # Python package: validation engine
  __init__.py             # Re-exports public API
  __main__.py             # CLI entry point (python -m validator)
  sexpr.py                # S-expression parser for KiCad files
  config.py               # YAML config loader + dataclasses
  checks.py               # Symbol validation checks
  footprint_checks.py     # Footprint-specific checks (layers, pads)
  report.py               # Markdown report generation
  table_gen.py            # Library table auto-generation
scripts/install.py        # One-command install for lab members
library_rules.yaml        # YAML-driven validation rules
tests/                    # pytest test suite
sym-lib-table             # KiCad symbol library table
fp-lib-table              # KiCad footprint library table
```

## Key Concepts

- **Prefix**: All library files/dirs use `AharoniLab_` prefix
- **Environment variable**: `${AHARONI_LAB_KICAD_LIB}` points to repo root in all library table URIs
- **Validated property**: Every symbol has `Validated` set to `"Yes"` or `"No"` — tracks whether a component has been proven in a real project
- **Flat structure**: `symbols/` contains only `.kicad_sym` files (no subdirectories). Footprints are grouped by package type in `.pretty` dirs
- **CI is the core**: Tests encode intentions. Write tests first, then implementation
- **YAML-driven validation**: All property requirements, patterns, pin counts, and reference prefixes are defined in `library_rules.yaml` — no hardcoded rules

## Running Tests

```bash
pip install pytest pyyaml
pytest tests/ -v
```

## Running Validation

```bash
python -m validator --all --check-tables --check-footprints   # Check everything
python -m validator --report                                   # Markdown report
python -m validator symbols/AharoniLab_Passive.kicad_sym       # Single file
python -m validator --generate-tables                          # Verify tables match disk
```

## Adding Components

1. Add symbol to appropriate `symbols/AharoniLab_*.kicad_sym` file
2. Required properties: Reference, Value, Footprint, Datasheet (URL), Description, ki_keywords, Validated ("No" for new)
3. Add footprint to `footprints/AharoniLab_*.pretty/`
4. Add 3D model to `3dmodels/AharoniLab_*.3dshapes/` (STEP format)
5. Update `sym-lib-table`/`fp-lib-table` only if creating a new library file/dir
6. Run `pytest tests/ -v` before committing

## Library Table Format

```
(sym_lib_table
  (version 7)
  (lib (name "AharoniLab_Passive")(type "KiCad")(uri "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Passive.kicad_sym")(options "")(descr "..."))
)
```

## File Grouping

- **Symbols**: By function — `AharoniLab_Passive`, `AharoniLab_Connector`, `AharoniLab_MCU`, etc.
- **Footprints**: By package type — `AharoniLab_Capacitor_SMD.pretty`, `AharoniLab_Package_QFP.pretty`, etc.
- **3D models**: Mirror footprint dirs — `AharoniLab_Capacitor_SMD.3dshapes`

## CI Pipeline

Three jobs on PR:
1. `test` — runs pytest
2. `klc-check` — runs official KiCad Library Convention checks + lab-specific validation
3. `render-and-report` — renders SVGs with kicad-cli, posts validation report as PR comment
