# Aharoni Lab KiCad Library

[![Library Validation](https://github.com/Aharoni-Lab/kicad-lab-library/actions/workflows/validate.yml/badge.svg)](https://github.com/Aharoni-Lab/kicad-lab-library/actions/workflows/validate.yml)

Shared KiCad 9 component library for the [Aharoni Lab](https://aharoni-lab.github.io/) at UCLA. Every component is validated by CI on every pull request.

## Quick Install

```bash
git clone https://github.com/Aharoni-Lab/kicad-lab-library.git ~/kicad-libraries/kicad-lab-library
cd ~/kicad-libraries/kicad-lab-library
python scripts/install.py
```

This automatically configures KiCad 9 to find the library. See [docs/INSTALL.md](docs/INSTALL.md) for details.

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

MIT
