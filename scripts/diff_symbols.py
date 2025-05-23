#!/usr/bin/env python3
"""
Generate a list of changed components from git diff output.
This script reads a list of changed files and outputs a list of components to validate.
Format: <file_path>,<component_name> for symbols, just <file_path> for other types.
"""
import sys
import re
from pathlib import Path

def extract_symbol_names(content):
    """Extract all symbol names from a .kicad_sym file."""
    # Look for all (symbol "NAME" ...) patterns
    return [match.group(1) for match in re.finditer(r'\(symbol\s+"([^"]+)"', content)]

def process_changed_files(changed_files_path):
    """Process the list of changed files and generate validation list."""
    components_to_validate = set()
    
    with open(changed_files_path, 'r') as f:
        for line in f:
            file_path = line.strip()
            if not file_path:
                continue
                
            # Handle different file types
            if file_path.endswith('.kicad_sym'):
                # For symbol files, extract all symbol names
                try:
                    if not Path(file_path).exists():
                        print(f"Warning: File {file_path} does not exist, skipping", file=sys.stderr)
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8') as sf:
                        content = sf.read()
                        symbol_names = extract_symbol_names(content)
                        if symbol_names:
                            for symbol_name in symbol_names:
                                components_to_validate.add(f"{file_path},{symbol_name}")
                        else:
                            # If no symbols found, add the file anyway to ensure it gets validated
                            print(f"Warning: No symbols found in {file_path}, adding file for validation", file=sys.stderr)
                            components_to_validate.add(file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}", file=sys.stderr)
                    # Add the file anyway to ensure it gets validated
                    components_to_validate.add(file_path)
            
            elif any(file_path.endswith(ext) for ext in ['.kicad_mod', '.step', '.wrl', '.pdf']):
                # For footprints, 3D models, and datasheets, just add the file path
                if not Path(file_path).exists():
                    print(f"Warning: File {file_path} does not exist, skipping", file=sys.stderr)
                    continue
                components_to_validate.add(file_path)
    
    return sorted(components_to_validate)

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <changed_files.txt>", file=sys.stderr)
        sys.exit(1)
    
    changed_files_path = sys.argv[1]
    if not Path(changed_files_path).exists():
        print(f"Error: Changed files list {changed_files_path} does not exist", file=sys.stderr)
        sys.exit(1)
        
    components = process_changed_files(changed_files_path)
    
    # Output the list of components to validate
    for component in components:
        print(component)

if __name__ == '__main__':
    main() 