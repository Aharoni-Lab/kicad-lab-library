#!/usr/bin/env python3
"""
Create empty symbol library files for all subcategories (including nested) as defined in config/library_structure.yml.
Each file will have a minimal valid KiCad symbol library header.
"""
import os
import yaml
from pathlib import Path

LAB_ROOT = Path(__file__).parent.parent
CONFIG_PATH = LAB_ROOT / "config" / "library_structure.yml"
SYMBOLS_ROOT = LAB_ROOT / "symbols"

HEADER = "(kicad_symbol_lib (version 20211014) (generator kicad-library-utils))\n"

def load_structure():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def create_symbol_lib_file(path: Path):
    if not path.exists():
        print(f"Creating {path}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(HEADER)
    else:
        print(f"Exists: {path}")

def process_category(category, category_data, parent_parts=None):
    if parent_parts is None:
        parent_parts = []
    current_parts = parent_parts + [category]
    if "subcategories" in category_data:
        for subcat, subcat_data in category_data["subcategories"].items():
            if "subcategories" in subcat_data:
                process_category(subcat, subcat_data, current_parts)
            else:
                # Leaf subcategory
                dir_path = SYMBOLS_ROOT.joinpath(*current_parts, subcat)
                dir_path.mkdir(parents=True, exist_ok=True)
                file_path = dir_path / f"{subcat}.kicad_sym"
                create_symbol_lib_file(file_path)
    else:
        # No subcategories, treat as leaf
        dir_path = SYMBOLS_ROOT.joinpath(*current_parts)
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / f"{category}.kicad_sym"
        create_symbol_lib_file(file_path)

def main():
    structure = load_structure()
    for category, category_data in structure["categories"].items():
        process_category(category, category_data)
    print("\nAll symbol library files created.")

if __name__ == "__main__":
    main() 