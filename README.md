# Aharoni Lab KiCad Library

[![Library Validation](https://github.com/Aharoni-Lab/kicad-lab-library/actions/workflows/validate.yml/badge.svg)](https://github.com/Aharoni-Lab/kicad-lab-library/actions/workflows/validate.yml)

Shared KiCad component library for the [Aharoni Lab](https://aharoni-lab.github.io/) at UCLA. Requires **KiCad 10** -- the library files are saved in the KiCad 10 format and will not load in KiCad 9. Every component is validated by CI on every pull request.

## Quick Install

```bash
git clone https://github.com/Aharoni-Lab/kicad-lab-library.git ~/kicad-libraries/kicad-lab-library
cd ~/kicad-libraries/kicad-lab-library
python scripts/install.py
```

This automatically configures KiCad 10 to find the library. See [docs/INSTALL.md](docs/INSTALL.md) for details.

## What's in the Library

The library is ready for components. Libraries are created on demand as components are added. See [docs/CONVENTIONS.md](docs/CONVENTIONS.md) for naming and grouping rules.

**Defined categories** (in `library_rules.yaml`):

| Category | Contents | Reference |
|---|---|---|
| `AharoniLab_Passive` | Resistors, capacitors, inductors, diodes | R, C, L, D |
| `AharoniLab_Connector` | Connectors and headers | J |
| `AharoniLab_MCU` | Microcontrollers | U |
| `AharoniLab_Power` | Power management ICs | U |
| `AharoniLab_Sensor` | Sensors and transducers | U |
| `AharoniLab_Interface` | Interface ICs (SERDES, level shifters) | U |
| `AharoniLab_OpAmp` | Operational amplifiers and comparators | U |
| `AharoniLab_Logic` | Logic ICs (gates, buffers, flip-flops) | U |
| `AharoniLab_Memory` | Memory ICs (EEPROM, Flash, SRAM) | U |
| `AharoniLab_Transistor` | Discrete transistors and MOSFETs | Q |
| `AharoniLab_Oscillator` | Oscillators and clock generators | U |
| `AharoniLab_Misc` | Miscellaneous ICs (digital potentiometers, etc.) | U |

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for how to add components. Every PR is automatically validated for:

- **KLC compliance** -- official KiCad Library Convention checks
- **Lab-specific checks** -- Datasheet URL required, `Validated` field required
- **Library table consistency** -- every file has a table entry, all paths use the environment variable
- **Structural checks** -- correct prefixes, flat layout, no backup files
- **Visual renderings** -- symbol and footprint previews posted as PR comments

## Documentation

- [Installation Guide](docs/INSTALL.md)
- [Contributing Guide](docs/CONTRIBUTING.md)
- [Conventions](docs/CONVENTIONS.md)

## License

[CC-BY-SA 4.0](LICENSE) with a design exception -- using library components in your projects requires no license obligations. Redistributing the library files themselves requires the same license. See [LICENSE](LICENSE) for details.
