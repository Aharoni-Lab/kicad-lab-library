import pytest
from scripts.generate_renders import (
    get_changed_files, get_changed_symbols,
    generate_symbol_render, generate_footprint_render,
    generate_3d_render, run_kicad_cli
)
import os
import tempfile
import shutil
import subprocess

def has_kicad_cli():
    """Check if kicad-cli is available in the system."""
    try:
        result = subprocess.run(['kicad-cli', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def test_get_changed_files():
    # Create a temporary file with changed files
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write('symbols/passive/resistors/test.kicad_sym\n')
        f.write('footprints/passive/resistors/test.kicad_mod\n')
        f.write('3dmodels/passive/resistors/test.step\n')
        temp_path = f.name

    try:
        # Test with valid file
        changed_files = get_changed_files(temp_path)
        assert changed_files is not None
        assert len(changed_files) == 3
        assert 'symbols/passive/resistors/test.kicad_sym' in changed_files
        assert 'footprints/passive/resistors/test.kicad_mod' in changed_files
        assert '3dmodels/passive/resistors/test.step' in changed_files

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
    # Create test symbol files in symbols/ subdir
    with tempfile.TemporaryDirectory() as temp_dir:
        symbols_dir = os.path.join(temp_dir, 'symbols', 'passive', 'resistors')
        os.makedirs(symbols_dir)
        sym_file = os.path.join(symbols_dir, 'test.kicad_sym')
        with open(sym_file, 'w') as f:
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
        # Test with single file
        changed_files = {sym_file}
        changed_symbols = get_changed_symbols(changed_files)
        assert sym_file in changed_symbols
        assert len(changed_symbols[sym_file]) == 2
        assert 'TestSymbol1' in changed_symbols[sym_file]
        assert 'TestSymbol2' in changed_symbols[sym_file]
        # Test with no symbol files
        changed_symbols = get_changed_symbols({os.path.join(temp_dir, 'footprints', 'test.kicad_mod')})
        assert not changed_symbols
        # Test with invalid file
        changed_symbols = get_changed_symbols({'nonexistent.kicad_sym'})
        assert not changed_symbols

@pytest.mark.skipif(not has_kicad_cli(), reason="kicad-cli not available")
def test_generate_symbol_render():
    # Create a test symbol file in symbols/ subdir
    with tempfile.TemporaryDirectory() as temp_dir:
        symbols_dir = os.path.join(temp_dir, 'symbols', 'passive', 'resistors')
        os.makedirs(symbols_dir)
        sym_file = os.path.join(symbols_dir, 'test.kicad_sym')
        with open(sym_file, 'w') as f:
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
        output_dir = tempfile.mkdtemp()
        try:
            changed_symbols = {sym_file: {'TestSymbol1'}}
            success, outputs = generate_symbol_render(sym_file, output_dir, changed_symbols)
            assert success
            assert len(outputs) > 0
            assert any('TestSymbol1' in k for k in outputs.keys())
            assert not any('TestSymbol2' in k for k in outputs.keys())
        finally:
            shutil.rmtree(output_dir)

@pytest.mark.skipif(not has_kicad_cli(), reason="kicad-cli not available")
def test_generate_footprint_render():
    # Create a test footprint file in footprints/ subdir
    with tempfile.TemporaryDirectory() as temp_dir:
        footprints_dir = os.path.join(temp_dir, 'footprints', 'passive', 'resistors')
        os.makedirs(footprints_dir)
        mod_file = os.path.join(footprints_dir, 'test.kicad_mod')
        with open(mod_file, 'w') as f:
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
        output_dir = tempfile.mkdtemp()
        try:
            success, outputs = generate_footprint_render(mod_file, output_dir)
            assert success
            assert len(outputs) > 0
            assert any('top' in k for k in outputs.keys())
            assert any('bottom' in k for k in outputs.keys())
        finally:
            shutil.rmtree(output_dir)

@pytest.mark.skipif(not has_kicad_cli(), reason="kicad-cli not available")
def test_generate_3d_render():
    # Create a test STEP file in 3dmodels/ subdir
    with tempfile.TemporaryDirectory() as temp_dir:
        models_dir = os.path.join(temp_dir, '3dmodels', 'passive', 'resistors')
        os.makedirs(models_dir)
        step_file = os.path.join(models_dir, 'test.step')
        with open(step_file, 'wb') as f:
            f.write(b'')  # Empty file for testing
        output_dir = tempfile.mkdtemp()
        try:
            success, outputs = generate_3d_render(step_file, output_dir)
            assert success
            assert len(outputs) > 0
            assert any('iso' in k for k in outputs.keys())
        finally:
            shutil.rmtree(output_dir) 