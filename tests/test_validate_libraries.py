import pytest
from scripts.validate_libraries import parse_kicad_sym, parse_kicad_mod, validate_component_fields, REQUIRED_SYMBOL_FIELDS, REQUIRED_FOOTPRINT_FIELDS, get_changed_files, get_changed_symbols, validate_symbol_file, validate_footprint_file, validate_directory_structure
import os
import tempfile
import shutil

def test_parse_kicad_sym():
    content = '''(kicad_symbol_lib
	(version 20241209)
	(generator "kicad_symbol_editor")
	(generator_version "9.0")
	(symbol "TestSymbol"
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(property "Reference" "C"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Value" ""
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Footprint" ""
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Datasheet" ""
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Description" ""
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Validated" "No"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Keywords" "cap"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(symbol "TestSymbol_0_1"
			(rectangle
				(start -3.81 8.89)
				(end 6.35 -6.35)
				(stroke
					(width 0)
					(type default)
				)
				(fill
					(type none)
				)
			)
		)
		(symbol "TestSymbol_1_1"
			(pin input line
				(at -6.35 5.08 0)
				(length 2.54)
				(name "1"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
				(number "1"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
			)
			(pin input line
				(at -6.35 -1.27 0)
				(length 2.54)
				(name "2"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
				(number "2"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
			)
		)
		(embedded_fonts no)
	)
)
'''
    symbols = parse_kicad_sym(content)
    assert len(symbols) == 1
    s = symbols[0]
    assert s['name'] == 'TestSymbol'
    for field in REQUIRED_SYMBOL_FIELDS:
        assert field in s['fields']
    assert s['fields']['Reference'] == 'C'
    # Do not check s['pins'] for KiCad 7+/9+ top-level symbols

def test_parse_kicad_mod():
    content = '''(footprint "TestFootprint"
  (property "Reference" "REF**" (at 0 0 0))
  (property "Value" "Test" (at 0 0 0))
  (property "Description" "desc" (at 0 0 0))
  (property "Keywords" "kw" (at 0 0 0))
  (property "Validated" "Yes" (at 0 0 0))
  (model "test.wrl")
)'''
    fp = parse_kicad_mod(content)
    assert fp['name'] == 'TestFootprint'
    for field in REQUIRED_FOOTPRINT_FIELDS:
        assert field in fp['fields']
    assert fp['fields']['Reference'] == 'REF**'
    assert fp['models'][0] == 'test.wrl'

def test_validate_component_fields_symbol():
    fields = {
        'Reference': 'R',
        'Value': 'Test',
        'Footprint': 'TestFootprint',
        'Datasheet': 'http://example.com',
        'Description': 'desc',
        'Keywords': 'kw',
        'Validated': 'Yes',
    }
    errors = validate_component_fields(fields, 'symbol', 'TestSymbol', 'passive', 'resistors')
    assert not errors

def test_validate_component_fields_footprint():
    fields = {
        'Reference': 'REF**',
        'Value': 'Test',
        'Description': 'desc',
        'Keywords': 'kw',
        'Validated': 'Yes',
    }
    errors = validate_component_fields(fields, 'footprint', 'TestFootprint', 'passive', 'resistors')
    assert not errors
    # Test invalid reference
    fields_bad = dict(fields)
    fields_bad['Reference'] = 'C1'
    errors = validate_component_fields(fields_bad, 'footprint', 'TestFootprint', 'passive', 'resistors')
    assert any('must be' in e for e in errors)

def test_parse_kicad_sym_multiline_pins():
    content = '''(kicad_symbol_lib
	(version 20241209)
	(generator "kicad_symbol_editor")
	(generator_version "9.0")
	(symbol "TestSymbol"
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(property "Reference" "C"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Value" ""
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Footprint" "Lab_Passive_Capacitors:Test_cap"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Datasheet" "empty"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Description" ""
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Validated" "No"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Keywords" "cap"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(symbol "TestSymbol_0_1"
			(rectangle
				(start -1.27 1.27)
				(end 6.35 -6.35)
				(stroke
					(width 0)
					(type default)
				)
				(fill
					(type none)
				)
			)
		)
		(symbol "TestSymbol_1_1"
			(pin input line
				(at -3.81 0 0)
				(length 2.54)
				(name "1"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
				(number "1"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
			)
			(pin input line
				(at -3.81 -2.54 0)
				(length 2.54)
				(name "2"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
				(number "2"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
			)
		)
		(embedded_fonts no)
	)
)
'''
    symbols = parse_kicad_sym(content)
    assert len(symbols) == 1
    s = symbols[0]
    assert s['name'] == 'TestSymbol'
    # Should find 2 pins with numbers '1' and '2'
    pin_numbers = sorted(pin['number'] for pin in s['pins'])
    assert pin_numbers == ['1', '2']

