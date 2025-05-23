# kicad-lab-library

## Overview
This repository contains the **shared global KiCad library** for our lab, supporting KiCad 8.0 and 9.0 (**9.0 recommended**):
- **Symbols** (`symbols/`)
- **Footprints** (`footprints/`)
- **3D Models** (`3dmodels/`)

The library adheres to the KiCad Library Convention (KLC) and includes continuous integration (CI) to validate all new components and changes.

**All contributions must be submitted via a pull request (PR) and pass all automated validation and CI checks before being merged.**

## Directory Structure
Key folders:
- `symbols/`: KiCad symbol library files (organized by category/subcategory)
- `footprints/`: KiCad footprint collections (organized by category/subcategory)
- `3dmodels/`: STEP/WRL files used by footprints
- `docs/`: Setup guide, contributing guide, KLC guidelines, and documentation
- `scripts/`: Validation and utility scripts
- `.github/`: PR templates and CI definitions

## Getting Started
1. **Clone** the repo:
   ```bash
   git clone https://github.com/Aharoni-Lab/kicad-lab-library.git
   cd kicad-lab-library
   ```
2. **Set up your environment and KiCad libraries:**
   - Follow the instructions in [`docs/setup.md`](docs/setup.md)

3. **Contributing:**
   - See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for detailed contribution, validation, and PR requirements.

## Validation & CI
- All changes are validated automatically via CI on every PR.
- Run `python scripts/validate_libraries.py` locally before submitting a PR to ensure all checks pass.
- The validation script prints a grouped summary for each symbol and footprint, showing all passing (✓) and failing (❌) checks under each item.

## Resources
- [Setup Guide](docs/setup.md)
- [Contributing Guide](docs/CONTRIBUTING.md)
- [KLC Guidelines](docs/KLC_GUIDELINES.md)
