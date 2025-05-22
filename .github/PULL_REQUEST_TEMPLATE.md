# New Component Addition

## Component Information
- **Component Name**: [e.g., OV2640 CMOS Image Sensor]
- **Manufacturer**: [e.g., OmniVision]
- **Part Number**: [e.g., OV2640-A71A]
- **Category**: [e.g., active/sensors/cmos_image]
- **Component Type**: [Symbol/Footprint/3D Model]
- **Validation Status**: [ ] Not Validated [ ] Validated (requires PCB verification)

## Files Added/Modified
<!-- List all files that are being added or modified -->
- `symbols/active/sensors/cmos_image/OV2640.kicad_sym`
- `footprints/active/sensors/cmos_image/OV2640_CSP.kicad_mod`
- `3dmodels/active/sensors/cmos_image/OV2640_CSP.wrl`
- `datasheets/active/sensors/cmos_image/OmniVision_OV2640-A71A_RevA.pdf`

## Component Renders
<!-- Note: Renders will be automatically generated and added to this PR -->
<!-- You can add additional screenshots below if needed -->

## Datasheet Information
- [ ] Datasheet is included in the repository
- [ ] Datasheet follows naming convention: `{manufacturer}_{part_number}_{revision}.{format}`
- [ ] Datasheet is placed in the correct category directory
- [ ] Datasheet file size is under 20MB
- [ ] Datasheet is in an allowed format (PDF, TXT, HTML)
- [ ] Datasheet link is provided in component fields
- [ ] Datasheet is properly referenced in symbol and footprint

## Validation
<!-- Check all that apply -->
- [ ] Component follows naming convention from `library_structure.yml`
- [ ] Component is placed in the correct category/subcategory
- [ ] All required fields are present in symbol/footprint
- [ ] 3D model file size is under 10MB
- [ ] Validation script passes (`python scripts/validate_libraries.py`)
- [ ] Component has been tested in a real project
- [ ] "Validated" field is set to "No" for new components

## Documentation
<!-- Check all that apply -->
- [ ] Datasheet link is provided
- [ ] Description is clear and accurate
- [ ] Keywords are appropriate
- [ ] Any special considerations are documented
- [ ] Validation status is clearly indicated

## Testing
<!-- Describe how you tested the component -->
- [ ] Symbol pins match datasheet
- [ ] Footprint dimensions match datasheet
- [ ] 3D model orientation is correct
- [ ] Component works in schematic capture
- [ ] Component works in PCB layout
- [ ] BOM generation works correctly

## Validation Process
<!-- For components marked as validated -->
- [ ] PCB has been manufactured and assembled
- [ ] Component functions as expected
- [ ] No issues with footprint or assembly
- [ ] All pins are accessible and functional
- [ ] Component meets datasheet specifications

## Additional Information
<!-- Add any other relevant information -->
- Why this component is needed
- Any special considerations for usage
- Known limitations or issues
- Related components or alternatives
- Validation process details (if validated)

## Checklist
<!-- Final checklist before submitting -->
- [ ] I have read and followed the [Contributing Guidelines](docs/CONTRIBUTING.md)
- [ ] My changes follow the [KLC Guidelines](docs/KLC_GUIDELINES.md)
- [ ] I have tested my changes
- [ ] I have updated the documentation if necessary
- [ ] My changes are compatible with KiCad 9.0
- [ ] Validation status is correctly set
- [ ] Datasheet is properly included and referenced

## Screenshots
<!-- Add screenshots of the component in KiCad if applicable -->
- Symbol in schematic editor
- Footprint in PCB editor
- 3D model in 3D viewer
- PCB implementation (if validated)

## Related Issues
<!-- Link any related issues here -->
Closes #[issue number] 