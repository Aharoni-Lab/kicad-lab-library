#!/usr/bin/env python3
"""
Script to add lab libraries to existing KiCad configuration files.
This script will append our lab libraries to the existing sym-lib-table and fp-lib-table
files without overwriting any existing libraries.
"""

import os
import sys
import platform
import yaml
import subprocess
from pathlib import Path

def get_kicad_config_dir(version):
    """Get the KiCad configuration directory based on the operating system and user-supplied version."""
    system = platform.system()
    if system == "Windows":
        base_dir = Path(os.environ["APPDATA"]) / "kicad"
    elif system == "Darwin":  # macOS
        base_dir = Path.home() / "Library" / "Preferences" / "kicad"
    else:  # Linux and others
        base_dir = Path.home() / ".config" / "kicad"
    config_dir = base_dir / str(version)
    print(f"Using KiCad configuration directory: {config_dir}")
    return config_dir

def load_library_structure():
    """Load the library structure from the YAML configuration file."""
    config_path = Path(__file__).parent.parent / "config" / "library_structure.yml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def generate_library_entries(structure):
    """Generate library entries for both symbol and footprint libraries."""
    sym_entries = []
    fp_entries = []
    
    def process_category(category, path_parts=None, category_data=None):
        if path_parts is None:
            path_parts = []
            category_data = structure["categories"][category]
        
        current_path = path_parts + [category]
        
        # Process subcategories
        if "subcategories" in category_data:
            for subcat, subcat_data in category_data["subcategories"].items():
                if "subcategories" in subcat_data:
                    # This is a nested category (e.g., active/sensors/cmos_image)
                    process_category(subcat, current_path, subcat_data)
                else:
                    # This is a leaf category (e.g., passive/resistors)
                    lib_name = f"Lab_{category.capitalize()}_{subcat.capitalize()}"
                    if len(current_path) > 1:
                        # For nested categories, include parent in name
                        lib_name = f"Lab_{current_path[0].capitalize()}_{current_path[1].capitalize()}_{subcat.capitalize()}"
                    
                    # Generate symbol library entry
                    sym_path = "/".join(current_path + [subcat, f"{subcat}.kicad_sym"])
                    sym_entries.append(
                        f'  (lib (name {lib_name})(type KiCad)(uri ${{KICAD_LAB_LIBS}}/symbols/{sym_path})(options "")(descr "{subcat_data["description"]}"))'
                    )
                    
                    # Generate footprint library entry
                    fp_path = "/".join(current_path + [subcat])
                    fp_entries.append(
                        f'  (lib (name {lib_name})(type KiCad)(uri ${{KICAD_LAB_LIBS}}/footprints/{fp_path})(options "")(descr "{subcat_data["description"]}"))'
                    )
    
    # Process each top-level category
    for category in structure["categories"]:
        process_category(category)
    
    return "\n".join(sym_entries), "\n".join(fp_entries)

def backup_file(file_path):
    """Create a backup of the file if it exists."""
    if file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        print(f"Creating backup of {file_path} as {backup_path}")
        file_path.rename(backup_path)

def append_libraries(config_file, entries):
    """Append library entries to the configuration file, only if not already present."""
    if not config_file.exists():
        print(f"Creating new configuration file: {config_file}")
        with open(config_file, "w") as f:
            f.write("(sym_lib_table\n" if "sym" in config_file.name else "(fp_lib_table\n")
            f.write(entries)
            f.write("\n)")
        return

    # If the file exists, read its content and make a backup
    with open(config_file, "r") as f:
        content = f.read()
    backup_file(config_file)

    # Check if our libraries are already added (look for any Lab_ entry)
    already_present = False
    for line in entries.splitlines():
        lib_name = line.split("(name ")[1].split(")")[0] if "(name " in line else None
        if lib_name and lib_name in content:
            already_present = True
            break
    if already_present:
        print(f"Lab libraries already exist in {config_file}")
        return

    # Insert entries before the final closing parenthesis
    idx = content.rfind(")")
    if idx == -1:
        print(f"Malformed library table file: {config_file}. Aborting append.")
        return
    new_content = content[:idx].rstrip() + "\n" + entries + "\n)" + content[idx+1:]
    with open(config_file, "w") as f:
        f.write(new_content)

def main():
    """Main function to set up the library configuration."""
    if len(sys.argv) < 2:
        print("Usage: python setup_libraries.py <kicad_version>")
        print("Example: python setup_libraries.py 9.0")
        sys.exit(1)
    version = sys.argv[1]
    
    # Load library structure and generate entries
    structure = load_library_structure()
    sym_entries, fp_entries = generate_library_entries(structure)
    
    config_dir = get_kicad_config_dir(version)
    print(f"Detected KiCad configuration directory: {config_dir}")
    config_dir.mkdir(parents=True, exist_ok=True)

    # Set up symbol libraries
    sym_lib_table = config_dir / "sym-lib-table"
    append_libraries(sym_lib_table, sym_entries)

    # Set up footprint libraries
    fp_lib_table = config_dir / "fp-lib-table"
    append_libraries(fp_lib_table, fp_entries)

    print("\nLibrary configuration completed successfully!")
    print("Please restart KiCad for the changes to take effect.")

if __name__ == "__main__":
    main() 