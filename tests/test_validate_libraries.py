import pytest
from scripts.validate_libraries import parse_kicad_sym, parse_kicad_mod, validate_component_fields, REQUIRED_SYMBOL_FIELDS, REQUIRED_FOOTPRINT_FIELDS

def test_parse_kicad_sym():
    content = '''(kicad_symbol_lib
	(version 20241209)
	(generator "kicad_symbol_editor")
	(generator_version "9.0")
	(symbol "TestSymbol"
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(property "Reference" "R"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Value" "Test"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Footprint" "TestFootprint"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Datasheet" "http://example.com"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Description" "desc"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Keywords" "kw"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Validated" "Yes"
			(at 0 0 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(symbol "TestSymbol_0_1"
			(pin input line
				(at 0 0 0)
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
    assert s['fields']['Reference'] == 'R'
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