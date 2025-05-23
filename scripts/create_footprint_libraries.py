#!/usr/bin/env python3
"""
Create empty footprint library directories for all subcategories (including nested) as defined in config/library_structure.yml.
Each directory will be named <subcat>.pretty and contain a README file.
"""
import os
import yaml
from pathlib import Path

LAB_ROOT = Path(__file__).parent.parent
CONFIG_PATH = LAB_ROOT / "config" / "library_structure.yml"
FOOTPRINTS_ROOT = LAB_ROOT / "footprints"

README_CONTENT = """# Footprint Library
This directory contains KiCad footprint files for this subcategory.
"""

def load_structure():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def create_footprint_lib_dir(path: Path):
    if not path.exists():
        print(f"Creating {path}")
        path.mkdir(parents=True, exist_ok=True)
        readme_path = path / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(README_CONTENT)
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
                dir_path = FOOTPRINTS_ROOT.joinpath(*current_parts, subcat)
                pretty_dir = dir_path  # No .pretty suffix for nested structure
                create_footprint_lib_dir(pretty_dir)
    else:
        # No subcategories, treat as leaf
        dir_path = FOOTPRINTS_ROOT.joinpath(*current_parts)
        create_footprint_lib_dir(dir_path)

def main():
    structure = load_structure()
    for category, category_data in structure["categories"].items():
        process_category(category, category_data)
    print("\nAll footprint library directories created.")

if __name__ == "__main__":
    main() 