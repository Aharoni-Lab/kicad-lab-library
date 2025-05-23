#!/usr/bin/env python3
"""
Validation script for CI: checks naming, duplicates, and file existence.
"""
import os
import sys
import json
import glob
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple

LAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(LAB_ROOT, 'config', 'library_structure.yml')

def load_config() -> Dict:
    """Load the library structure configuration."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        sys.exit(1)

# Load configuration
CONFIG = load_config()
CATEGORIES = CONFIG['categories']
REQUIRED_SYMBOL_FIELDS = set(CONFIG['validation']['required_symbol_fields'])
REQUIRED_FOOTPRINT_FIELDS = set(CONFIG['validation']['required_footprint_fields'])
MAX_3D_MODEL_SIZE = CONFIG['validation']['max_3d_model_size_mb'] * 1024 * 1024

def validate_directory_structure() -> Tuple[bool, List[str]]:
    """Validate that the actual directory structure matches the configuration."""
    errors = []
    required_dirs = set()
    
    # Build the set of required directories from the configuration
    for category in CATEGORIES:
        # Add main category directories
        for lib_type in ['symbols', 'footprints', '3dmodels']:
            required_dirs.add(os.path.join(LAB_ROOT, lib_type, category))
        
        # Add subcategory directories
        for subcategory in CATEGORIES[category]['subcategories']:
            for lib_type in ['symbols', 'footprints', '3dmodels']:
                required_dirs.add(os.path.join(LAB_ROOT, lib_type, category, subcategory))
            
            # Add nested subcategory directories if they exist
            if 'subcategories' in CATEGORIES[category]['subcategories'][subcategory]:
                for subsubcategory in CATEGORIES[category]['subcategories'][subcategory]['subcategories']:
                    for lib_type in ['symbols', 'footprints', '3dmodels']:
                        required_dirs.add(os.path.join(LAB_ROOT, lib_type, category, subcategory, subsubcategory))
    
    # Check for missing directories
    for required_dir in required_dirs:
        if not os.path.exists(required_dir):
            errors.append(f"Missing required directory: {os.path.relpath(required_dir, LAB_ROOT)}")
    
    # Check for unexpected directories
    for lib_type in ['symbols', 'footprints', '3dmodels']:
        lib_root = os.path.join(LAB_ROOT, lib_type)
        if not os.path.exists(lib_root):
            errors.append(f"Missing library root directory: {lib_type}/")
            continue
        
        # Check each category directory
        for category in os.listdir(lib_root):
            category_path = os.path.join(lib_root, category)
            if not os.path.isdir(category_path):
                continue
            
            if category not in CATEGORIES:
                errors.append(f"Unexpected category directory: {lib_type}/{category}/")
                continue
            
            # Check subcategories
            for subcategory in os.listdir(category_path):
                subcategory_path = os.path.join(category_path, subcategory)
                if not os.path.isdir(subcategory_path):
                    continue
                
                if subcategory not in CATEGORIES[category]['subcategories']:
                    errors.append(f"Unexpected subcategory directory: {lib_type}/{category}/{subcategory}/")
                    continue
                
                # Check nested subcategories
                if 'subcategories' in CATEGORIES[category]['subcategories'][subcategory]:
                    for subsubcategory in os.listdir(subcategory_path):
                        subsubcategory_path = os.path.join(subcategory_path, subsubcategory)
                        if not os.path.isdir(subsubcategory_path):
                            continue
                        
                        if subsubcategory not in CATEGORIES[category]['subcategories'][subcategory]['subcategories']:
                            errors.append(f"Unexpected nested subcategory directory: {lib_type}/{category}/{subcategory}/{subsubcategory}/")
    
    return len(errors) == 0, errors

def get_component_category(name: str) -> Tuple[str, str, str]:
    """Determine the category and subcategory of a component based on its name.
    Returns (category, subcategory, subsubcategory)"""
    for category, cat_info in CATEGORIES.items():
        for subcategory, subcat_info in cat_info['subcategories'].items():
            # Check for nested subcategories
            if 'subcategories' in subcat_info:
                for subsubcategory, subsubcat_info in subcat_info['subcategories'].items():
                    if any(name.startswith(prefix) for prefix in subsubcat_info.get('reference_prefixes', [])):
                        return category, subcategory, subsubcategory
            # Check regular subcategories
            elif any(name.startswith(prefix) for prefix in subcat_info.get('reference_prefixes', [])):
                return category, subcategory, None
    return 'misc', 'misc', None

def get_component_path(category: str, subcategory: str, subsubcategory: str = None) -> str:
    """Get the full path for a component based on its categories."""
    path = [category]
    if subcategory:
        path.append(subcategory)
    if subsubcategory:
        path.append(subsubcategory)
    return os.path.join(*path)

def get_reference_prefixes(category: str, subcategory: str, subsubcategory: str = None) -> List[str]:
    """Get the allowed reference prefixes for a given (sub)category."""
    try:
        if subsubcategory:
            return CATEGORIES[category]['subcategories'][subcategory]['subcategories'][subsubcategory].get('reference_prefixes', [])
        elif subcategory:
            return CATEGORIES[category]['subcategories'][subcategory].get('reference_prefixes', [])
        else:
            return CATEGORIES[category].get('reference_prefixes', [])
    except Exception:
        return []

def extract_pins_from_block(block: str) -> list:
    """Extract all pins from a symbol block, including multi-line pins and nested parentheses."""
    pins = []
    lines = block.split('\n')
    in_pin = False
    pin_lines = []
    paren_depth = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('(pin '):
            in_pin = True
            pin_lines = [line]
            paren_depth = stripped.count('(') - stripped.count(')')
        elif in_pin:
            pin_lines.append(line)
            paren_depth += line.count('(') - line.count(')')
            if paren_depth <= 0:
                # End of pin block
                pin_block = '\n'.join(pin_lines)
                import re
                number_match = re.search(r'\(number\s+"([^"]+)"', pin_block)
                name_match = re.search(r'\(name\s+"([^"]+)"', pin_block)
                pin = {
                    'number': number_match.group(1) if number_match else '',
                    'name': name_match.group(1) if name_match else '',
                    'type': 'unknown'
                }
                pins.append(pin)
                in_pin = False
                pin_lines = []
                paren_depth = 0
    return pins

def parse_kicad_sym(content: str) -> list:
    """Parse KiCad symbol file and extract only top-level symbol definitions, collecting pins from all nested sub-symbols."""
    symbols = []
    lines = content.split('\n')
    current_symbol = None
    symbol_depth = 0
    in_top_symbol = False
    block_lines = []

    for line in lines:
        line_stripped = line.lstrip()
        if line_stripped.startswith('(symbol '):
            if not in_top_symbol:
                # Start of a top-level symbol
                symbol_name = line_stripped.split('"')[1]
                current_symbol = {'name': symbol_name, 'fields': {}, 'pins': []}
                in_top_symbol = True
                symbol_depth = 1
                block_lines = [line]
            else:
                # Nested symbol (sub-symbol), just increase depth
                symbol_depth += 1
                block_lines.append(line)
        elif in_top_symbol:
            block_lines.append(line)
            if line_stripped.startswith('(property '):
                parts = line_stripped.split('"')
                if len(parts) >= 4:
                    field_name = parts[1]
                    field_value = parts[3]
                    current_symbol['fields'][field_name] = field_value
            # Track parentheses to know when the top-level symbol block ends
            symbol_depth += line_stripped.count('(') - line_stripped.count(')')
            if symbol_depth == 0:
                # Collect pins from all nested sub-symbols in block_lines (recursively)
                block = '\n'.join(block_lines)
                current_symbol['pins'] = extract_pins_from_block(block)
                symbols.append(current_symbol)
                current_symbol = None
                in_top_symbol = False
                block_lines = []
    return symbols

def validate_datasheet_reference(fields: Dict, component_type: str, name: str) -> List[str]:
    """Validate datasheet references and file existence."""
    errors = []
    
    if 'Datasheet' not in fields:
        errors.append(f"{component_type.title()} {name} missing 'Datasheet' field")
        return errors
    
    datasheet_ref = fields['Datasheet']
    
    # Check if it's a URL
    if datasheet_ref.startswith(('http://', 'https://')):
        # URL validation could be added here if needed
        pass
    else:
        # Check if it's a local file
        expected_cat, expected_subcat, expected_subsubcat = get_component_category(name)
        expected_path = get_component_path(expected_cat, expected_subcat, expected_subsubcat)
        datasheet_path = os.path.join(LAB_ROOT, 'datasheets', expected_path, datasheet_ref)
        
        if not os.path.exists(datasheet_path):
            errors.append(f"{component_type.title()} {name} references non-existent datasheet: {datasheet_ref}")
        else:
            # Check file size
            size = os.path.getsize(datasheet_path)
            if size == 0:
                errors.append(f"Empty datasheet file: {datasheet_ref}")
            elif size > CONFIG['datasheets']['max_size_mb'] * 1024 * 1024:
                errors.append(f"Large datasheet file (>{CONFIG['datasheets']['max_size_mb']}MB): {datasheet_ref}")
            
            # Check file format
            ext = os.path.splitext(datasheet_ref)[1].lower().lstrip('.')
            if ext not in CONFIG['datasheets']['allowed_formats']:
                errors.append(f"Invalid datasheet format: {datasheet_ref}. Allowed formats: {', '.join(CONFIG['datasheets']['allowed_formats'])}")
    
    return errors

def validate_component_fields(fields: Dict, component_type: str, name: str, category=None, subcategory=None, subsubcategory=None) -> List[str]:
    """Validate component fields and their values, including Reference prefix."""
    errors = []
    # Check required fields
    required_fields = REQUIRED_SYMBOL_FIELDS if component_type == 'symbol' else REQUIRED_FOOTPRINT_FIELDS
    missing_fields = set(required_fields)
    # Special handling for keywords field in symbols
    if component_type == 'symbol':
        if 'Keywords' in missing_fields and ('Keywords' in fields or 'ki_keywords' in fields):
            missing_fields.remove('Keywords')
    missing_fields -= set(fields.keys())
    if missing_fields:
        errors.append(f"{component_type.title()} {name} missing required fields: {', '.join(missing_fields)}")
    # Only check Validated value if present
    if 'Validated' in fields:
        validated_value = fields['Validated'].lower()
        if validated_value not in ['yes', 'no']:
            errors.append(f"{component_type.title()} {name} has invalid 'Validated' value: {fields['Validated']}. Must be 'Yes' or 'No'")
    # Check Reference field
    if component_type == 'symbol' and 'Reference' in fields:
        allowed_prefixes = get_reference_prefixes(category, subcategory, subsubcategory)
        ref_value = fields['Reference']
        if allowed_prefixes and not any(ref_value.startswith(prefix) for prefix in allowed_prefixes):
            errors.append(f"{component_type.title()} {name} Reference '{ref_value}' does not start with allowed prefixes: {', '.join(allowed_prefixes)}")
    elif component_type == 'footprint' and 'Reference' in fields:
        if fields['Reference'] != 'REF**':
            errors.append(f"Footprint {name} Reference field must be 'REF**', found '{fields['Reference']}'")
    # Only check datasheet for symbols
    if component_type == 'symbol':
        errors.extend(validate_datasheet_reference(fields, component_type, name))
    if not errors:
        print(f"✓ Symbol {name}: All required fields are present")
    return errors

def parse_kicad_mod(content: str) -> Dict:
    """Parse KiCad footprint file and extract footprint definition and pad numbers."""
    footprint = {'name': '', 'fields': {}, 'models': [], 'pads': set()}
    tags_value = None

    # Extract name (should match (footprint "NAME")
    name_match = re.search(r'\(footprint\s+"([^"]+)"', content)
    if name_match:
        footprint['name'] = name_match.group(1)

    # Extract fields from (property ...) lines and tags
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('(property "Reference"'):
            parts = line.split('"')
            if len(parts) > 3:
                footprint['fields']['Reference'] = parts[3]
        elif line.startswith('(property "Value"'):
            parts = line.split('"')
            if len(parts) > 3:
                footprint['fields']['Value'] = parts[3]
        elif line.startswith('(property "Description"'):
            parts = line.split('"')
            if len(parts) > 3:
                footprint['fields']['Description'] = parts[3]
        elif line.startswith('(property "Keywords"'):
            parts = line.split('"')
            if len(parts) > 3:
                footprint['fields']['Keywords'] = parts[3]
        elif line.startswith('(property "Validated"'):
            parts = line.split('"')
            if len(parts) > 3:
                footprint['fields']['Validated'] = parts[3]
        elif line.startswith('(model '):
            model_path = line.split('"')[1]
            footprint['models'].append(model_path)
        elif line.startswith('(pad '):
            # (pad "1" smd ...)
            pad_parts = line.split('"')
            if len(pad_parts) > 1:
                pad_number = pad_parts[1]
                footprint['pads'].add(pad_number)
        elif line.startswith('(tags '):
            # (tags "kword1 kword2")
            tag_match = re.match(r'\(tags\s+"([^"]*)"', line)
            if tag_match:
                tags_value = tag_match.group(2)
    # If no property Keywords, use tags as Keywords
    if 'Keywords' not in footprint['fields'] and tags_value is not None:
        footprint['fields']['Keywords'] = tags_value
    return footprint

def validate_symbol_file(sym_file, category, subcategory, subsubcategory, find_footprint_file_by_libprefix):
    errors = []
    warnings = []
    successes = {}  # symbol_name -> [success messages]
    try:
        with open(sym_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # Basic validation
        if not content.strip():
            errors.append(f"Empty symbol file: {sym_file}")
            return errors, warnings
        if "(kicad_symbol_lib" not in content:
            errors.append(f"Invalid symbol file format: {sym_file}")
            return errors, warnings
        # Parse and validate symbols
        symbols = parse_kicad_sym(content)
        if not symbols:
            return errors, warnings
        # Check each symbol
        symbol_names = set()
        for symbol in symbols:
            # Check for duplicates
            if symbol['name'] in symbol_names:
                errors.append(f"Duplicate symbol name: {symbol['name']}")
            symbol_names.add(symbol['name'])
            # Check fields and reference prefix
            errs = validate_component_fields(symbol['fields'], 'symbol', symbol['name'], category, subcategory, subsubcategory)
            if not errs:
                successes.setdefault(symbol['name'], []).append("All required fields are present")
            # If reference prefix error, add details
            if 'Reference' in symbol['fields']:
                allowed_prefixes = get_reference_prefixes(category, subcategory, subsubcategory)
                ref_value = symbol['fields']['Reference']
                if allowed_prefixes and not any(ref_value.startswith(prefix) for prefix in allowed_prefixes):
                    errs.append(f"Reference field '{ref_value}' does not match allowed prefixes: {allowed_prefixes}")
            errors.extend([f"Symbol {symbol['name']}:\n    - {e}" for e in errs])
            # Check pins (warning only)
            if not symbol['pins']:
                warnings.append(f"⚠️ Symbol {symbol['name']} has no pins (file: {sym_file})")
            # Check pin/footprint pad match if Footprint field is set
            if 'Footprint' in symbol['fields'] and symbol['fields']['Footprint']:
                fp_file = find_footprint_file_by_libprefix(symbol['fields']['Footprint'])
                if fp_file and symbol['pins']:
                    with open(fp_file, 'r', encoding='utf-8') as fpf:
                        fp = parse_kicad_mod(fpf.read())
                    symbol_pins = set(pin['number'] for pin in symbol['pins'])
                    footprint_pads = fp.get('pads', set())
                    if symbol_pins != footprint_pads:
                        errors.append(f"Symbol {symbol['name']}:\n    - Pin numbers {sorted(symbol_pins)} do not match footprint pads {sorted(footprint_pads)} (footprint: {fp_file})")
                    else:
                        n = len(symbol_pins)
                        successes.setdefault(symbol['name'], []).append(f"All {n} symbol pins match {n} footprint pads")
                elif not fp_file:
                    errors.append(f"Symbol {symbol['name']}:\n    - Footprint '{symbol['fields']['Footprint']}' not found for pin check")
    except Exception as e:
        errors.append(f"Error processing {sym_file}: {str(e)}")
    # Store successes globally for check_symbols to print
    validate_symbol_file.global_successes = successes
    return errors, warnings

def check_symbols() -> Tuple[bool, List[str]]:
    """Validate symbol library files."""
    errors = []
    warnings = []
    successes = {}  # New: group success messages by symbol name
    def find_footprint_file_by_libprefix(footprint_field: str) -> str:
        if ':' not in footprint_field:
            return None
        lib_prefix, fp_name = footprint_field.split(':', 1)
        if lib_prefix.startswith('Lab_'):
            parts = lib_prefix[4:].split('_')
            subdir = '/'.join([p.lower() for p in parts])
            fp_path = f'footprints/{subdir}/{fp_name}.kicad_mod'
            abs_fp_path = os.path.join(LAB_ROOT, fp_path)
            if os.path.exists(abs_fp_path):
                return abs_fp_path
        return None
    for category, cat_info in CATEGORIES.items():
        for subcategory, subcat_info in cat_info['subcategories'].items():
            # Handle nested subcategories
            if 'subcategories' in subcat_info:
                for subsubcategory, subsubcat_info in subcat_info['subcategories'].items():
                    symbol_dir = os.path.join(LAB_ROOT, 'symbols', get_component_path(category, subcategory, subsubcategory))
                    if not os.path.exists(symbol_dir):
                        continue
                    sym_files = glob.glob(os.path.join(symbol_dir, "*.kicad_sym"))
                    if not sym_files:
                        continue
                    for sym_file in sym_files:
                        file_errors, file_warnings = validate_symbol_file(sym_file, category, subcategory, subsubcategory, find_footprint_file_by_libprefix)
                        errors.extend(file_errors)
                        warnings.extend(file_warnings)
                        # Collect successes from global_successes (set below)
                        if hasattr(validate_symbol_file, 'global_successes'):
                            for symbol_name, msgs in validate_symbol_file.global_successes.items():
                                successes.setdefault(symbol_name, []).extend(msgs)
                            validate_symbol_file.global_successes = {}  # Reset for next file
            else:
                symbol_dir = os.path.join(LAB_ROOT, 'symbols', get_component_path(category, subcategory))
                if not os.path.exists(symbol_dir):
                    continue
                sym_files = glob.glob(os.path.join(symbol_dir, "*.kicad_sym"))
                if not sym_files:
                    continue
                for sym_file in sym_files:
                    file_errors, file_warnings = validate_symbol_file(sym_file, category, subcategory, None, find_footprint_file_by_libprefix)
                    errors.extend(file_errors)
                    warnings.extend(file_warnings)
                    if hasattr(validate_symbol_file, 'global_successes'):
                        for symbol_name, msgs in validate_symbol_file.global_successes.items():
                            successes.setdefault(symbol_name, []).extend(msgs)
                        validate_symbol_file.global_successes = {}
    # Print grouped successes
    if successes:
        print("\nPassed:")
        for symbol, msgs in successes.items():
            print(f"  ✓ Symbol {symbol}:")
            for msg in msgs:
                print(f"      ✓ {msg}")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(w)
    return len(errors) == 0, errors

def validate_footprint_file(mod_file, category, subcategory, subsubcategory, expected_path):
    errors = []
    successes = {}  # footprint_name -> [success messages]
    try:
        with open(mod_file, 'r', encoding='utf-8') as f:
            content = f.read()
        footprint = parse_kicad_mod(content)
        # Use file path to determine category
        actual_path = os.path.relpath(os.path.dirname(mod_file), os.path.join(LAB_ROOT, 'footprints'))
        if expected_path != actual_path:
            errors.append(f"Footprint {footprint['name']}: should be in {expected_path}/ not {actual_path}/")
        else:
            successes.setdefault(footprint['name'], []).append(f"Footprint is in correct directory: {expected_path}/")
        # Check for duplicates (handled in main loop)
        # Check fields
        field_errs = validate_component_fields(footprint['fields'], 'footprint', footprint['name'], category, subcategory, subsubcategory)
        if not field_errs:
            successes.setdefault(footprint['name'], []).append("All required fields are present")
        errors.extend(field_errs)
        # Check 3D models
        for model in footprint['models']:
            model_path = os.path.join(LAB_ROOT, '3dmodels', expected_path, model)
            if not os.path.exists(model_path):
                errors.append(f"Footprint {footprint['name']}: references missing 3D model: {model}")
            else:
                successes.setdefault(footprint['name'], []).append(f"3D model '{model}' found")
    except Exception as e:
        errors.append(f"Footprint error processing {mod_file}: {str(e)}")
    # Store successes globally for check_footprints to print
    validate_footprint_file.global_successes = successes
    return errors

def check_footprints() -> Tuple[bool, List[str]]:
    """Validate footprint libraries."""
    errors = []
    successes = {}  # New: group success messages by footprint name
    for category, cat_info in CATEGORIES.items():
        for subcategory, subcat_info in cat_info['subcategories'].items():
            # Handle nested subcategories
            if 'subcategories' in subcat_info:
                for subsubcategory, subsubcat_info in subcat_info['subcategories'].items():
                    footprint_dir = os.path.join(LAB_ROOT, 'footprints', get_component_path(category, subcategory, subsubcategory))
                    if not os.path.exists(footprint_dir):
                        continue
                    mod_files = glob.glob(os.path.join(footprint_dir, "*.kicad_mod"))
                    if not mod_files:
                        continue
                    footprint_names = set()
                    expected_path = get_component_path(category, subcategory, subsubcategory)
                    for mod_file in mod_files:
                        file_errors = validate_footprint_file(mod_file, category, subcategory, subsubcategory, expected_path)
                        # Collect successes from global_successes (set below)
                        if hasattr(validate_footprint_file, 'global_successes'):
                            for fp_name, msgs in validate_footprint_file.global_successes.items():
                                successes.setdefault(fp_name, []).extend(msgs)
                            validate_footprint_file.global_successes = {}
                        # Check for duplicates
                        with open(mod_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        footprint = parse_kicad_mod(content)
                        if footprint['name'] in footprint_names:
                            errors.append(f"Footprint {footprint['name']}: duplicate footprint name")
                        footprint_names.add(footprint['name'])
                        errors.extend(file_errors)
            else:
                footprint_dir = os.path.join(LAB_ROOT, 'footprints', get_component_path(category, subcategory))
                if not os.path.exists(footprint_dir):
                    continue
                mod_files = glob.glob(os.path.join(footprint_dir, "*.kicad_mod"))
                if not mod_files:
                    continue
                footprint_names = set()
                expected_path = get_component_path(category, subcategory)
                for mod_file in mod_files:
                    file_errors = validate_footprint_file(mod_file, category, subcategory, None, expected_path)
                    if hasattr(validate_footprint_file, 'global_successes'):
                        for fp_name, msgs in validate_footprint_file.global_successes.items():
                            successes.setdefault(fp_name, []).extend(msgs)
                        validate_footprint_file.global_successes = {}
                    # Check for duplicates
                    with open(mod_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    footprint = parse_kicad_mod(content)
                    if footprint['name'] in footprint_names:
                        errors.append(f"Footprint {footprint['name']}: duplicate footprint name")
                    footprint_names.add(footprint['name'])
                    errors.extend(file_errors)
    # Print grouped successes
    if successes:
        print("\nPassed:")
        for fp, msgs in successes.items():
            print(f"  ✓ Footprint {fp}:")
            for msg in msgs:
                print(f"      ✓ {msg}")
    return len(errors) == 0, errors

def check_3d_models() -> Tuple[bool, List[str]]:
    """Validate 3D model files."""
    errors = []
    
    # Check each category directory
    for category, cat_info in CATEGORIES.items():
        for subcategory, subcat_info in cat_info['subcategories'].items():
            # Handle nested subcategories
            if 'subcategories' in subcat_info:
                for subsubcategory, subsubcat_info in subcat_info['subcategories'].items():
                    model_dir = os.path.join(LAB_ROOT, '3dmodels', get_component_path(category, subcategory, subsubcategory))
                    if not os.path.exists(model_dir):
                        continue
                    
                    # Check for STEP and WRL files
                    step_files = glob.glob(os.path.join(model_dir, "*.step"))
                    wrl_files = glob.glob(os.path.join(model_dir, "*.wrl"))
                    
                    # Check file sizes and names, group errors by file
                    for file in step_files + wrl_files:
                        file_errors = []
                        try:
                            # Check file size
                            size = os.path.getsize(file)
                            if size == 0:
                                file_errors.append(f"Empty 3D model file")
                            elif size > MAX_3D_MODEL_SIZE:
                                file_errors.append(f"Large 3D model file (>{CONFIG['validation']['max_3d_model_size_mb']}MB)")
                        except Exception as e:
                            file_errors.append(f"Error checking file: {str(e)}")
                        if file_errors:
                            errors.append((os.path.basename(file), file_errors))
            else:
                # Handle regular subcategories
                model_dir = os.path.join(LAB_ROOT, '3dmodels', get_component_path(category, subcategory))
                if not os.path.exists(model_dir):
                    continue
                
                # Check for STEP and WRL files
                step_files = glob.glob(os.path.join(model_dir, "*.step"))
                wrl_files = glob.glob(os.path.join(model_dir, "*.wrl"))
                
                # Check file sizes and names, group errors by file
                for file in step_files + wrl_files:
                    file_errors = []
                    try:
                        # Check file size
                        size = os.path.getsize(file)
                        if size == 0:
                            file_errors.append(f"Empty 3D model file")
                        elif size > MAX_3D_MODEL_SIZE:
                            file_errors.append(f"Large 3D model file (>{CONFIG['validation']['max_3d_model_size_mb']}MB)")
                    except Exception as e:
                        file_errors.append(f"Error checking file: {str(e)}")
                    if file_errors:
                        errors.append((os.path.basename(file), file_errors))
    # Flatten errors for main error reporting
    grouped_errors = []
    for fname, ferrs in errors:
        grouped_errors.append(f"3D Model {fname}:")
        for ferr in ferrs:
            grouped_errors.append(f"    - {ferr}")
    return len(grouped_errors) == 0, grouped_errors

def validate_datasheet_file(file_path, allowed_formats, max_size_mb, naming_convention):
    errors = []
    try:
        size = os.path.getsize(file_path)
        if size == 0:
            errors.append(f"Empty datasheet file: {os.path.basename(file_path)}")
        elif size > max_size_mb:
            errors.append(f"Large datasheet file (>{max_size_mb // (1024*1024)}MB): {os.path.basename(file_path)}")
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        if ext not in allowed_formats:
            errors.append(f"Invalid datasheet format: {os.path.basename(file_path)}. Allowed formats: {', '.join(allowed_formats)}")
        if not re.match(naming_convention, os.path.basename(file_path)):
            errors.append(f"Datasheet {os.path.basename(file_path)} does not follow naming convention: {naming_convention}")
    except Exception as e:
        errors.append(f"Error checking {os.path.basename(file_path)}: {str(e)}")
    return errors

def check_datasheets() -> Tuple[bool, List[str]]:
    """Validate datasheet files and references."""
    errors = []
    allowed_formats = CONFIG['datasheets']['allowed_formats']
    max_size_mb = CONFIG['datasheets']['max_size_mb'] * 1024 * 1024
    naming_convention = CONFIG['datasheets']['naming_convention']
    for category, cat_info in CATEGORIES.items():
        for subcategory, subcat_info in cat_info['subcategories'].items():
            # Handle nested subcategories
            if 'subcategories' in subcat_info:
                for subsubcategory, subsubcat_info in subcat_info['subcategories'].items():
                    datasheet_dir = os.path.join(LAB_ROOT, 'datasheets', get_component_path(category, subcategory, subsubcategory))
                    if not os.path.exists(datasheet_dir):
                        continue
                    for file in os.listdir(datasheet_dir):
                        file_path = os.path.join(datasheet_dir, file)
                        if not os.path.isfile(file_path):
                            continue
                        file_errors = validate_datasheet_file(file_path, allowed_formats, max_size_mb, naming_convention)
                        errors.extend(file_errors)
            else:
                datasheet_dir = os.path.join(LAB_ROOT, 'datasheets', get_component_path(category, subcategory))
                if not os.path.exists(datasheet_dir):
                    continue
                for file in os.listdir(datasheet_dir):
                    file_path = os.path.join(datasheet_dir, file)
                    if not os.path.isfile(file_path):
                        continue
                    file_errors = validate_datasheet_file(file_path, allowed_formats, max_size_mb, naming_convention)
                    errors.extend(file_errors)
    return len(errors) == 0, errors

def main():
    """Run all validation checks."""
    print("Running KiCad library validation...")
    
    checks = [
        ("Directory Structure", validate_directory_structure),
        ("Symbols", check_symbols),
        ("Footprints", check_footprints),
        ("3D Models", check_3d_models),
        ("Datasheets", check_datasheets)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        passed, errors = check_func()
        if not passed:
            print(f"❌ {name} validation failed:")
            # Group errors by component if possible
            grouped = {}
            for error in errors:
                # Try to extract component name
                match = re.match(r'(Symbol|Footprint) ([^ ]*) (.*)', error)
                if match:
                    comp_type, comp_name, msg = match.groups()
                    key = f"{comp_type} {comp_name}".strip()
                    grouped.setdefault(key, []).append(msg)
                else:
                    grouped.setdefault('Other', []).append(error)
            for comp, msgs in grouped.items():
                print(f"  - {comp}:")
                for msg in msgs:
                    # Remove redundant component name from the message if present
                    cleaned_msg = re.sub(r'^\s*-+\s*(Symbol|Footprint) [^:]+:?\s*', '- ', msg)
                    print(f"      {cleaned_msg}")
            all_passed = False
        else:
            print(f"✓ {name} validation passed")
    
    if not all_passed:
        print("\nValidation failed. Please fix the issues above.")
        sys.exit(1)
    else:
        print("\nAll validations passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()
    