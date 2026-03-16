# Contributing Guide

## Workflow

1. Fork the repository (or create a branch if you have write access)
2. Create a feature branch: `git checkout -b add-<component-name>`
3. Add your component(s)
4. Run tests: `pip install pytest && pytest tests/ -v`
5. Commit and push
6. Open a pull request -- CI will validate automatically

## Which Library File?

| Component Type | Symbol Library | Footprint Library |
|---|---|---|
| Resistors, capacitors, inductors, diodes | `AharoniLab_Passive` | `AharoniLab_Resistor_SMD`, `AharoniLab_Capacitor_SMD`, etc. |
| Connectors (headers, JST, USB, FPC) | `AharoniLab_Connector` | `AharoniLab_Connector` |
| Op-amps, comparators | `AharoniLab_OpAmp` | `AharoniLab_Package_SO`, `AharoniLab_Package_QFP`, etc. |
| BJT, MOSFET | `AharoniLab_Transistor` | Package-appropriate library |
| Regulators, power monitors | `AharoniLab_Power` | Package-appropriate library |
| ESP32, STM32, PIC/AVR | `AharoniLab_MCU` | Package-appropriate library |
| Gates, muxes, level shifters | `AharoniLab_Logic` | Package-appropriate library |
| EEPROM, flash, RAM | `AharoniLab_Memory` | Package-appropriate library |
| Temperature, pressure, IMU | `AharoniLab_Sensor` | Package-appropriate library |

If the library file doesn't exist yet, create it and add an entry to `sym-lib-table` or `fp-lib-table`.

## Required Symbol Properties

Every symbol **must** have these properties:

| Property | Example | Notes |
|---|---|---|
| `Reference` | `R`, `C`, `U` | Standard reference designator |
| `Value` | `100nF`, `LM1117` | Component value or part number |
| `Footprint` | `""` | Can be empty (assigned per-use) |
| `Datasheet` | `https://www.ti.com/...` | **Must be a URL** (not empty, not `~`) |
| `Description` | `"100nF ceramic capacitor"` | Brief description |
| `ki_keywords` | `"capacitor cap ceramic"` | Search keywords |
| `Validated` | `"No"` | Set to `"No"` for new components |

### The Validated Field

```
(property "Validated" "No" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
```

- **New components**: Set to `"No"`
- **Proven in a real project**: Open a PR to change to `"Yes"` and mention the project in the PR description
- CI enforces that this field exists and is either `"Yes"` or `"No"`

## KLC Rules

All components must follow the [KiCad Library Conventions](https://klc.kicad.org/). Key rules:

- **Symbols**: Pin placement, property positions, graphical style
- **Footprints**: Pad sizes, courtyard clearance, silkscreen, fab layer
- **Naming**: Follow KLC naming patterns (e.g., `C_0201_0603Metric`)

CI runs the official KLC checker on every PR.

## Naming Conventions

- All library files use `AharoniLab_` prefix
- Symbols: follow KLC naming (e.g., `C`, `R`, `LM1117-3.3`)
- Footprints: follow KLC naming (e.g., `C_0201_0603Metric`, `R_0402_1005Metric`)
- 3D models: match footprint names with `.step` extension

## Running Tests Locally

```bash
pip install pytest
pytest tests/ -v
```

Tests check:
- Directory structure (flat layout, correct prefixes)
- Symbol properties (Datasheet URL, Validated field)
- Library table consistency (every file has an entry, all URIs use the env variable)

## What CI Checks

When you open a PR, three CI jobs run:

1. **Tests** -- `pytest tests/ -v`
2. **KLC Validation** -- official KLC checks on changed symbols and footprints
3. **Render & Report** -- renders symbol/footprint SVGs and posts a validation report as a PR comment

All three must pass to merge.

## Creating New Library Files

If you need a new library file (e.g., `AharoniLab_Sensor`):

1. Create the symbol file: `symbols/AharoniLab_Sensor.kicad_sym`
2. Add entry to `sym-lib-table`:
   ```
   (lib (name "AharoniLab_Sensor")(type "KiCad")(uri "${AHARONI_LAB_KICAD_LIB}/symbols/AharoniLab_Sensor.kicad_sym")(options "")(descr "Sensor ICs"))
   ```
3. For footprints, create the `.pretty` directory and add entry to `fp-lib-table`
4. For 3D models, create the matching `.3dshapes` directory