def test_get_changed_files():
    # Create a temporary file with changed files
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write('symbols/passive/resistors/test.kicad_sym\n')
        f.write('footprints/passive/resistors/test.kicad_mod\n')
        f.write('3dmodels/passive/resistors/test.step\n')
        f.write('datasheets/passive/resistors/test.pdf\n')
        temp_path = f.name

    try:
        # Test with valid file
        changed_files = get_changed_files(temp_path)
        assert changed_files is not None
        assert len(changed_files) == 4
        assert 'symbols/passive/resistors/test.kicad_sym' in changed_files
        assert 'footprints/passive/resistors/test.kicad_mod' in changed_files
        assert '3dmodels/passive/resistors/test.step' in changed_files
        assert 'datasheets/passive/resistors/test.pdf' in changed_files

        # Test with non-existent file
        assert get_changed_files('nonexistent.txt') is None

        # Test with empty file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        assert get_changed_files(temp_path) == set()
    finally:
        # Clean up temporary files
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_get_changed_symbols():
    # Create test symbol files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.kicad_sym', delete=False) as f:
        f.write('''(kicad_symbol_lib (version 20211123) (generator eeschema)
  (symbol "TestSymbol1" (pin_numbers hide) (pin_names (offset 0.254))
    (in_bom yes) (on_board yes)
    (property "Reference" "R" (id 0) (at 0 0 0))
    (property "Value" "TestSymbol1" (id 1) (at 0 2.54 0))
  )
  (symbol "TestSymbol2" (pin_numbers hide) (pin_names (offset 0.254))
    (in_bom yes) (on_board yes)
    (property "Reference" "R" (id 0) (at 0 0 0))
    (property "Value" "TestSymbol2" (id 1) (at 0 2.54 0))
  )
)''')
        sym_file = f.name

    try:
        # Test with single file
        changed_files = {sym_file}
        changed_symbols = get_changed_symbols(changed_files)
        assert sym_file in changed_symbols
        assert len(changed_symbols[sym_file]) == 2
        assert 'TestSymbol1' in changed_symbols[sym_file]
        assert 'TestSymbol2' in changed_symbols[sym_file]

        # Test with no symbol files
        changed_symbols = get_changed_symbols({'footprints/test.kicad_mod'})
        assert not changed_symbols

        # Test with invalid file
        changed_symbols = get_changed_symbols({'nonexistent.kicad_sym'})
        assert not changed_symbols

    finally:
        # Clean up temporary files
        if os.path.exists(sym_file):
            os.unlink(sym_file)

def test_validate_symbol_file_with_changes():
    # Create a test symbol file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.kicad_sym', delete=False) as f:
        f.write('''(kicad_symbol_lib (version 20211123) (generator eeschema)
  (symbol "TestSymbol1" (pin_numbers hide) (pin_names (offset 0.254))
    (in_bom yes) (on_board yes)
    (property "Reference" "R" (id 0) (at 0 0 0))
    (property "Value" "TestSymbol1" (id 1) (at 0 2.54 0))
    (property "Footprint" "" (id 2) (at 0 5.08 0))
    (property "Datasheet" "test.pdf" (id 3) (at 0 7.62 0))
  )
  (symbol "TestSymbol2" (pin_numbers hide) (pin_names (offset 0.254))
    (in_bom yes) (on_board yes)
    (property "Reference" "R" (id 0) (at 0 0 0))
    (property "Value" "TestSymbol2" (id 1) (at 0 2.54 0))
    (property "Footprint" "" (id 2) (at 0 5.08 0))
    (property "Datasheet" "test.pdf" (id 3) (at 0 7.62 0))
  )
)''')
        sym_file = f.name

    try:
        # Test validation with specific changed symbols
        changed_symbols = {sym_file: {'TestSymbol1'}}
        errors, warnings = validate_symbol_file(sym_file, 'passive', 'resistors', None, lambda x: None, changed_symbols)
        
        # Check that only TestSymbol1 was validated
        assert hasattr(validate_symbol_file, 'global_results')
        results = validate_symbol_file.global_results
        assert 'TestSymbol1' in results
        assert 'TestSymbol2' not in results

    finally:
        # Clean up temporary files
        if os.path.exists(sym_file):
            os.unlink(sym_file)

def test_validate_footprint_file_with_changes():
    # Create a test footprint file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.kicad_mod', delete=False) as f:
        f.write('''(kicad_pcb (version 20211123) (generator pcbnew)
  (module "TestFootprint" (layer F.Cu) (tedit 0)
    (at 0 0 0)
    (property "Reference" "REF**" (at 0 0 0))
    (property "Value" "TestFootprint" (at 0 2.54 0))
    (property "Description" "Test footprint" (at 0 5.08 0))
    (property "Keywords" "test" (at 0 7.62 0))
    (property "Validated" "Yes" (at 0 10.16 0))
  )
)''')
        mod_file = f.name

    try:
        # Test validation with changed file
        errors = validate_footprint_file(mod_file, 'passive', 'resistors', None, 'passive/resistors')
        
        # Check that the footprint was validated
        assert hasattr(validate_footprint_file, 'global_results')
        results = validate_footprint_file.global_results
        assert 'TestFootprint' in results
        assert not errors  # No validation errors

    finally:
        # Clean up temporary files
        if os.path.exists(mod_file):
            os.unlink(mod_file)

def test_validate_directory_structure_with_changes():
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directories
        os.makedirs(os.path.join(temp_dir, 'symbols', 'passive', 'resistors'))
        os.makedirs(os.path.join(temp_dir, 'footprints', 'passive', 'resistors'))
        os.makedirs(os.path.join(temp_dir, '3dmodels', 'passive', 'resistors'))
        os.makedirs(os.path.join(temp_dir, 'datasheets', 'passive', 'resistors'))

        # Test with changed files
        changed_files = {
            'symbols/passive/resistors/test.kicad_sym',
            'footprints/passive/resistors/test.kicad_mod'
        }

        # Call validate_directory_structure with temp_dir as lab_root
        passed, errors = validate_directory_structure(changed_files, lab_root=temp_dir)
        assert passed  # Directory structure should be valid
        assert not errors  # No errors should be reported 