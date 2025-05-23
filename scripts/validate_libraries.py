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

def parse_kicad_sym(content: str) -> List[Dict]:
    """Parse KiCad symbol file and extract only top-level symbol definitions."""
    symbols = []
    lines = content.split('\n')
    stack = []
    current_symbol = None

    for line in lines:
        line_stripped = line.lstrip()
        if line_stripped.startswith('(symbol '):
            stack.append('symbol')
            if len(stack) == 1:
                # Top-level symbol
                if current_symbol:
                    symbols.append(current_symbol)
                symbol_name = line_stripped.split('"')[1]
                current_symbol = {'name': symbol_name, 'fields': {}, 'pins': []}
        elif line_stripped.startswith('(property ') and current_symbol and len(stack) == 1:
            parts = line_stripped.split('"')
            if len(parts) >= 4:
                field_name = parts[1]
                field_value = parts[3]
                current_symbol['fields'][field_name] = field_value
        elif line_stripped.startswith('(pin ') and current_symbol and len(stack) == 1:
            parts = line_stripped.split('"')
            if len(parts) >= 4:
                pin = {
                    'number': parts[1],
                    'name': parts[3],
                    'type': parts[5] if len(parts) > 5 else 'unknown'
                }
                current_symbol['pins'].append(pin)
        if line_stripped.startswith('('):
            # Count open parens
            stack.extend(['('] * (line_stripped.count('(') - (1 if line_stripped.startswith('(symbol ') else 0)))
        if line_stripped.endswith(')'):
            # Count close parens
            for _ in range(line_stripped.count(')')):
                if stack:
                    stack.pop()
            if not stack and current_symbol:
                symbols.append(current_symbol)
                current_symbol = None

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
    missing_fields = required_fields - set(fields.keys())
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
    return errors

