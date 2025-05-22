# kicad-lab-library

## Overview
This repository contains the **shared global KiCad 9 library** for our lab:
- **Symbols** (`symbols/lab_symbols.kicad_sym`)
- **Footprints** (`footprints/lab_footprints.pretty`)
- **3D Models** (`3dmodels/`)

It adheres to the KiCad Library Convention (KLC) and includes CI to validate new components.

## Directory Structure
Refer to the project root for the full tree. Key folders:
- `symbols/`: KiCad symbol library files
- `footprints/`: KiCad footprint collections
- `3dmodels/`: STEP/WRL files used by footprints
- `docs/`: KLC guidelines and internal extensions
- `env/`: Environment variable instructions
- `scripts/`: Validation and utility scripts
- `.github/workflows/`: CI definitions

## Getting Started
1. **Clone** the repo:
   ```bash
   git clone https://github.com/Aharoni-Lab/kicad-lab-library.git
