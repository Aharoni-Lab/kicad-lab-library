# KiCad Lab Library Environment Setup

This guide helps you configure your KiCad environment to use our shared lab library.

## Prerequisites
- KiCad 9.0 or later
- Git

## Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/<org>/kicad-lab-library.git
   cd kicad-lab-library
   ```

2. **Set Environment Variable**
   
   Add this to your system environment variables or shell profile:
   
   Windows (PowerShell):
   ```powershell
   [System.Environment]::SetEnvironmentVariable('KICAD_LAB_LIBS', 'C:\path\to\kicad-lab-library', 'User')
   ```
   
   Linux/macOS:
   ```bash
   echo 'export KICAD_LAB_LIBS=/path/to/kicad-lab-library' >> ~/.bashrc
   ```

3. **Configure KiCad Global Libraries**

   Open KiCad and go to Preferences → Manage Symbol Libraries:
   
   Add a new library:
   - Name: `Lab_Symbols`
   - Path: `${KICAD_LAB_LIBS}/symbols/lab_symbols.kicad_sym`
   - Type: `KiCad`
   
   Then go to Preferences → Manage Footprint Libraries:
   
   Add a new library:
   - Name: `Lab_Footprints`
   - Path: `${KICAD_LAB_LIBS}/footprints/lab_footprints.pretty`
   - Type: `KiCad`

4. **Verify Setup**
   - Open KiCad
   - Create a new project
   - Open the schematic editor
   - Try placing a component from the Lab_Symbols library
   - Open the PCB editor
   - Try placing a footprint from the Lab_Footprints library

## Troubleshooting

If components or footprints aren't showing up:
1. Verify the `KICAD_LAB_LIBS` environment variable is set correctly
2. Check that the paths in KiCad's library tables use `${KICAD_LAB_LIBS}` syntax
3. Ensure you have the latest version of the library pulled from git

## Contributing

When adding new components:
1. Follow the KLC guidelines in `docs/KLC_GUIDELINES.md`
2. Run the validation script locally before committing:
   ```bash
   python scripts/validate_libraries.py
   ```
3. Create a pull request for review 