def check_symbols() -> Tuple[bool, List[str]]:
    """Validate symbol library files."""
    errors = []
    
    # Check each category directory
    for category, cat_info in CATEGORIES.items():
        for subcategory, subcat_info in cat_info['subcategories'].items():
            # Handle nested subcategories
            if 'subcategories' in subcat_info:
                for subsubcategory, subsubcat_info in subcat_info['subcategories'].items():
                    symbol_dir = os.path.join(LAB_ROOT, 'symbols', get_component_path(category, subcategory, subsubcategory))
                    if not os.path.exists(symbol_dir):
                        continue
                    
                    # Find all .kicad_sym files
                    sym_files = glob.glob(os.path.join(symbol_dir, "*.kicad_sym"))
                    if not sym_files:
                        continue
                    
                    for sym_file in sym_files:
                        try:
                            with open(sym_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Basic validation
                            if not content.strip():
                                errors.append(f"Empty symbol file: {sym_file}")
                                continue
                            
                            if "(kicad_symbol_lib" not in content:
                                errors.append(f"Invalid symbol file format: {sym_file}")
                                continue
                            
                            # Parse and validate symbols
                            symbols = parse_kicad_sym(content)
                            if not symbols:
                                continue
                            
                            # Check each symbol
                            symbol_names = set()
                            for symbol in symbols:
                                # Check category
                                expected_cat, expected_subcat, expected_subsubcat = get_component_category(symbol['name'])
                                expected_path = get_component_path(expected_cat, expected_subcat, expected_subsubcat)
                                actual_path = get_component_path(category, subcategory, subsubcategory)
                                if expected_path != actual_path:
                                    errors.append(f"Symbol {symbol['name']} should be in {expected_path}/ not {actual_path}/")
                                
                                # Check for duplicates
                                if symbol['name'] in symbol_names:
                                    errors.append(f"Duplicate symbol name: {symbol['name']}")
                                symbol_names.add(symbol['name'])
                                
                                # Check fields
                                errors.extend(validate_component_fields(symbol['fields'], 'symbol', symbol['name'], category, subcategory, subsubcategory))
                                
                                # Check pins
                                if not symbol['pins']:
                                    errors.append(f"Symbol {symbol['name']} has no pins")
                                else:
                                    pin_numbers = set()
                                    for pin in symbol['pins']:
                                        if pin['number'] in pin_numbers:
                                            errors.append(f"Symbol {symbol['name']} has duplicate pin number: {pin['number']}")
                                        pin_numbers.add(pin['number'])
                        
                        except Exception as e:
                            errors.append(f"Error processing {sym_file}: {str(e)}")
            else:
                # Handle regular subcategories
                symbol_dir = os.path.join(LAB_ROOT, 'symbols', get_component_path(category, subcategory))
                if not os.path.exists(symbol_dir):
                    continue
                
                # Find all .kicad_sym files
                sym_files = glob.glob(os.path.join(symbol_dir, "*.kicad_sym"))
                if not sym_files:
                    continue
                
                for sym_file in sym_files:
                    try:
                        with open(sym_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Basic validation
                        if not content.strip():
                            errors.append(f"Empty symbol file: {sym_file}")
                            continue
                        
                        if "(kicad_symbol_lib" not in content:
                            errors.append(f"Invalid symbol file format: {sym_file}")
                            continue
                        
                        # Parse and validate symbols
                        symbols = parse_kicad_sym(content)
                        if not symbols:
                            continue
                        
                        # Check each symbol
                        symbol_names = set()
                        for symbol in symbols:
                            # Check category
                            expected_cat, expected_subcat, _ = get_component_category(symbol['name'])
                            expected_path = get_component_path(expected_cat, expected_subcat)
                            actual_path = get_component_path(category, subcategory)
                            if expected_path != actual_path:
                                errors.append(f"Symbol {symbol['name']} should be in {expected_path}/ not {actual_path}/")
                            
                            # Check for duplicates
                            if symbol['name'] in symbol_names:
                                errors.append(f"Duplicate symbol name: {symbol['name']}")
                            symbol_names.add(symbol['name'])
                            
                            # Check fields
                            errors.extend(validate_component_fields(symbol['fields'], 'symbol', symbol['name'], category, subcategory))
                            
                            # Check pins
                            if not symbol['pins']:
                                errors.append(f"Symbol {symbol['name']} has no pins")
                            else:
                                pin_numbers = set()
                                for pin in symbol['pins']:
                                    if pin['number'] in pin_numbers:
                                        errors.append(f"Symbol {symbol['name']} has duplicate pin number: {pin['number']}")
                                    pin_numbers.add(pin['number'])
                    
                    except Exception as e:
                        errors.append(f"Error processing {sym_file}: {str(e)}")
    
    return len(errors) == 0, errors

def parse_kicad_mod(content: str) -> Dict:
    """Parse KiCad footprint file and extract footprint definition."""
    footprint = {'name': '', 'fields': {}, 'models': []}

    # Extract name (should match (footprint "NAME")
    name_match = re.search(r'\(footprint\s+"([^"]+)"', content)
    if name_match:
        footprint['name'] = name_match.group(1)

    # Extract fields from (property ...) lines
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

    return footprint

def check_footprints() -> Tuple[bool, List[str]]:
    """Validate footprint libraries."""
    errors = []
    
    # Check each category directory
    for category, cat_info in CATEGORIES.items():
        for subcategory, subcat_info in cat_info['subcategories'].items():
            # Handle nested subcategories
            if 'subcategories' in subcat_info:
                for subsubcategory, subsubcat_info in subcat_info['subcategories'].items():
                    footprint_dir = os.path.join(LAB_ROOT, 'footprints', get_component_path(category, subcategory, subsubcategory))
                    if not os.path.exists(footprint_dir):
                        continue
                    
                    # Find all .kicad_mod files
                    mod_files = glob.glob(os.path.join(footprint_dir, "*.kicad_mod"))
                    if not mod_files:
                        continue
                    
                    # Check each footprint
                    footprint_names = set()
                    for mod_file in mod_files:
                        try:
                            with open(mod_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            footprint = parse_kicad_mod(content)
                            
                            # Use file path to determine category
                            expected_path = get_component_path(category, subcategory, subsubcategory)
                            actual_path = os.path.relpath(os.path.dirname(mod_file), os.path.join(LAB_ROOT, 'footprints'))
                            if expected_path != actual_path:
                                errors.append(f"Footprint {footprint['name']}: should be in {expected_path}/ not {actual_path}/")
                            
                            # Check for duplicates
                            if footprint['name'] in footprint_names:
                                errors.append(f"Footprint {footprint['name']}: duplicate footprint name")
                            footprint_names.add(footprint['name'])
                            
                            # Check fields
                            errors.extend(validate_component_fields(footprint['fields'], 'footprint', footprint['name'], category, subcategory, subsubcategory))
                            
                            # Check 3D models
                            for model in footprint['models']:
                                model_path = os.path.join(LAB_ROOT, '3dmodels', expected_path, model)
                                if not os.path.exists(model_path):
                                    errors.append(f"Footprint {footprint['name']}: references missing 3D model: {model}")
                        
                        except Exception as e:
                            errors.append(f"Footprint {footprint['name']}: error processing {mod_file}: {str(e)}")
            else:
                # Handle regular subcategories
                footprint_dir = os.path.join(LAB_ROOT, 'footprints', get_component_path(category, subcategory))
                if not os.path.exists(footprint_dir):
                    continue
                
                # Find all .kicad_mod files
                mod_files = glob.glob(os.path.join(footprint_dir, "*.kicad_mod"))
                if not mod_files:
                    continue
                
                # Check each footprint
                footprint_names = set()
                for mod_file in mod_files:
                    try:
                        with open(mod_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        footprint = parse_kicad_mod(content)
                        
                        # Use file path to determine category
                        expected_path = get_component_path(category, subcategory)
                        actual_path = os.path.relpath(os.path.dirname(mod_file), os.path.join(LAB_ROOT, 'footprints'))
                        if expected_path != actual_path:
                            errors.append(f"Footprint {footprint['name']}: should be in {expected_path}/ not {actual_path}/")
                        
                        # Check for duplicates
                        if footprint['name'] in footprint_names:
                            errors.append(f"Footprint {footprint['name']}: duplicate footprint name")
                        footprint_names.add(footprint['name'])
                        
                        # Check fields
                        errors.extend(validate_component_fields(footprint['fields'], 'footprint', footprint['name'], category, subcategory))
                        
                        # Check 3D models
                        for model in footprint['models']:
                            model_path = os.path.join(LAB_ROOT, '3dmodels', expected_path, model)
                            if not os.path.exists(model_path):
                                errors.append(f"Footprint {footprint['name']}: references missing 3D model: {model}")
                    
                    except Exception as e:
                        errors.append(f"Footprint {footprint['name']}: error processing {mod_file}: {str(e)}")
    
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

def check_datasheets() -> Tuple[bool, List[str]]:
    """Validate datasheet files and references."""
    errors = []
    
    # Check each category directory
    for category, cat_info in CATEGORIES.items():
        for subcategory, subcat_info in cat_info['subcategories'].items():
            # Handle nested subcategories
            if 'subcategories' in subcat_info:
                for subsubcategory, subsubcat_info in subcat_info['subcategories'].items():
                    datasheet_dir = os.path.join(LAB_ROOT, 'datasheets', get_component_path(category, subcategory, subsubcategory))
                    if not os.path.exists(datasheet_dir):
                        continue
                    
                    # Check each datasheet file
                    for file in os.listdir(datasheet_dir):
                        file_path = os.path.join(datasheet_dir, file)
                        if not os.path.isfile(file_path):
                            continue
                        
                        try:
                            # Check file size
                            size = os.path.getsize(file_path)
                            if size == 0:
                                errors.append(f"Empty datasheet file: {file}")
                            elif size > CONFIG['datasheets']['max_size_mb'] * 1024 * 1024:
                                errors.append(f"Large datasheet file (>{CONFIG['datasheets']['max_size_mb']}MB): {file}")
                            
                            # Check file format
                            ext = os.path.splitext(file)[1].lower().lstrip('.')
                            if ext not in CONFIG['datasheets']['allowed_formats']:
                                errors.append(f"Invalid datasheet format: {file}. Allowed formats: {', '.join(CONFIG['datasheets']['allowed_formats'])}")
                            
                            # Check naming convention
                            if not re.match(r'^[A-Za-z0-9]+_[A-Za-z0-9]+_[A-Za-z0-9]+\.[a-z]+$', file):
                                errors.append(f"Datasheet {file} does not follow naming convention: {CONFIG['datasheets']['naming_convention']}")
                        
                        except Exception as e:
                            errors.append(f"Error checking {file}: {str(e)}")
            else:
                # Handle regular subcategories
                datasheet_dir = os.path.join(LAB_ROOT, 'datasheets', get_component_path(category, subcategory))
                if not os.path.exists(datasheet_dir):
                    continue
                
                # Check each datasheet file
                for file in os.listdir(datasheet_dir):
                    file_path = os.path.join(datasheet_dir, file)
                    if not os.path.isfile(file_path):
                        continue
                    
                    try:
                        # Check file size
                        size = os.path.getsize(file_path)
                        if size == 0:
                            errors.append(f"Empty datasheet file: {file}")
                        elif size > CONFIG['datasheets']['max_size_mb'] * 1024 * 1024:
                            errors.append(f"Large datasheet file (>{CONFIG['datasheets']['max_size_mb']}MB): {file}")
                        
                        # Check file format
                        ext = os.path.splitext(file)[1].lower().lstrip('.')
                        if ext not in CONFIG['datasheets']['allowed_formats']:
                            errors.append(f"Invalid datasheet format: {file}. Allowed formats: {', '.join(CONFIG['datasheets']['allowed_formats'])}")
                        
                        # Check naming convention
                        if not re.match(r'^[A-Za-z0-9]+_[A-Za-z0-9]+_[A-Za-z0-9]+\.[a-z]+$', file):
                            errors.append(f"Datasheet {file} does not follow naming convention: {CONFIG['datasheets']['naming_convention']}")
                    
                    except Exception as e:
                        errors.append(f"Error checking {file}: {str(e)}")
    
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
                    print(f"      - {msg}")
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
    