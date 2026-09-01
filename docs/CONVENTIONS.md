# Library Conventions

## AharoniLab_ Prefix

All library files and directories use the `AharoniLab_` prefix to avoid name collisions with official KiCad libraries and other third-party libraries. This makes it instantly clear which components come from the lab's library.

## Symbol Grouping

Symbols are grouped by **function** into `.kicad_sym` files. Categories with validation rules in `library_rules.yaml`:

- `AharoniLab_Passive` -- resistors, capacitors, inductors, diodes
- `AharoniLab_Connector` -- headers, JST, Molex, USB, FPC
- `AharoniLab_MCU` -- ESP32, STM32, PIC/AVR
- `AharoniLab_Power` -- regulators, supervisors, power monitors
- `AharoniLab_Sensor` -- temperature, pressure, IMU

Additional categories can be added as needed (e.g., `AharoniLab_OpAmp`, `AharoniLab_Transistor`, `AharoniLab_Logic`, `AharoniLab_Memory`). Add the rules to `library_rules.yaml` before creating the library file.

## Footprint Grouping

Footprints are grouped by **package type** into `.pretty` directories:

- `AharoniLab_Capacitor_SMD.pretty` -- SMD capacitor packages
- `AharoniLab_Resistor_SMD.pretty` -- SMD resistor packages
- `AharoniLab_Package_SO.pretty` -- SOIC, SSOP, TSSOP
- `AharoniLab_Package_QFP.pretty` -- QFP, LQFP, TQFP
- `AharoniLab_Package_DFN_QFN.pretty` -- DFN, QFN
- `AharoniLab_Connector.pretty` -- connector footprints

## 3D Models

3D model directories mirror footprint directories:
- `AharoniLab_Capacitor_SMD.3dshapes/` matches `AharoniLab_Capacitor_SMD.pretty/`
- Models use STEP format (`.step` or `.stp` extension)
- Name the model after its footprint where practical; vendor-supplied models may keep their manufacturer part number
- Every `(model ...)` path in a footprint must use `${AHARONI_LAB_KICAD_LIB}` and point at a file that exists in this repo (CI enforces this); a footprint without a model is allowed

## Library Files and Categories

The repo pre-creates library files/dirs for the categories defined in `library_rules.yaml`, so some are still empty — that's expected. To add a brand-new category: add its rules to `library_rules.yaml` first, then create the library file/dir and regenerate the tables (`python -m validator --generate-tables`).

## The Validated Field

Every symbol carries a `Validated` property:

```
(property "Validated" "No" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
```

### Purpose

Tracks whether a component has been proven in a real, fabricated project. This gives the team confidence in component quality:
- `"No"` -- added to the library but not yet used in a manufactured board
- `"Yes"` -- used in a real project, confirmed working

### Lifecycle

1. New component added -> `Validated: "No"`
2. Component used in a real project, board fabricated and tested -> PR to change to `"Yes"` with project reference in PR description
3. Only the person who verified the component in a real project should mark it as `"Yes"`

### CI Enforcement

CI checks that every symbol has a `Validated` property set to exactly `"Yes"` or `"No"`. Any other value (or a missing field) fails validation. All validation rules (required properties, regex patterns, reference prefixes, pin counts) are defined in `library_rules.yaml` at the repo root.

## Environment Variable

The `AHARONI_LAB_KICAD_LIB` environment variable is set in KiCad's configuration and points to the repository root. All library table URIs use `${AHARONI_LAB_KICAD_LIB}` instead of absolute paths, making the library portable across machines.

## KiCad Embedded Files

When sharing KiCad projects that use lab library components, use KiCad's embedded files feature. This embeds the component data directly in the project file, so recipients don't need the library installed to open and edit the project.
