# Contributing to the KiCad Lab Library

This guide explains how to contribute new components to our shared KiCad library. **All contributions must be submitted via a pull request (PR) and must pass all automated validation and tests before being merged.**

## Library Structure

Our library is organized into three main directories, each with subdirectories for different component types:

### Symbols (`symbols/`)
- `passive/`
  - `resistors/` - All resistor symbols
  - `capacitors/` - All capacitor symbols
  - `inductors/` - All inductor symbols
- `active/`
  - `sensors/` - Image sensors, environmental sensors, etc.
    - `cmos_image/` - CMOS image sensors
    - `environmental/` - Temperature, humidity, etc.
  - `ics/` - Integrated circuits
    - `microcontrollers/` - MCUs and processors
    - `memory/` - RAM, Flash, etc.
    - `interface/` - Communication ICs (I2C, SPI, etc.)
  - `discrete/` - Transistors, diodes, etc.
    - `transistors/` - BJT, MOSFET, etc.
    - `diodes/` - Regular, Schottky, etc.
- `connectors/`
  - `board/` - Board-to-board connectors
  - `wire/` - Wire-to-board connectors
  - `rf/` - RF connectors
- `mechanical/`
  - `mounting/` - Mounting holes, standoffs
  - `enclosure/` - Enclosure parts
- `power/`
  - `regulators/` - Voltage regulators
  - `converters/` - DC-DC converters
  - `protection/` - Protection circuits
- `misc/` - Other components

### Footprints (`footprints/`)
- `passive/`
  - `resistors/` - R_* footprints
  - `capacitors/` - C_* footprints
  - `inductors/` - L_* footprints
- `active/`
  - `sensors/` - Image sensor footprints
    - `cmos_image/` - CMOS image sensor packages
    - `environmental/` - Environmental sensor packages
  - `ics/` - IC footprints
    - `microcontrollers/` - MCU packages
    - `memory/` - Memory packages
    - `interface/` - Interface IC packages
  - `discrete/` - Discrete component footprints
    - `transistors/` - Transistor packages
    - `diodes/` - Diode packages
- `connectors/`
  - `board/` - Board connector footprints
  - `wire/` - Wire connector footprints
  - `rf/` - RF connector footprints
- `mechanical/`
  - `mounting/` - Mounting hardware footprints
  - `enclosure/` - Enclosure part footprints
- `power/`
  - `regulators/` - Regulator packages
  - `converters/` - Converter packages
  - `protection/` - Protection circuit packages
- `misc/` - Other footprints

### 3D Models (`3dmodels/`)
- `passive/`
  - `resistors/` - Resistor models
  - `capacitors/` - Capacitor models
  - `inductors/` - Inductor models
- `active/`
  - `sensors/` - Sensor models
    - `cmos_image/` - CMOS image sensor models
    - `environmental/` - Environmental sensor models
  - `ics/` - IC models
    - `microcontrollers/` - MCU models
    - `memory/` - Memory models
    - `interface/` - Interface IC models
  - `discrete/` - Discrete component models
    - `transistors/` - Transistor models
    - `diodes/` - Diode models
- `connectors/`
  - `board/` - Board connector models
  - `wire/` - Wire connector models
  - `rf/` - RF connector models
- `mechanical/`
  - `mounting/` - Mounting hardware models
  - `enclosure/` - Enclosure part models
- `power/`
  - `regulators/` - Regulator models
  - `converters/` - Converter models
  - `protection/` - Protection circuit models
- `misc/` - Other models

## Getting Started

1. **Setup Your Environment**
   - Follow the instructions in `docs/setup.md`
   - Make sure you can access the library in KiCad

2. **Fork and Clone**
   ```bash
   git clone https://github.com/<your-username>/kicad-lab-library.git
   cd kicad-lab-library
   git remote add upstream https://github.com/<org>/kicad-lab-library.git
   ```

## Adding New Components

### 1. Creating Symbols

1. Open KiCad and create a new project
2. Open the Symbol Editor
3. Create a new symbol following the KLC guidelines:
   - Use clear, descriptive names
   - Include all required fields
   - Follow pin numbering conventions
4. Save the symbol to the appropriate subdirectory in `symbols/`
   - Example: `symbols/active/sensors/cmos_image/OV2640.kicad_sym` for a CMOS image sensor

### 2. Creating Footprints

1. Open the Footprint Editor
2. Create a new footprint following the KLC guidelines:
   - Match symbol names when possible
   - Include package type in name
   - Follow IPC-7351 standards
