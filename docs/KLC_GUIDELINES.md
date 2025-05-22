# KiCad Library Convention (KLC) Guidelines

This document outlines the standards we follow for our KiCad library components, based on the official [KiCad Library Convention](https://klc.kicad.org/).

## Symbol Guidelines

### Naming
- Use clear, descriptive names
- Follow manufacturer part numbers when available
- Prefix with manufacturer name for custom parts
- Example: `Texas_Instruments_TPS7A4700`

### Required Fields
- `Value`: Component value (e.g., "10k" for resistor)
- `Footprint`: Default footprint name
- `Datasheet`: URL to component datasheet
- `Description`: Brief component description
- `Keywords`: Search terms for finding the component

### Pin Configuration
- Number pins according to datasheet
- Use standard pin names
- Group related pins together
- Include power pins in logical positions

## Footprint Guidelines

### Naming
- Match symbol names when possible
- Include package type in name
- Example: `Texas_Instruments_TPS7A4700_SOT-223`

### Required Fields
- `Value`: Component value
- `Datasheet`: URL to component datasheet
- `Description`: Brief description
- `Keywords`: Search terms

### Design Rules
- Follow IPC-7351 standards for pad sizes
- Include courtyard layer
- Add assembly layer with component outline
- Include 3D model reference when available

## 3D Model Guidelines

### File Organization
- Store in `3dmodels/` directory
- Use STEP format for mechanical models
- Use WRL format for simple shapes
- Name files to match footprint names

### Model Requirements
- Origin at component center
- Correct orientation (top view)
- Proper scale (1:1)
- Include only necessary detail

## Validation

Before submitting changes:
1. Run the validation script:
   ```bash
   python scripts/validate_libraries.py
   ```
2. Check for:
   - Required fields
   - Correct naming
   - Valid 3D model references
   - No duplicate names

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run validation
5. Submit a pull request

## Resources

- [Official KLC Documentation](https://klc.kicad.org/)
- [KiCad Library Utils](https://github.com/KiCad/kicad-library-utils)
- [IPC-7351 Standards](https://www.ipc.org/standards) 