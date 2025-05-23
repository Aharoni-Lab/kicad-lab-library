# KiCad Lab Library Environment Setup

This guide helps you configure your KiCad environment to use our shared lab library and contribute new components.

## Prerequisites
- KiCad 8.0 or later (**9.0 recommended**)
- Git
- Python 3.6 or later

## Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/<org>/kicad-lab-library.git
   cd kicad-lab-library
   ```

2. **Set Environment Variable**
   Add the following environment variable to your system. Use the actual path where you cloned the repository, replacing 'path\to\kicad-lab-library':

   Windows (PowerShell):
   ```powershell
   [System.Environment]::SetEnvironmentVariable('KICAD_LAB_LIBS', 'C:\path\to\kicad-lab-library', 'User')
   ```
   Linux/macOS:
   ```bash
   echo 'export KICAD_LAB_LIBS=/path/to/kicad-lab-library' >> ~/.bashrc
   ```

3. **Find Your KiCad Version**
   - In KiCad: Go to `Help` > `About KiCad` and note the version (e.g., `9.0`).
   - On disk: Check the versioned folders in your KiCad config directory (see below).

4. **Configure KiCad Libraries**
   Run the setup script with your KiCad version as an argument:
   Windows (PowerShell):
   ```powershell
   python scripts/setup_libraries.py 9.0
   ```
   Linux/macOS:
   ```bash
   python3 scripts/setup_libraries.py 9.0
   ```
   Replace `9.0` with your actual KiCad version (e.g., `8.0`, `9.0`).

   This script will:
   - Create backups of your existing library configuration files
   - Add our lab libraries to your existing configuration
   - Not overwrite any of your existing libraries
   - Support KiCad 8.0 and later

5. **Verify Setup**
   - Open KiCad
   - Create a new project
   - Open the schematic editor and try placing components from Lab libraries
   - Open the PCB editor and try placing footprints from Lab libraries

## Troubleshooting

If components or footprints aren't showing up:
1. Verify the `KICAD_LAB_LIBS` environment variable is set correctly
2. Check that the library configuration files were updated correctly
3. Ensure you have the latest version of the library pulled from git
4. Verify that the library files exist in the correct subdirectories
5. Try restarting KiCad after making these changes
6. Check the console output of `setup_libraries.py` for any warnings or errors
7. **If validation fails:**
   - Run `python scripts/validate_libraries.py` and review the grouped output for each symbol/footprint. All checks must pass (✓) for your changes to be accepted.
   - See the [Contributing Guide](../docs/CONTRIBUTING.md) for full validation and PR requirements.

## Contributing

When adding new components:
1. Follow the KLC guidelines in `docs/KLC_GUIDELINES.md`
2. Place components in the appropriate category and subcategory directories
3. Follow the naming conventions defined in `config/library_structure.yml`
4. **Run the validation script locally before committing:**
   ```bash
   python scripts/validate_libraries.py
   ```
   - Review the grouped validation output. All items must pass (✓) for your PR to be accepted.
5. **All contributions must be submitted via a pull request (PR) and pass all automated validation and CI checks.**
6. See the [Contributing Guide](../docs/CONTRIBUTING.md) for full details.

## Library Structure

The library is organized into categories and subcategories:

### Passive Components
- `passive/resistors/` - Resistors (prefix: `R_`)
- `passive/capacitors/` - Capacitors (prefix: `C_`)
- `passive/inductors/` - Inductors (prefix: `L_`)

### Active Components
- `active/sensors/`
  - `cmos_image/` - CMOS image sensors (prefix: `U_CMOS_`)
  - `environmental/` - Environmental sensors (prefix: `U_ENV_`)
- `active/ics/`
  - `microcontrollers/` - MCUs (prefix: `U_MCU_`)
  - `memory/` - Memory ICs (prefix: `U_MEM_`)
  - `interface/` - Interface ICs (prefix: `U_IF_`)
- `active/discrete/`
  - `transistors/` - Transistors (prefix: `Q_`)
  - `diodes/` - Diodes (prefix: `D_`)

### Connectors
- `connectors/board/` - Board connectors (prefix: `J_BOARD_`)
- `connectors/wire/` - Wire connectors (prefix: `J_WIRE_`)
- `connectors/rf/` - RF connectors (prefix: `J_RF_`)

### Mechanical
- `mechanical/mounting/` - Mounting hardware (prefixes: `H_`, `M_`)
- `mechanical/enclosure/` - Enclosure parts (prefix: `E_`)

### Power
- `power/regulators/` - Voltage regulators (prefix: `U_REG_`)
- `power/converters/` - DC-DC converters (prefix: `U_CONV_`)
- `power/protection/` - Protection circuits (prefix: `U_PROT_`)

### Miscellaneous
- `misc/misc/` - Other components (no prefix)

Each subcategory has its own:
- Symbol library (`.kicad_sym`)
- Footprint library (`.pretty` directory)
- 3D models directory
- Datasheets directory 