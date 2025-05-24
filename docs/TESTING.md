# Testing Plan for Optimized Validation and Rendering

This document outlines the test cases for verifying the optimized validation and rendering process.

## Test Environment Setup

1. Create a test branch:
   ```bash
   git checkout -b test-optimized-validation
   ```

2. Create test directories:
   ```bash
   mkdir -p test/{symbols,footprints,3dmodels,datasheets}/{passive,active}/{resistors,capacitors}
   ```

## Test Cases

### 1. Symbol File Changes

#### 1.1 New Symbol File
```bash
# Create a new symbol file
echo '(kicad_symbol_lib (version 20211123) (generator eeschema)
  (symbol "Test_Resistor" (pin_numbers hide) (pin_names (offset 0.254))
    (in_bom yes) (on_board yes)
    (property "Reference" "R" (id 0) (at 0 0 0))
    (property "Value" "Test_Resistor" (id 1) (at 0 2.54 0))
    (property "Footprint" "" (id 2) (at 0 5.08 0))
    (property "Datasheet" "test.pdf" (id 3) (at 0 7.62 0))
  )
)' > test/symbols/passive/resistors/test_resistor.kicad_sym

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt

# Test rendering
python scripts/generate_renders.py --changed-files changed_files.txt
```

#### 1.2 Modified Symbol in Existing File
```bash
# Modify an existing symbol file
sed -i 's/Test_Resistor/Modified_Resistor/' test/symbols/passive/resistors/test_resistor.kicad_sym

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt

# Test rendering
python scripts/generate_renders.py --changed-files changed_files.txt
```

#### 1.3 Multiple Symbols in One File
```bash
# Add a second symbol to the file
echo '
  (symbol "Test_Capacitor" (pin_numbers hide) (pin_names (offset 0.254))
    (in_bom yes) (on_board yes)
    (property "Reference" "C" (id 0) (at 0 0 0))
    (property "Value" "Test_Capacitor" (id 1) (at 0 2.54 0))
    (property "Footprint" "" (id 2) (at 0 5.08 0))
    (property "Datasheet" "test.pdf" (id 3) (at 0 7.62 0))
  )' >> test/symbols/passive/resistors/test_resistor.kicad_sym

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt

# Test rendering
python scripts/generate_renders.py --changed-files changed_files.txt
```

### 2. Footprint Changes

#### 2.1 New Footprint
```bash
# Create a new footprint file
echo '(kicad_pcb (version 20211123) (generator pcbnew)
  (module "Test_Resistor" (layer F.Cu) (tedit 0)
    (at 0 0 0)
    (property "Reference" "REF**" (at 0 0 0))
    (property "Value" "Test_Resistor" (at 0 2.54 0))
    (property "Footprint" "Test_Resistor" (at 0 5.08 0))
  )
)' > test/footprints/passive/resistors/test_resistor.kicad_mod

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt

# Test rendering
python scripts/generate_renders.py --changed-files changed_files.txt
```

#### 2.2 Modified Footprint
```bash
# Modify the footprint
sed -i 's/Test_Resistor/Modified_Resistor/' test/footprints/passive/resistors/test_resistor.kicad_mod

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt

# Test rendering
python scripts/generate_renders.py --changed-files changed_files.txt
```

### 3. 3D Model Changes

#### 3.1 New 3D Model
```bash
# Create a test STEP file (empty file for testing)
touch test/3dmodels/passive/resistors/test_resistor.step

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt

# Test rendering
python scripts/generate_renders.py --changed-files changed_files.txt
```

### 4. Datasheet Changes

#### 4.1 New Datasheet
```bash
# Create a test PDF file (empty file for testing)
touch test/datasheets/passive/resistors/test.pdf

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt
```

### 5. Directory Structure Changes

#### 5.1 New Directory
```bash
# Create a new subcategory
mkdir -p test/symbols/passive/inductors
mkdir -p test/footprints/passive/inductors
mkdir -p test/3dmodels/passive/inductors
mkdir -p test/datasheets/passive/inductors

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt
```

### 6. Mixed Changes

#### 6.1 Multiple File Types
```bash
# Create a new component with all file types
echo '(kicad_symbol_lib (version 20211123) (generator eeschema)
  (symbol "Test_Component" (pin_numbers hide) (pin_names (offset 0.254))
    (in_bom yes) (on_board yes)
    (property "Reference" "U" (id 0) (at 0 0 0))
    (property "Value" "Test_Component" (id 1) (at 0 2.54 0))
    (property "Footprint" "" (id 2) (at 0 5.08 0))
    (property "Datasheet" "test.pdf" (id 3) (at 0 7.62 0))
  )
)' > test/symbols/active/capacitors/test_component.kicad_sym

echo '(kicad_pcb (version 20211123) (generator pcbnew)
  (module "Test_Component" (layer F.Cu) (tedit 0)
    (at 0 0 0)
    (property "Reference" "REF**" (at 0 0 0))
    (property "Value" "Test_Component" (at 0 2.54 0))
    (property "Footprint" "Test_Component" (at 0 5.08 0))
  )
)' > test/footprints/active/capacitors/test_component.kicad_mod

touch test/3dmodels/active/capacitors/test_component.step
touch test/datasheets/active/capacitors/test.pdf

# Test validation
python scripts/validate_libraries.py --changed-files changed_files.txt

# Test rendering
python scripts/generate_renders.py --changed-files changed_files.txt
```

## Expected Results

1. **Validation**:
   - Only changed files should be validated
   - For symbol files, only changed symbols should be validated
   - Validation output should show grouped results for each component
   - All required fields should be checked
   - Directory structure should be validated

2. **Rendering**:
   - Only changed files should be rendered
   - For symbol files, only changed symbols should be rendered
   - Renders should be generated in the correct format (SVG/PNG)
   - Renders should be optimized for size

3. **Performance**:
   - Processing time should be significantly reduced when only changed files are processed
   - Memory usage should be proportional to the number of changed files

## Cleanup

After testing:
```bash
# Remove test files
rm -rf test/

# Switch back to main branch
git checkout main
```

## Reporting Issues

If you encounter any issues during testing:
1. Document the exact steps to reproduce
2. Note the expected vs actual behavior
3. Include any error messages or logs
4. Create an issue in the repository with the "bug" label 