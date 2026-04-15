# Contributing Guide

## Workflow

1. Fork the repository (or create a branch if you have write access)
2. Create a feature branch: `git checkout -b add-<component-name>`
3. Add your component(s)
4. Run tests: `pip install pytest pyyaml && pytest tests/ -v`
5. Commit and push
6. Open a pull request -- CI will validate automatically

## Which Library File?

Categories with validation rules in `library_rules.yaml`:

| Component Type | Symbol Library | Reference | Footprint Library |
|---|---|---|---|
| Resistors, capacitors, inductors, diodes | `AharoniLab_Passive` | R, C, L, D | `AharoniLab_Resistor_SMD`, `AharoniLab_Capacitor_SMD`, etc. |
| Connectors (headers, JST, USB, FPC) | `AharoniLab_Connector` | J | `AharoniLab_Connector` |
| Microcontrollers (ESP32, STM32, etc.) | `AharoniLab_MCU` | U | Package-appropriate library |
| Regulators, power monitors | `AharoniLab_Power` | U | Package-appropriate library |
| Temperature, pressure, IMU | `AharoniLab_Sensor` | U | Package-appropriate library |

Need a category not listed above (op-amps, transistors, logic, memory, etc.)? Add the rules to `library_rules.yaml` first, then create the library file. See existing categories for the format.

If the library file doesn't exist yet, create it and add an entry to `sym-lib-table` or `fp-lib-table`. You can also run `python -m validator --generate-tables` to auto-generate the table entries.

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
pip install pytest pyyaml
pytest tests/ -v
```

You can also run the validator directly:

```bash
python -m validator --all --check-tables --check-footprints --report
```

Tests check:
- Directory structure (flat layout, correct prefixes)
- Symbol properties (Datasheet URL, Validated field, and all rules from `library_rules.yaml`)
- Reference prefix and pin count validation (per-category rules)
- Footprint layer and pad validation
- Library table consistency (every file has an entry, all URIs use the env variable)
- Library table generation (tables match what's on disk)

## What CI Checks

When you open a PR, three CI jobs run:

1. **Tests** -- `pytest tests/ -v`
2. **KLC Validation** -- official KLC checks on changed symbols and footprints, plus lab-specific validation via `python -m validator`
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