3. Save the footprint to the appropriate subdirectory in `footprints/`
   - Example: `footprints/active/sensors/cmos_image/OV2640_CSP.kicad_mod` for a CMOS image sensor

### 3. Adding 3D Models

1. Create or obtain a 3D model (STEP or WRL format)
2. Place it in the appropriate subdirectory in `3dmodels/`
   - Example: `3dmodels/active/sensors/cmos_image/OV2640_CSP.wrl` for a CMOS image sensor
3. Link it in the footprint file

## Automated Validation & PR Requirements

**All contributions must:**
- Be submitted via a GitHub pull request (PR).
- Pass all automated validation and tests before being merged.
- Not be merged by maintainers unless all checks pass.

### What the Automated Validation Checks
- **Required fields**: All symbols and footprints must have all required fields (Reference, Value, Description, Keywords, Validated, etc.).
- **Naming conventions**: File and component names must follow the library's naming rules.
- **Pin/footprint matching**: For symbols with a linked footprint, pin numbers must match pad numbers in the footprint.
- **3D model references**: Footprints must reference valid 3D model files if applicable.
- **Datasheet links**: Datasheet fields must be valid URLs or reference an existing file.
- **Directory structure**: All files must be in the correct subdirectory according to the config.
- **No duplicates**: No duplicate symbol or footprint names.
- **Grouped validation output**: The validation script will print a grouped summary for each symbol and footprint, showing all passing (✓) and failing (❌) checks under each item.

### Optimized Validation and Rendering
The validation and rendering process has been optimized to only process changed files and symbols:

1. **Changed File Detection**:
   - For PRs: Files changed between the PR branch and target branch
   - For direct pushes to main: Files changed in the latest commit
   - Only relevant files are processed (symbols, footprints, 3D models)

2. **Symbol-Level Changes**:
   - For symbol files (.kicad_sym), only changed symbols are validated and rendered
   - Changes are detected at the individual symbol level
   - New, modified, and removed symbols are tracked separately

3. **Other Components**:
   - Footprints (.kicad_mod) are validated and rendered at the file level
   - 3D models (.step, .wrl) are validated and rendered at the file level
   - Datasheets are validated at the file level

4. **Running Validation Locally**:
   ```bash
   # Validate all files (backward compatible)
   python scripts/validate_libraries.py

   # Validate only changed files
   python scripts/validate_libraries.py --changed-files changed_files.txt
   ```

5. **Generating Renders Locally**:
   ```bash
   # Generate renders for all files (backward compatible)
   python scripts/generate_renders.py

   # Generate renders for changed files
   python scripts/generate_renders.py --changed-files changed_files.txt
   ```

### Running Validation Locally
Before submitting your PR, run the validation script:
```bash
python scripts/validate_libraries.py
```
Review the output. **All symbols and footprints you add or modify must show only passing checks (✓) in the grouped output.**

## Submitting Changes

1. Create a new branch:
   ```bash
   git checkout -b add-new-component
   ```

2. Add your changes:
   ```bash
   git add symbols/<category>/<subcategory>/
   git add footprints/<category>/<subcategory>/
   git add 3dmodels/<category>/<subcategory>/
   ```

3. Commit with a descriptive message:
   ```bash
   git commit -m "Add new component: [Component Name]"
   ```

4. Push to your fork:
   ```bash
   git push origin add-new-component
   ```

5. Create a pull request on GitHub

## Review & Merge Process

1. Your PR will be automatically validated by CI.
2. Review the grouped validation output in the PR checks for any errors or warnings.
3. A team member will review your changes and may request fixes.
4. **PRs will not be merged unless all validation checks pass.**
5. Once approved and passing, your changes will be merged.

## Best Practices

1. **Naming**
   - Use clear, descriptive names
   - Follow manufacturer part numbers
   - Include package type in footprint names
   - Place components in the correct category and subcategory

2. **Documentation**
   - Include datasheet links
   - Add clear descriptions
   - Use appropriate keywords
   - Document any special requirements or considerations

3. **3D Models**
   - Use STEP format for mechanical models
   - Keep file sizes reasonable
   - Ensure correct orientation
   - Include mounting information when relevant

4. **Testing**
   - Test components in a real project
   - Verify 3D model appearance
   - Check BOM generation
   - Test with different KiCad versions

## Resources

- [KLC Guidelines](KLC_GUIDELINES.md)
- [KiCad Documentation](https://docs.kicad.org/)
- [IPC-7351 Standards](https://www.ipc.org/standards) 